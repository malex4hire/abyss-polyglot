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

import { BoardSettingsProvider, useBoardSettings } from "../lib/BoardContext";

it("context: reads a shared value, and names the missing provider", () => {
  const { result } = renderHook(() => useBoardSettings(), {
    wrapper: ({ children }) => (
      <BoardSettingsProvider value={{ apiBase: "", pageSize: 3 }}>
        {children}
      </BoardSettingsProvider>
    ),
  });
  expect(result.current.pageSize).toBe(3);

  expect(() => renderHook(() => useBoardSettings())).toThrow(/BoardSettingsProvider/);
});
