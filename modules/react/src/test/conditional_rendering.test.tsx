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

import { StatusBadge } from "../components/StatusBadge";

it("conditional-rendering: chooses what to render at render time", () => {
  render(<StatusBadge status="DONE" archived={false} />);
  expect(screen.getByTestId("badge")).toHaveTextContent("complete");

  render(<StatusBadge status="IN_PROGRESS" archived={false} />);
  expect(screen.getAllByTestId("badge")[1]).toHaveTextContent("in progress");

  render(<StatusBadge status="OPEN" archived={true} />);
  expect(screen.getAllByTestId("badge")[2]).toHaveTextContent("archived");
});
