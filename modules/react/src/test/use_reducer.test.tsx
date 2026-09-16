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

import { boardReducer } from "../lib/reducer";

it("use-reducer: every transition is enumerated in one pure function", () => {
  const start = { items: [], selected: null };

  const loaded = boardReducer(start, { type: "loaded", items: [item("WI-1")] });
  expect(loaded.items).toHaveLength(1);

  const selected = boardReducer(loaded, { type: "selected", id: "WI-1" });
  expect(selected.selected).toBe("WI-1");
  expect(boardReducer(selected, { type: "selected", id: "WI-1" })).toBe(selected);
  expect(boardReducer(start, { type: "cleared" })).toBe(start);
});
