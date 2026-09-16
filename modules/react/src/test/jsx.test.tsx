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

import { Heading } from "../components/Heading";

it("jsx: is an expression, not a template language", () => {
  render(<Heading count={1} assignee="avery" />);
  expect(screen.getByTestId("heading")).toHaveTextContent("1 item for avery");
  expect(screen.getByTestId("heading")).toHaveClass("board-heading");
  expect(screen.getByTestId("heading-note")).toBeEmptyDOMElement();

  render(<Heading count={6} assignee="briar" />);
  expect(screen.getAllByTestId("heading")[1]).toHaveTextContent("6 items for briar");
  expect(screen.getAllByTestId("heading-note")[1]).toHaveTextContent("busy week");
});
