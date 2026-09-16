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

import { FetchStates } from "../components/FetchStates";

it("data-fetch-states: loading, failed and empty are named states", () => {
  const { rerender } = render(
    <FetchStates items={[]} loading={true} error={null}>
      <p>loaded</p>
    </FetchStates>,
  );
  expect(screen.getByTestId("state")).toHaveTextContent("loading");

  rerender(
    <FetchStates items={[]} loading={false} error="boom">
      <p>loaded</p>
    </FetchStates>,
  );
  expect(screen.getByTestId("state")).toHaveTextContent("boom");

  rerender(
    <FetchStates items={[]} loading={false} error={null}>
      <p>loaded</p>
    </FetchStates>,
  );
  expect(screen.getByTestId("state")).toHaveTextContent("nothing here yet");

  rerender(
    <FetchStates items={[item("WI-1")]} loading={false} error={null}>
      <p>loaded</p>
    </FetchStates>,
  );
  expect(screen.getByText("loaded")).toBeInTheDocument();
});
