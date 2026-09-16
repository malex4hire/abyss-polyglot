import { Component, EventEmitter, Input, Output } from "@angular/core";

@Component({
  selector: "app-counter",
  standalone: true,
  template: `
    <button
      type="button"
      data-testid="counter"
      `
    + `[disabled]="isBusy"`
    + `
      [attr.aria-label]="label"
      `
    + `(click)="bump()"`
    + `
    >
      {{ count }}
    </button>
  `,
})
export class CounterComponent {
  @Input() busy = false;
  @Input() label = "increment";
  @Output() changed = new EventEmitter<number>();
  count = 0;

  /**
   * Context for the property binding in the template fragment above. The demonstration is
   * `[disabled]="isBusy"`; this getter is only what that binding reads, and on its own it
   * says nothing about Angular — a reader sent here instead of to the template learns
   * type coercion, not binding.
   *
   * Returning a real boolean rather than a truthy value is the same discipline one level
   * down from the binding.
   */
  get isBusy(): boolean {
    return this.busy === true;
  }

  /**
   * Respond to a DOM event, bound with (click) in the template.
   *
   * Parentheses bind an event to a statement, and Angular removes the listener when the
   * component is destroyed — which makes a leak impossible here without doing anything
   * to prevent one. $event carries the DOM event when the handler wants it.
   *
   * Unlike interpolation, an event binding may have side effects: it is a statement, not
   * an expression, because responding to an event is exactly when mutation belongs.
   */
  bump(): void {
    this.count += 1;
    this.changed.emit(this.count);
  }
}
