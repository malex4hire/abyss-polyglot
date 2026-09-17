import { Injectable, computed, signal } from "@angular/core";

/**
 * Which backend the application is talking to, chosen at runtime.
 *
 * The list is fetched from this frontend's own server, which reads it from
 * stacks/manifest.yaml. Nothing here names a stack: activating a backend in the manifest
 * makes it an option with no change to any file in this module.
 *
 * Switching is a signal write. Every request built from base() picks up the new value on
 * its next call, so there is no rebuild and no reload, which is the point: watching the
 * same UI behave identically against each runtime in turn is what makes contract parity
 * something a viewer sees rather than a test result they are told about.
 */
export interface BackendOption {
  id: string;
  label: string;
}

@Injectable({ providedIn: "root" })
export class BackendStore {
  readonly options = signal<BackendOption[]>([]);
  readonly selected = signal<string>("");

  /** The prefix every contract call is built from. Same-origin, so no CORS anywhere. */
  readonly base = computed(() => (this.selected() ? `/api/${this.selected()}` : ""));

  async load(): Promise<void> {
    const response = await fetch("/__backends");
    const body = (await response.json()) as { backends: BackendOption[] };
    this.options.set(body.backends ?? []);
    if (!this.selected() && body.backends?.length) {
      this.selected.set(body.backends[0].id);
    }
  }

  select(id: string): void {
    this.selected.set(id);
  }
}
