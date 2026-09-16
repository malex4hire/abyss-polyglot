import { describe, expect, it, vi } from "vitest";
import { render, screen, renderHook, act, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkItem } from "../lib/types";

const AT = "2026-01-01T00:00:00Z";

function item(id: string, over: Partial<WorkItem> = {}): WorkItem {
  return {
    id, title: `title-${id}`, status: "OPEN", priority: 5, assignee: "avery",
    createdAt: AT, updatedAt: AT, tags: ["backend"], archivedAt: null, ...over,
  };
}

import { useSelectionCount } from "../components/Counter";

it("use-state: the setter schedules a render rather than mutating", () => {
  const { result } = renderHook(() => useSelectionCount());
  expect(result.current[0]).toBe(0);

  act(() => {
    result.current[1]();
    result.current[1]();
  });

  expect(result.current[0]).toBe(2);
});
