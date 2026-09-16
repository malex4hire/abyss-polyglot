import { expect, it, vi } from "vitest";

import { changes } from "../lib/changes";

/**
 * The teardown function the Observable returns is the point, so that is what is asserted:
 * the connection is opened when someone subscribes and closed when the last subscriber
 * leaves. A stream that opens an EventSource and never returns a teardown delivers exactly
 * the same values, which is why nothing here checks only that values arrive.
 *
 * The second test is the property that distinguishes this from the React counterpart. The
 * lifetime is attached to the stream, not to a component, so it holds without any component
 * existing at all — including the cold-Observable property that a second subscriber gets its
 * own connection. Neither is observable through a template.
 *
 * jsdom has no EventSource; the stub records every instance, because the defect worth
 * catching is a connection left open rather than one never made.
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

  emit(kind: string, id: string): void {
    const event = { data: JSON.stringify({ kind, id }) } as MessageEvent;
    for (const fn of this.listeners.get("change") ?? []) fn(event);
  }

  /** A frame the parser will reject, to reach the branch that survives one. */
  emitRaw(data: string): void {
    for (const fn of this.listeners.get("change") ?? []) fn({ data } as MessageEvent);
  }
}

function withFakeEventSource(): typeof FakeEventSource {
  FakeEventSource.instances = [];
  vi.stubGlobal("EventSource", FakeEventSource);
  return FakeEventSource;
}

it("sse-observable: unsubscribing runs the teardown and closes the connection", () => {
  const sources = withFakeEventSource();
  const seen: { kind: string; id: string }[] = [];

  const subscription = changes("/api/spring-boot").subscribe((change) => seen.push(change));

  expect(sources.instances).toHaveLength(1);
  expect(sources.instances[0].url).toBe("/api/spring-boot/events");

  sources.instances[0].emit("created", "w-1");
  // A malformed frame must not tear the stream down; the next good one still arrives.
  sources.instances[0].emitRaw("{not json");
  sources.instances[0].emit("archived", "w-2");
  expect(seen).toEqual([{ kind: "created", id: "w-1" }, { kind: "archived", id: "w-2" }]);

  // The teardown. Without it the connection outlives every subscriber.
  subscription.unsubscribe();
  expect(sources.instances[0].closed).toBe(true);

  vi.unstubAllGlobals();
});

it("sse-observable: the lifetime belongs to the stream, so each subscriber owns its own", () => {
  const sources = withFakeEventSource();
  const stream = changes("/api/python-modern");

  // Cold: subscribing is what opens a connection, so nothing is open before anyone does.
  expect(sources.instances).toHaveLength(0);

  const first = stream.subscribe(() => undefined);
  const second = stream.subscribe(() => undefined);
  expect(sources.instances).toHaveLength(2);

  // One leaving closes only its own, which is the difference from a shared connection.
  first.unsubscribe();
  expect(sources.instances[0].closed).toBe(true);
  expect(sources.instances[1].closed).toBe(false);

  second.unsubscribe();
  expect(sources.instances[1].closed).toBe(true);

  vi.unstubAllGlobals();
});
