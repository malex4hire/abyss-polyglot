import { HttpClient, HttpErrorResponse } from "@angular/common/http";
import { Observable, catchError, of } from "rxjs";
import { API_BASE, WorkItem } from "./types";

/**
 * Fetch work items through Angular's HttpClient.
 *
 * HttpClient returns a cold Observable: nothing is sent until something subscribes, and
 * unsubscribing cancels the request in flight. That is the substantive difference from
 * fetch, which returns a Promise that has already started and cannot be cancelled by
 * dropping it.
 *
 * It also throws on a non-2xx, where fetch resolves with ok:false and leaves the check
 * to the caller. Here that error is turned into an empty list rather than escaping.
 */
export function loadItems(http: HttpClient): Observable<WorkItem[]> {
  return http.get<{ items: WorkItem[] }>(`${API_BASE}/work-items`).pipe(
    catchError((error: HttpErrorResponse) => {
      console.warn(`work-items responded ${error.status}`);
      return of({ items: [] as WorkItem[] });
    }),
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return
    (source) => new Observable<WorkItem[]>((subscriber) =>
      source.subscribe({
        next: (body) => subscriber.next(body.items),
        error: (cause) => subscriber.error(cause),
        complete: () => subscriber.complete(),
      }),
    ),
  );
}
