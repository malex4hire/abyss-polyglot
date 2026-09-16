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

import { Panel } from "../components/Panel";

it("component-composition: children is a prop that holds elements", () => {
  render(
    <Panel title="work" actions={<button type="button">act</button>}>
      <p>inner</p>
    </Panel>,
  );

  expect(screen.getByRole("heading")).toHaveTextContent("work");
  expect(screen.getByTestId("panel-body")).toHaveTextContent("inner");
  expect(screen.getByRole("button")).toHaveTextContent("act");
});
