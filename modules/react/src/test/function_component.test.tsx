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

import { EmptyState } from "../components/EmptyState";

it("function-component: is called with props and returns what to render", () => {
  render(<EmptyState />);
  expect(screen.getByTestId("empty-state")).toHaveTextContent("nothing selected");

  render(<EmptyState message="pick one" />);
  expect(screen.getAllByTestId("empty-state")[1]).toHaveTextContent("pick one");
});
