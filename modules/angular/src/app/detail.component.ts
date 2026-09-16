import { AsyncPipe } from "@angular/common";
import { Component, inject } from "@angular/core";
import { ActivatedRoute } from "@angular/router";
import { Observable, map } from "rxjs";

/**
 * Read the parameter that selected this view.
 *
 * paramMap is an Observable, not a snapshot, because Angular reuses a component when only
 * the parameter changes — navigating from /items/1 to /items/2 does not recreate this
 * class. Reading the snapshot once is the bug that follows from assuming it does: the
 * view shows the first id forever.
 */
@Component({
  selector: "app-detail",
  standalone: true,
  // A standalone component declares what its template needs. Omitting AsyncPipe here is
  // an NG0302 at runtime rather than a compile error, which is the cost of the template
  // being a separate language.
  imports: [AsyncPipe],
  template: `<p data-testid="detail">{{ id$ | async }}</p>`,
})
export class DetailComponent {
  private readonly route = inject(ActivatedRoute);
  readonly id$: Observable<string> = this.watchId();

  /**
   * Follow the route parameter as it changes.
   *
   * paramMap is an Observable rather than a snapshot because Angular reuses a component
   * when only the parameter changes — navigating from /items/1 to /items/2 does not
   * construct this class again. Reading the snapshot once is the bug that follows from
   * assuming it does, and the symptom is a view stuck on the first id forever.
   */
  private watchId(): Observable<string> {
    return this.route.paramMap.pipe(map((params) => params.get("id") ?? "none"));
  }
}
