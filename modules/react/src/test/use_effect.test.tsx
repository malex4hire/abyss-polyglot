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

import { useDocumentTitle } from "../components/Counter";

it("use-effect: cleanup runs before the next run and at unmount", () => {
  document.title = "original";
  const { rerender, unmount } = renderHook(({ t }) => useDocumentTitle(t), {
    initialProps: { t: "first" },
  });
  expect(document.title).toBe("first");

  rerender({ t: "second" });
  expect(document.title).toBe("second");

  unmount();
  expect(document.title).toBe("original");
});
