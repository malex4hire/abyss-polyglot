import { expect, it, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";

import { useChanges } from "../lib/changes";

/**
 * The mechanism under test is the cleanup return, so the test is written against what the
 * cleanup does rather than against the data arriving. An effect with no cleanup opens the
 * connection, receives the events and updates the list perfectly well. It fails only on
 * what happens to the previous connection, which is why both closing assertions are here.
 *
 * jsdom has no EventSource, so one is supplied. It records every instance rather than only
 * the last: the defect this pins is a connection left open behind a new one, and a stub
 * that kept a single instance could not see it.
 */
class FakeEventSource {
  static instances: FakeEventSource[] = [];
  closed = false;
  onerror: (() => void) | null = null;
  private readonly listeners = new Map<string, Set<(event: MessageEvent) => void>>();

  constructor(readonly url: string) {
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, fn: (event: MessageEvent) => void): void {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type)!.add(fn);
  }

  removeEventListener(type: string, fn: (event: MessageEvent) => void): void {
    this.listeners.get(type)?.delete(fn);
  }

  close(): void {
    this.closed = true;
  }

  /** Deliver a frame the way the browser would, to whoever is still listening. */
  emit(kind: string, id: string): void {
    const event = { data: JSON.stringify({ kind, id }) } as MessageEvent;
    for (const fn of this.listeners.get("change") ?? []) fn(event);
  }
}

function withFakeEventSource(): typeof FakeEventSource {
  FakeEventSource.instances = [];
  vi.stubGlobal("EventSource", FakeEventSource);
  return FakeEventSource;
}

it("sse-subscription: the effect opens one stream and its cleanup closes it at unmount", () => {
  const sources = withFakeEventSource();
  const onChange = vi.fn();

  const { unmount } = renderHook(() => useChanges("/api/spring-boot", onChange));

  expect(sources.instances).toHaveLength(1);
  expect(sources.instances[0].url).toBe("/api/spring-boot/events");
  expect(sources.instances[0].closed).toBe(false);

  act(() => sources.instances[0].emit("created", "w-1"));
  expect(onChange).toHaveBeenCalledTimes(1);

  // The cleanup return. Without it the connection outlives the component.
  unmount();
  expect(sources.instances[0].closed).toBe(true);

  vi.unstubAllGlobals();
});

it("sse-subscription: switching backends closes the previous stream before opening the next", () => {
  const sources = withFakeEventSource();
  const onChange = vi.fn();

  const { rerender, unmount } = renderHook(({ base }) => useChanges(base, onChange), {
    initialProps: { base: "/api/spring-boot" },
  });
  rerender({ base: "/api/python-modern" });

  expect(sources.instances.map((s) => s.url)).toEqual([
    "/api/spring-boot/events",
    "/api/python-modern/events",
  ]);
  // React runs the cleanup before the next effect, so the first is already shut.
  expect(sources.instances[0].closed).toBe(true);
  expect(sources.instances[1].closed).toBe(false);

  // The consequence the cleanup exists to prevent: one event, one call. A leaked first
  // connection would deliver its own frame as well and the list would update twice.
  act(() => sources.instances[1].emit("archived", "w-2"));
  act(() => sources.instances[0].emit("archived", "w-2"));
  expect(onChange).toHaveBeenCalledTimes(1);

  unmount();
  vi.unstubAllGlobals();
});
