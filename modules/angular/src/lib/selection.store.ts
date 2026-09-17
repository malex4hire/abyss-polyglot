import { Injectable, computed, signal } from "@angular/core";

/** Which items are selected. Held apart from the board so it can be reasoned about alone. */
@Injectable({ providedIn: "root" })
export class SelectionStore {
  private readonly selected = signal<string[]>([]);

  /**
   * State the framework tracks at the value level.
   *
   * A signal holds a value and records who read it, so a computed recomputes only when
   * something it actually read has changed. There is no dependency array to keep in
   * step, because the dependencies are discovered by reading them.
   *
   * That is the difference from an Observable here: a signal always has a current value
   * and is read synchronously, where a stream is subscribed to and may never emit.
   * Signals are for state; streams are for events.
   *
   * update takes the previous value rather than reading the signal and setting it, which
   * is what keeps concurrent updates from losing one another.
   */
  select(id: string): void {
    this.selected.update((current) =>
      current.includes(id) ? current : [...current, id],
    );
  }

  readonly count = computed(() => this.selected().length);
}
