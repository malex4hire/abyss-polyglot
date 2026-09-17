import { Observable, combineLatest, debounceTime, distinctUntilChanged, map } from "rxjs";
import { WorkItem } from "./types";

/**
 * Combine a stream of items with a stream of filter text.
 *
 * Operators are pure functions from Observable to Observable, so a pipeline reads as a
 * description of the data flow rather than as a sequence of callbacks. debounceTime and
 * distinctUntilChanged express "wait for typing to settle, and ignore repeats" in two
 * words each. The same behaviour written by hand is a timer, a saved value and two
 * cleanup paths.
 *
 * combineLatest re-emits whenever either input does, which is the whole reason the
 * filtering does not need to know when items arrive.
 */
export function filtered(
  items$: Observable<WorkItem[]>,
  filter$: Observable<string>,
): Observable<WorkItem[]> {
  return combineLatest([
    items$,
    filter$.pipe(debounceTime(150), distinctUntilChanged()),
  ]).pipe(
    map(([items, filter]) =>
      filter ? items.filter((item) => item.tags.includes(filter)) : items,
    ),
  );
}
