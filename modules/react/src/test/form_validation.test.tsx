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

import { validateDraft } from "../lib/validation";

it("form-validation: rules are a plain function, testable without rendering", () => {
  expect(validateDraft({ title: "ok title", priority: "5", assignee: "avery" })).toEqual({});

  const errors = validateDraft({ title: "no", priority: "99", assignee: "" });
  expect(errors.title).toMatch(/three characters/);
  expect(errors.priority).toMatch(/one to ten/);
  expect(errors.assignee).toMatch(/required/);
});
