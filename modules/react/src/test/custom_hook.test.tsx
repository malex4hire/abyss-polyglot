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

import { useWorkItems } from "../lib/useWorkItems";

it("custom-hook: shares stateful logic by calling other hooks", async () => {
  const load = vi.fn().mockResolvedValue([item("WI-1")]);
  const { result } = renderHook(() => useWorkItems(load));

  expect(result.current.loading).toBe(true);
  await waitFor(() => expect(result.current.loading).toBe(false));

  expect(result.current.items).toHaveLength(1);
  expect(result.current.error).toBeNull();
  expect(load).toHaveBeenCalledTimes(1);
});
