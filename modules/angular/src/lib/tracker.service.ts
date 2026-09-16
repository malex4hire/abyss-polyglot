import { HttpClient, HttpErrorResponse, HttpParams } from "@angular/common/http";
import { Injectable, inject } from "@angular/core";
import { Observable, catchError, map, of, throwError } from "rxjs";
import { BackendStore } from "./backend.store";
import { Status, WorkItem } from "./types";

/**
 * The whole contract, against whichever backend is selected right now.
 *
 * Every URL is built from BackendStore.base() at call time rather than captured once, so a
 * switch takes effect on the next request with nothing re-created.
 */
export interface Rejection {
  from?: string;
  to?: string;
  reason?: string;
}

@Injectable({ providedIn: "root" })
export class TrackerService {
  private readonly http = inject(HttpClient);
  private readonly backend = inject(BackendStore);

  list(filters: { status?: string; tag?: string }): Observable<WorkItem[]> {
    let query = new HttpParams();
    if (filters.status) query = query.set("status", filters.status);
    if (filters.tag) query = query.set("tag", filters.tag);
    return this.http
      .get<{ items: WorkItem[] }>(`${this.backend.base()}/work-items`, { params: query })
      .pipe(map((body) => body.items ?? []));
  }

  create(draft: {
    id: string;
    title: string;
    status: Status;
    priority: number;
    assignee: string;
    tags: string[];
  }): Observable<WorkItem> {
    return this.http
      .post<{ item: WorkItem }>(`${this.backend.base()}/work-items`, draft)
      .pipe(map((body) => body.item));
  }

  /**
   * B2. A refusal is not an error to swallow: 422 carries the typed rejection, and the
   * user is shown why rather than being told something went wrong.
   */
  transition(id: string, status: Status): Observable<{ item?: WorkItem; rejected?: Rejection }> {
    return this.http
      .post<{ item: WorkItem }>(`${this.backend.base()}/work-items/${id}/transition`, { status })
      .pipe(
        map((body) => ({ item: body.item })),
        catchError((error: HttpErrorResponse) => {
          if (error.status === 422) {
            return of({ rejected: (error.error?.rejected ?? {}) as Rejection });
          }
          return throwError(() => error);
        }),
      );
  }

  archive(id: string): Observable<string> {
    return this.http
      .post<{ archived: string }>(`${this.backend.base()}/work-items/${id}/archive`, {})
      .pipe(map((body) => body.archived));
  }

  /** B3. Deliberately slow on every backend, which is what makes the loading state real. */
  workload(): Observable<Record<string, number>> {
    return this.http
      .get<{ byAssignee: Record<string, number> }>(`${this.backend.base()}/workload`)
      .pipe(map((body) => body.byAssignee ?? {}));
  }
}
