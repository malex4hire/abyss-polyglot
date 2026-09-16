import { HttpClient, HttpParams } from "@angular/common/http";
import { Injectable, inject } from "@angular/core";
import { Observable, map } from "rxjs";
import { loadItems } from "./http-client";
import { API_BASE, WorkItem } from "./types";

/**
 * Shared state and behaviour, provided once and injected where needed.
 *
 * providedIn: "root" registers this with the root injector, so the container creates one
 * instance lazily and hands the same one to every consumer. That is the substantive
 * difference from React's hooks: a service is a singleton the framework owns, where a
 * custom hook runs per component and its state is per caller.
 *
 * inject() replaces constructor parameters and works in field initialisers, which is
 * what lets this class declare its dependencies without writing a constructor at all.
 */
@Injectable({ providedIn: "root" })
export class WorkItemService {
  private readonly http = inject(HttpClient);

  /** Every item, through the shared loader. */
  all(): Observable<WorkItem[]> {
    return loadItems(this.http);
  }

  /**
   * A filtered list, through the injected client.
   *
   * providedIn: "root" registers this service with the root injector, so the container
   * creates one instance lazily and hands the same one to every consumer. inject()
   * resolves the dependency in a field initialiser, which is what lets this class declare
   * what it needs without writing a constructor at all.
   *
   * That singleton is the substantive difference from React's hooks: a service is one
   * instance the framework owns, where a custom hook runs per component and its state is
   * per caller. Sharing state in React needs context or a store on top; here it is the
   * default.
   */
  list(params: { status?: string; tag?: string } = {}): Observable<WorkItem[]> {
    // HttpParams rather than a hand-built query string: it is immutable, so each set
    // returns a new instance, and HttpClient does the encoding. The React side reaches
    // for URLSearchParams and concatenates, which works and leaves the encoding to you.
    let query = new HttpParams();
    if (params.status) query = query.set("status", params.status);
    if (params.tag) query = query.set("tag", params.tag);
    return this.http
      .get<{ items: WorkItem[] }>(`${API_BASE}/work-items`, { params: query })
      .pipe(map((body) => body.items));
  }
}
