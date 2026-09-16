import { Component, Input } from "@angular/core";
import { Status } from "../lib/types";

/**
 * Put a value into the DOM as text.
 *
 * The double braces evaluate an expression in the component's context and write the
 * result as text — always as text, so markup in a value is escaped rather than parsed.
 * That is the default, and it is why interpolation is not an XSS vector the way
 * innerHTML is.
 *
 * The expression is deliberately limited: no assignment, no new, no chaining to
 * arbitrary globals. Angular restricts what a template may say so that a template stays
 * declarative.
 */
@Component({
  selector: "app-badge",
  standalone: true,
  template: `<span data-testid="badge">`
    + `{{ label }} ({{ status }})`
    + `</span>`,
})
export class BadgeComponent {
  @Input() status: Status = "OPEN";

  /**
   * What the double braces evaluate.
   *
   * Interpolation evaluates an expression in the component's context and writes the
   * result as text — always as text, so markup in a value is escaped rather than parsed.
   * That default is why interpolation is not the XSS vector innerHTML is.
   *
   * The expression itself is deliberately restricted: no assignment, no new, no reaching
   * for arbitrary globals. Anything more than a lookup belongs here, in the class, which
   * is why a getter is the idiomatic home for it.
   */
  get label(): string {
    return this.status === "DONE" ? "complete" : this.status.toLowerCase().replace("_", " ");
  }
}
