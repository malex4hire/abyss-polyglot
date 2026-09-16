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

import { WorkItemList } from "../components/WorkItemList";

it("list-keys: identity survives reordering", () => {
  const { rerender } = render(
    <WorkItemList items={[item("WI-1"), item("WI-2")]} onSelect={() => undefined} />,
  );
  const first = screen.getAllByTestId("row")[0];

  rerender(<WorkItemList items={[item("WI-2"), item("WI-1")]} onSelect={() => undefined} />);

  expect(screen.getAllByTestId("row")).toHaveLength(2);
  expect(screen.getAllByTestId("row")[1]).toBe(first);
});
