import { ChangeDetectionStrategy, Component, Input } from "@angular/core";
import { WorkItem } from "../lib/types";

@Component({
  selector: "app-totals",
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<span data-testid="totals">{{ render() }}</span>`,
})
export class TotalsComponent {
  @Input() items: WorkItem[] = [];

  /**
   * What OnPush lets Angular skip.
   *
   * By default Angular checks every binding in the tree on every event. OnPush narrows
   * that to when an input reference changes, an event fires from this component, or an
   * async pipe emits, so this method runs far less often.
   *
   * The catch is the reference: mutating the items array in place leaves the reference
   * equal and this view stale. OnPush is a promise the component makes about immutable
   * inputs, and the framework holds it to that promise rather than checking.
   */
  render(): string {
    const totals = new Map<string, number>();
    for (const item of this.items) {
      totals.set(item.assignee, (totals.get(item.assignee) ?? 0) + item.priority);
    }
    return [...totals.entries()].map(([who, total]) => `${who}:${total}`).join(" ");
  }
}
