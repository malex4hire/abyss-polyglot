import { Observable } from "rxjs";

/**
 * B4 on the Angular side: an EventSource wrapped as an Observable.
 *
 * The wrapping is the point. An Observable's teardown function runs when the last
 * subscriber unsubscribes, so closing the connection is part of the stream's definition
 * rather than something a component has to remember in ngOnDestroy. Combined with the async
 * pipe (which subscribes and unsubscribes with the view), a browser connection is opened
 * and closed by the template, and nothing in the component touches it.
 *
 * The React counterpart puts the same close in an effect's cleanup return. Both are correct
 * and the difference is where the lifetime lives: attached to the stream here, attached to
 * the component there.
 */
export function changes(base: string): Observable<{ kind: string; id: string }> {
  return new Observable<{ kind: string; id: string }>((subscriber) => {
    const source = new EventSource(`${base}/events`);

    source.addEventListener("change", (event) => {
      try {
        subscriber.next(JSON.parse((event as MessageEvent).data));
      } catch {
        // A malformed frame is not worth tearing the stream down for.
      }
    });

    // EventSource reconnects on its own, so an error is not terminal and must not be
    // reported as one. Completing here would close a stream the browser is about to
    // reopen, and the view would silently stop updating.
    source.onerror = () => undefined;

    // The teardown. It runs when the last subscriber leaves, which under the async pipe is
    // when the view is destroyed. Without it every navigation leaks a live connection.
    return () => source.close();
  });
}
