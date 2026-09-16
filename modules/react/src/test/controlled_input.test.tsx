import { describe, expect, it, vi } from "vitest";
import { render, screen, renderHook, act, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkItem } from "../lib/types";

// DraftForm's submit handler calls validateDraft before deciding whether to reset — so
// this file would go red whenever validation broke, even though what it covers is the
// controlled input. Stubbing validateDraft to always pass keeps a failure here about the
// input alone, never about the validation logic another test already covers.
vi.mock("../lib/validation", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../lib/validation")>();
  return { ...actual, validateDraft: () => ({}) };
});

const AT = "2026-01-01T00:00:00Z";

function item(id: string, over: Partial<WorkItem> = {}): WorkItem {
  return {
    id, title: `title-${id}`, status: "OPEN", priority: 5, assignee: "avery",
    createdAt: AT, updatedAt: AT, tags: ["backend"], archivedAt: null, ...over,
  };
}

import { DraftForm } from "../components/DraftForm";

it("controlled-input: the DOM node holds no truth of its own", async () => {
  render(<DraftForm onSubmit={() => undefined} />);
  const title = screen.getByLabelText("title") as HTMLInputElement;

  await userEvent.type(title, "migrate");

  expect(title.value).toBe("migrate");
  await userEvent.clear(title);
  expect(title.value).toBe("");
});

it("controlled-input: submitting resets the field from state, not from user action", async () => {
  // The test above passes identically against an uncontrolled input — typing then
  // clearing leaves value === "" either way, since a native <input> already tracks its
  // own text. What only a controlled input can do: go blank because *state* changed,
  // with no keystroke or user action touching the node at all. DraftForm's own onSubmit
  // already does exactly this (setDraft(EMPTY) after a valid submit) — an uncontrolled
  // title input has no value prop for that reset to reach, and would still show what was
  // typed after the form clears.
  render(<DraftForm onSubmit={() => undefined} />);
  const title = screen.getByLabelText("title") as HTMLInputElement;

  await userEvent.type(title, "migrate");
  await userEvent.type(screen.getByLabelText("priority"), "5");
  await userEvent.type(screen.getByLabelText("assignee"), "avery");
  expect(title.value).toBe("migrate");

  await userEvent.click(screen.getByRole("button", { name: "add" }));

  expect(title.value).toBe("");
});
