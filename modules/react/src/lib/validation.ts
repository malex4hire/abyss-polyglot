import { Status } from "./types";

export interface DraftItem {
  title: string;
  priority: string;
  assignee: string;
}

/**
 * Validate a draft, returning one message per bad field.
 *
 * The rules live in a plain function with no React in sight, so they are testable
 * without rendering anything and reusable outside a form. React ships no validation of
 * its own — this is the whole mechanism, where Angular's reactive forms supply
 * validators, a validity state machine, and per-control error objects.
 */
export function validateDraft(draft: DraftItem): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!draft.title.trim()) {
    errors.title = "title is required";
  } else if (draft.title.trim().length < 3) {
    errors.title = "title must be at least three characters";
  }
  const priority = Number(draft.priority);
  if (!draft.priority.trim()) {
    errors.priority = "priority is required";
  } else if (!Number.isInteger(priority) || priority < 1 || priority > 10) {
    errors.priority = "priority must be a whole number from one to ten";
  }
  if (!draft.assignee.trim()) {
    errors.assignee = "assignee is required";
  }
  return errors;
}

export const NEXT_STATUS: Record<Status, Status | null> = {
  OPEN: "IN_PROGRESS",
  IN_PROGRESS: "BLOCKED",
  BLOCKED: "IN_PROGRESS",
  DONE: null,
  CANCELLED: null,
};
