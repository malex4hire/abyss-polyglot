import { Component, EventEmitter, Input, Output } from "@angular/core";

@Component({
  selector: "app-filter-box",
  standalone: true,
  template: `
    <input
      data-testid="filter"
      [value]="current"
      (input)="onInput($any($event.target).value)"
    />
  `,
})
export class FilterBoxComponent {
  current = "";
  seen: string[] = [];

  /**
   * A value the parent supplies, observed as it changes.
   *
   * @Input marks part of the component's public surface, set by the parent's template
   * binding rather than passed as an argument. Declaring it as a setter is what lets the
   * component react to a new value. The alternative is ngOnChanges, which fires for
   * every input at once and hands you a SimpleChanges bag to pick through.
   *
   * The framework writes this, which is why an input is declared with a default or a
   * definite assignment rather than initialised in a constructor.
   */
  @Input() set value(next: string) {
    this.current = next ?? "";
    this.seen.push(this.current);
  }

  @Output() changed = new EventEmitter<string>();

  /**
   * Send a value upward to the parent.
   *
   * @Output exposes an EventEmitter the parent binds to with (changed)="...". Data flows
   * down through inputs and events flow up through outputs, so a child never writes to
   * its parent's state. It reports, and the parent decides what that means.
   *
   * The emitter is an Observable underneath, which is why an output composes with the
   * same operators as any other stream. Emitting is a deliberate call, not a side effect
   * of assignment, so the component controls exactly what the parent sees and when.
   */
  onInput(next: string): void {
    this.current = next.trim();
    this.changed.emit(this.current);
  }
}
