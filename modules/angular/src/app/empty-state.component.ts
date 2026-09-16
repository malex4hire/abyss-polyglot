import { Component, Input } from "@angular/core";

/**
 * Shown when nothing is selected.
 *
 * Deliberately trivial. The component-testing spec needs something inert to render, or it
 * would be exercising the harness through a component another test already covers, and a
 * failure would not say which of the two broke.
 */
@Component({
  selector: "app-empty-state",
  standalone: true,
  template: `<p data-testid="empty-state">{{ message }}</p>`,
})
export class EmptyStateComponent {
  @Input() message = "nothing selected";
}
