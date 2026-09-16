import { Status } from "../lib/types";

export interface StatusBadgeProps {
  status: Status;
  archived: boolean;
}

/**
 * Show one of several things, chosen at render time.
 *
 * There is no template directive here: a component returns a value, so choosing what to
 * render is ordinary JavaScript — an early return, a ternary, or && for the
 * render-or-nothing case. The trap is that && renders a literal 0 when the left side is
 * the number zero, which is why the guard below is a boolean.
 *
 * Angular's answer is @if in the template, which reads as markup rather than as code.
 */
export function StatusBadge({ status, archived }: StatusBadgeProps) {
  if (archived) {
    return <em data-testid="badge">archived</em>;
  }
  return (
    <span data-testid="badge">
      {status === "DONE" ? "complete" : status.toLowerCase().replace("_", " ")}
    </span>
  );
}
