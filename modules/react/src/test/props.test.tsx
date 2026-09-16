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

import { WorkItemRow } from "../components/WorkItemRow";

it("props: are the component's whole input, flowing one way", async () => {
  const onSelect = vi.fn();
  render(<WorkItemRow item={item("WI-1", { priority: 7 })} onSelect={onSelect} />);

  expect(screen.getByTestId("row-status")).toHaveTextContent("OPEN");
  expect(screen.getByTestId("row-priority")).toHaveTextContent("7");

  await userEvent.click(screen.getByRole("button"));
  expect(onSelect).toHaveBeenCalledWith("WI-1");
});

it("props: the signature names what the component needs", () => {
  // Reading props off the object renders identically — destructuring is notation, and a
  // counter derived from this component by transformation proved nothing on screen can
  // separate them. What the notation does is put the component's interface in its
  // signature, and the signature survives compilation, so it is readable.
  const source = String(WorkItemRow);

  expect(source).toMatch(/^\s*function\s+\w+\s*\(\s*\{/);
  expect(source).toMatch(/\{\s*item\s*,\s*onSelect\s*\}/);
});
