import { AsyncPipe } from "@angular/common";
import { Component, Input } from "@angular/core";
import { Observable, map } from "rxjs";
import { WorkItem } from "../lib/types";

@Component({
  selector: "app-titles",
  standalone: true,
  imports: [AsyncPipe],
  template: `<p data-testid="titles">`
    + `{{ titles$ | async }}`
    + `</p>`,
})
export class TitlesComponent {
  @Input({ required: true }) items$!: Observable<WorkItem[]>;

  /**
   * Hand a stream to the template and let it manage the subscription.
   *
   * The async pipe subscribes when the view renders and unsubscribes when it is
   * destroyed, which removes the most common Angular leak: a manual subscribe with no
   * matching unsubscribe. It also marks the component for check on each emission, so it
   * works with OnPush where assigning to a field would not.
   *
   * The cost is that each async in a template is its own subscription: piping the same
   * source twice runs it twice, which is why the shape below derives once and binds once.
   */
  get titles$(): Observable<string> {
    return this.items$.pipe(map((items) => items.map((item) => item.title).join(", ")));
  }
}
