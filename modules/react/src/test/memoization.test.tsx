import { describe, expect, it, vi } from "vitest";
import { render, screen, renderHook, act, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkItem } from "../lib/types";
import * as summaryModule from "../lib/summary";

const AT = "2026-01-01T00:00:00Z";

function item(id: string, over: Partial<WorkItem> = {}): WorkItem {
  return {
    id, title: `title-${id}`, status: "OPEN", priority: 5, assignee: "avery",
    createdAt: AT, updatedAt: AT, tags: ["backend"], archivedAt: null, ...over,
  };
}

import { Totals } from "../components/Board";

it("memoization: caches against a dependency array", () => {
  const items = [item("WI-1", { priority: 5 }), item("WI-2", { assignee: "briar", priority: 3 })];
  const { rerender } = render(<Totals items={items} />);

  expect(screen.getByTestId("totals")).toHaveTextContent("avery:5 briar:3");

  rerender(<Totals items={[...items, item("WI-3", { priority: 2 })]} />);
  expect(screen.getByTestId("totals")).toHaveTextContent("avery:7 briar:3");
});

it("memoization: recomputes only when the dependency array changes", () => {
  // The test above passes against recomputing on every render. The totals are correct
  // either way, which is why it survived as vacuous. This counts the actual work: a
  // rerender with the same items reference must not call summarise again, and a rerender
  // with a new reference must.
  const spy = vi.spyOn(summaryModule, "summarise");
  const items = [item("WI-1", { priority: 5 }), item("WI-2", { assignee: "briar", priority: 3 })];
  const { rerender } = render(<Totals items={items} />);
  expect(spy).toHaveBeenCalledTimes(1);

  rerender(<Totals items={items} />);
  expect(spy).toHaveBeenCalledTimes(1);

  rerender(<Totals items={[...items, item("WI-3", { priority: 2 })]} />);
  expect(spy).toHaveBeenCalledTimes(2);

  spy.mockRestore();
});
