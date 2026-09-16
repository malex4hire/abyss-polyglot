import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { BackendStore } from "../lib/backend.store";
import { Subscription } from "rxjs";
import { changes } from "../lib/changes";
import { Rejection, TrackerService } from "../lib/tracker.service";
import { Status, WorkItem } from "../lib/types";

type SortKey = "priority" | "title" | "updatedAt";

const STATUSES: Status[] = ["OPEN", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELLED"];

/**
 * The work item tracker. A real application, not a fixture: everything the domain does is
 * reachable by clicking, and every backend serves it identically.
 */
@Component({
  selector: "app-tracker",
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="app" data-testid="tracker">
      <header class="bar">
        <h1 class="brand">
          <svg class="icon" viewBox="0 0 16 16" aria-hidden="true">
            <path fill="currentColor" d="M2 3.2A1.2 1.2 0 0 1 3.2 2h9.6A1.2 1.2 0 0 1 14 3.2v9.6a1.2 1.2 0 0 1-1.2 1.2H3.2A1.2 1.2 0 0 1 2 12.8Zm2.4 2.3h7.2v1.4H4.4Zm0 3h4.8v1.4H4.4Z"/>
          </svg>
          Work items
        </h1>
        <span class="sub">Angular</span>
        <span class="spacer"></span>
        <span class="sub live-count" data-testid="live-count">{{ liveEvents() }} live</span>
        <button type="button" class="ghost" data-testid="theme-toggle" (click)="toggleTheme()"
                [attr.aria-label]="theme() === 'dark' ? 'switch to light' : 'switch to dark'">
          @if (theme() === "dark") {
            <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1.5a1 1 0 0 1 1 1V4a1 1 0 1 1-2 0V2.5a1 1 0 0 1 1-1Zm0 9a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5Zm0 1.5a1 1 0 0 1 1 1v1.5a1 1 0 1 1-2 0V13a1 1 0 0 1 1-1Zm6-4a1 1 0 0 1-1 1h-1.5a1 1 0 1 1 0-2H13a1 1 0 0 1 1 1ZM4.5 8a1 1 0 0 1-1 1H2a1 1 0 1 1 0-2h1.5a1 1 0 0 1 1 1Z"/></svg>
          } @else {
            <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M13.2 9.6A5.6 5.6 0 0 1 6.4 2.8 5.6 5.6 0 1 0 13.2 9.6Z"/></svg>
          }
        </button>
        <button type="button" class="ghost" data-testid="runtime-toggle" (click)="toggleRuntime()">
          <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1.6 14 5v6l-6 3.4L2 11V5Zm0 1.8L3.6 5.9v4.2L8 12.6l4.4-2.5V5.9Z"/></svg>
          runtime
        </button>
        <label class="field">
          <span class="label">backend</span>
          <select data-testid="backend-select" [ngModel]="backend.selected()"
                  (ngModelChange)="switchBackend($event)">
            @for (option of backend.options(); track option.id) {
              <option [value]="option.id">{{ option.label }}</option>
            }
          </select>
        </label>
      </header>

      <aside class="rail">
        <div>
          <span class="label">filter</span>
          <label class="field">
            <select data-testid="filter-status" [ngModel]="statusFilter()" (ngModelChange)="setStatus($event)">
              <option value="">any status</option>
              @for (status of statuses; track status) {
                <option [value]="status">{{ status }}</option>
              }
            </select>
          </label>
          <label class="field">
            <input data-testid="filter-tag" [ngModel]="tagFilter()" (ngModelChange)="setTag($event)"
                   placeholder="part of a tag" />
          </label>
        </div>

        <div>
          <span class="label">sort</span>
          <label class="field">
            <select data-testid="sort" [ngModel]="sortKey()" (ngModelChange)="setSort($event)">
              <option value="priority">priority</option>
              <option value="title">title</option>
              <option value="updatedAt">recently updated</option>
            </select>
          </label>
        </div>

        <div>
          <span class="label">aggregate</span>
          <button type="button" data-testid="run-workload" (click)="runWorkload()"
                  [disabled]="workloadLoading()">
            <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M2 13h12v1.4H2Zm1.6-4h2v3h-2Zm3.4-4h2v7H7Zm3.4-3h2v10h-2Z"/></svg>
            workload
          </button>
        </div>
      </aside>

      <main class="main">
        <h2 class="page-title">{{ backend.selected() }}</h2>
        <p class="sub">One contract, {{ backend.options().length }} runtimes. This screen is the
          same in both frameworks.</p>

        @if (runtimeShown() && runtime(); as info) {
          <section class="card runtime" data-testid="runtime-panel">
            <h2>{{ info.backend }}</h2>
            <p class="sub">
              <!-- The exact build, because "25" is a claim and "25.0.3+9-LTS" is an answer.
                   The short form remains what the version floor is compared against; this
                   panel is where someone asks which JDK actually produced the page. -->
              <strong data-testid="runtime-version">{{
                info.identity?.runtime_version_exact || info.identity?.runtime_version
              }}</strong>
              @if (info.identity?.runtime_vendor) {
                · <span data-testid="runtime-vendor">{{ info.identity?.runtime_vendor }}</span>
              }
              · <span data-testid="runtime-server">{{ info.identity?.http_server_class }}</span>
              · <span data-testid="runtime-artifacts">{{ (info.identity?.artifacts || []).length }} artifacts</span>
            </p>
            @if ((info.identity?.artifacts || []).length) {
              <!-- The count above answers "how many"; this answers "which, and at what
                   version" — the question the count can't. Collapsed by default so the
                   panel stays scannable, but the exact resolved versions are one click
                   away rather than only visible in the raw JSON. -->
              <details data-testid="runtime-artifacts-detail">
                <summary>show artifacts</summary>
                <ul class="artifact-list" data-testid="runtime-artifacts-list">
                  @for (artifact of info.identity?.artifacts; track artifact) {
                    <li>{{ artifact }}</li>
                  }
                </ul>
              </details>
            }
            @if (info.pair?.identity) {
              <!-- The framework version, not the JVM underneath it: spring-boot and
                   spring-traditional share a base image, so runtime_version_exact is
                   identical on both sides and says nothing about which framework is
                   which. frameworkVersion is resolved server-side from the artifact the
                   declared framework actually ships as; falls back to the runtime
                   version only for java-modern and python-modern, which have no
                   framework by design and where the runtime genuinely is the whole
                   answer. -->
              <p class="sub pair-versions" data-testid="runtime-pair-versions">
                <strong>{{ info.backend }}</strong> version:
                <strong>{{
                  info.frameworkVersion || info.identity?.runtime_version_exact || info.identity?.runtime_version
                }}</strong>
                · <strong>{{ info.pair.backend }}</strong> version:
                <strong>{{
                  info.pair.frameworkVersion
                    || info.pair.identity?.runtime_version_exact
                    || info.pair.identity?.runtime_version
                }}</strong>
              </p>
              <p class="sub pair-counts" data-testid="runtime-pair">
                against its pair — <strong>{{ info.backend }}: {{ (info.identity?.artifacts || []).length }}</strong>
                artifacts, <strong>{{ info.pair.backend }}: {{ (info.pair.identity.artifacts || []).length }}</strong>.
                Same contract, same behaviour, {{ artifactDelta(info) }} {{ artifactComparison(info) }} jars to get there.
              </p>
            }
            @if (capabilities().length) {
              <table data-testid="runtime-capabilities">
                <thead><tr><th>capability</th><th>bean</th><th>supplied by</th><th>declared at</th></tr></thead>
                <tbody>
                  @for (row of capabilities(); track row[0]) {
                    <tr>
                      <td>{{ row[0] }}</td><td>{{ row[1].bean }}</td>
                      <td data-testid="capability-source">{{ suppliedBy(row[1]) }}</td>
                      <td class="where">{{ row[1].declared_at }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            }
          </section>
        }

        @if (workloadLoading()) {
          <section class="card" data-testid="workload-loading">
            <h2>workload</h2>
            <p class="sub">Fanning out one slow computation per assignee.</p>
            <div class="progress"><span [style.width.%]="workloadProgress()"></span></div>
          </section>
        } @else if (workload()) {
          <section class="card" data-testid="workload">
            <h2>workload</h2>
            <div class="bars">
              @for (row of workloadRows(); track row[0]) {
                <div class="bar-row">
                  <span>{{ row[0] }}</span>
                  <span class="meter"><span [style.width.%]="barWidth(row[1])"></span></span>
                  <span class="num">{{ row[1] }}</span>
                </div>
              }
            </div>
          </section>
        }

        @if (rejection(); as refused) {
          <p class="refused" data-testid="rejection" role="status">
            <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1.6 14.6 13H1.4Zm-.8 4v4h1.6v-4Zm0 5v1.6h1.6v-1.6Z"/></svg>
            {{ refused.reason || (refused.from + " cannot move to " + refused.to) }}
          </p>
        }

        <p class="sub" data-testid="transition-note">the status control runs a state machine:
          an illegal move is refused by the backend, not hidden by the form.</p>

        @if (loading()) {
          <section class="card table-card" data-testid="loading">
            @for (row of [1, 2, 3, 4, 5]; track row) {
              <div class="skeleton-row">
                <span class="skeleton"></span><span class="skeleton"></span>
                <span class="skeleton"></span><span class="skeleton"></span>
              </div>
            }
          </section>
        } @else if (failed()) {
          <section class="card state" data-kind="error" data-testid="error">
            <svg class="icon-lg" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1.6 14.6 13H1.4Zm-.8 4v4h1.6v-4Zm0 5v1.6h1.6v-1.6Z"/></svg>
            <strong>{{ backend.selected() }} did not answer</strong>
            <span class="sub">The request failed. The other runtimes are still selectable.</span>
            <button type="button" (click)="refresh()">try again</button>
          </section>
        } @else if (sorted().length === 0) {
          <section class="card state" data-testid="empty">
            <svg class="icon-lg" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M2.5 3h11v1.6h-11Zm0 4h11v1.6h-11Zm0 4h7v1.6h-7Z"/></svg>
            <strong>Nothing matches those filters</strong>
            <span class="sub">{{ items().length }} items exist on this backend.</span>
            <button type="button" (click)="clearFilters()">clear filters</button>
          </section>
        } @else {
          <section class="card table-card">
            <table data-testid="list">
              <thead>
                <tr>
                  <th>id</th><th>title</th><th>status</th><th class="num">pri</th>
                  <th>assignee</th><th>tags</th><th></th>
                </tr>
              </thead>
              <tbody>
                @for (item of sorted(); track item.id) {
                  <tr data-testid="row" [class.arrived]="isArrival(item.id)" [class.leaving]="isLeaving(item.id)">
                    <td class="id mono">{{ item.id }}</td>
                    <td class="title">{{ item.title }}</td>
                    <td>
                      <span class="pill" [attr.data-status]="item.status">
                        <select data-testid="row-status" [ngModel]="item.status"
                                (ngModelChange)="move(item, $event)" aria-label="change status">
                          @for (status of statuses; track status) {
                            <option [value]="status">{{ status }}</option>
                          }
                        </select>
                      </span>
                    </td>
                    <td class="num">{{ item.priority }}</td>
                    <td>{{ item.assignee }}</td>
                    <td><span class="tags">@for (tag of item.tags; track tag) {
                      <span class="tag">{{ tag }}</span>
                    }</span></td>
                    <td>
                      <button type="button" class="ghost row-actions" data-testid="archive"
                              (click)="archive(item)" aria-label="archive">
                        <svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M2 3h12v2.4H2Zm1 3.4h10V13H3Zm2.4 2v1.4h5.2V8.4Z"/></svg>
                      </button>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </section>
        }

        <section class="card">
          <h2>new item</h2>
          <form (submit)="submit($event)" style="display:flex;gap:var(--space-2);align-items:end;flex-wrap:wrap">
            <label class="field" [class.invalid]="errorFor('title')" style="flex:2 1 14rem">
              <span class="label">title</span>
              <input data-testid="new-title" name="title" [ngModel]="title()"
                     (ngModelChange)="title.set($event)" placeholder="what needs doing" />
              @if (errorFor("title"); as message) {
                <span class="error" data-testid="error-title">{{ message }}</span>
              }
            </label>
            <label class="field" [class.invalid]="errorFor('priority')" style="flex:0 1 7rem">
              <span class="label">priority</span>
              <input data-testid="new-priority" name="priority" [ngModel]="priority()"
                     (ngModelChange)="priority.set($event)" placeholder="1–10" />
              @if (errorFor("priority"); as message) {
                <span class="error" data-testid="error-priority">{{ message }}</span>
              }
            </label>
            <label class="field" [class.invalid]="errorFor('assignee')" style="flex:1 1 10rem">
              <span class="label">assignee</span>
              <input data-testid="new-assignee" name="assignee" [ngModel]="assignee()"
                     (ngModelChange)="assignee.set($event)" placeholder="who" />
              @if (errorFor("assignee"); as message) {
                <span class="error" data-testid="error-assignee">{{ message }}</span>
              }
            </label>
            <button class="primary" type="submit" data-testid="create">create</button>
          </form>
          @if (errors().length) {
            <ul class="error" data-testid="create-errors">
              @for (error of errors(); track error) { <li>{{ error }}</li> }
            </ul>
          }
        </section>
      </main>

      <div class="toasts" data-testid="toasts">
        @for (toast of toasts(); track toast.id) {
          <div class="toast"><span class="dot"></span>{{ toast.text }}</div>
        }
      </div>
    </div>
  `,
})
export class TrackerComponent implements OnInit {
  readonly backend = inject(BackendStore);
  private readonly tracker = inject(TrackerService);

  readonly statuses = STATUSES;

  readonly items = signal<WorkItem[]>([]);
  readonly loading = signal(true);
  readonly statusFilter = signal("");
  readonly tagFilter = signal("");
  readonly sortKey = signal<SortKey>("priority");
  readonly rejection = signal<Rejection | null>(null);
  readonly workload = signal<Record<string, number> | null>(null);
  readonly workloadLoading = signal(false);

  private liveUpdates: Subscription | null = null;
  readonly liveEvents = signal(0);

  /**
   * Which rows arrived from the stream rather than from this browser, and which are on
   * their way out. Signals hold them and the template binds classes off them, so the
   * animation is a consequence of state rather than a DOM instruction — which is the
   * Angular half of the pair. React derives the same two sets from hooks.
   */
  readonly arrivals = signal<Set<string>>(new Set());
  /** Transient notices for changes that arrived from another browser over SSE. */
  readonly toasts = signal<{ id: number; text: string }[]>([]);
  readonly theme = signal<"dark" | "light">("dark");
  readonly leaving = signal<Set<string>>(new Set());
  readonly failed = signal(false);
  readonly workloadProgress = signal(0);
  private progressTimer: ReturnType<typeof setInterval> | null = null;

  readonly runtimeShown = signal(false);
  readonly runtime = signal<any>(null);

  readonly title = signal("");
  readonly priority = signal("");
  readonly assignee = signal("");
  readonly errors = signal<string[]>([]);

  /** Sorting is client-side and is a signal read, so it re-derives with no refetch. */
  readonly sorted = computed(() => {
    const key = this.sortKey();
    return [...this.items()].sort((a, b) => {
      if (key === "priority") return b.priority - a.priority || a.title.localeCompare(b.title);
      if (key === "title") return a.title.localeCompare(b.title);
      return (b.updatedAt ?? "").localeCompare(a.updatedAt ?? "");
    });
  });

  readonly workloadRows = computed(() => Object.entries(this.workload() ?? {}));

  async ngOnInit(): Promise<void> {
    await this.backend.load();

    // The side-by-side page points both frames at the same backend through this
    // parameter. Reading it here is what makes one selector drive two frameworks.
    const params = new URLSearchParams(location.search);
    const backend = params.get("backend");
    if (backend && this.backend.options().some((option) => option.id === backend)) {
      this.backend.select(backend);
    }
    this.refresh();
    this.listen();
  }

  readonly capabilities = computed(() => {
    const info = this.runtime();
    const caps = info?.autoconfig?.capabilities ?? info?.beans?.capabilities ?? {};
    return Object.entries<any>(caps);
  });

  /**
   * What actually supplied the capability, not the category it belongs to.
   *
   * "auto-configuration" is the answer to a different question. The Boot side should read
   * as a list of specific things Boot brought — DataSourceConfiguration$Hikari,
   * DispatcherServletAutoConfiguration — because that is what the traditional module wrote
   * by hand and what the contrast is about.
   */
  suppliedBy(row: any): string {
    const declared = String(row?.declared_at ?? "");
    if (!declared) return String(row?.source ?? "");
    const cleaned = declared.replace(/^class path resource \[/, "").replace(/\.class\]$/, "");
    return cleaned.split(/[\/.]/).filter(Boolean).pop() ?? cleaned;
  }

  artifactDelta(info: any): number {
    const mine = (info?.identity?.artifacts || []).length;
    const theirs = (info?.pair?.identity?.artifacts || []).length;
    return Math.abs(theirs - mine);
  }

  /**
   * "more" or "fewer", from the direction of the difference.
   *
   * The count was absolute, so the sentence said "more" whichever side you were looking
   * at — and read on the smaller runtime it claimed the opposite of the truth. The number
   * describes the selected backend against its pair, so the word has to follow the sign.
   */
  artifactComparison(info: any): string {
    const mine = (info?.identity?.artifacts || []).length;
    const theirs = (info?.pair?.identity?.artifacts || []).length;
    return mine > theirs ? "more" : "fewer";
  }

  async toggleRuntime(): Promise<void> {
    this.runtimeShown.update((shown) => !shown);
    if (this.runtimeShown()) await this.loadRuntime();
  }

  private async loadRuntime(): Promise<void> {
    // Every runtime serves one identical contract, and the interface where that is
    // happening said only their names. This reports what the selected one actually is.
    const response = await fetch(`/__runtime?backend=${encodeURIComponent(this.backend.selected())}`);
    this.runtime.set(response.ok ? await response.json() : null);
  }

  /** Flag rows as new for one animation, then forget them. */
  toggleTheme(): void {
    // One attribute on the document; both palettes are declared, so nothing here knows a
    // colour. Dark is the default because the application is a tool, not a document.
    const next = this.theme() === "dark" ? "light" : "dark";
    this.theme.set(next);
    document.documentElement.setAttribute("data-theme", next);
  }

  private notify(text: string): void {
    const id = this.liveEvents();
    this.toasts.update((current) => [...current, { id, text }].slice(-3));
    setTimeout(() => this.toasts.update((current) => current.filter((t) => t.id !== id)), 4000);
  }

  private markArrivals(ids: string[]): void {
    this.arrivals.set(new Set([...this.arrivals(), ...ids]));
    setTimeout(() => {
      const rest = new Set(this.arrivals());
      ids.forEach((id) => rest.delete(id));
      this.arrivals.set(rest);
    }, 1200);
  }

  isArrival(id: string): boolean {
    return this.arrivals().has(id);
  }

  isLeaving(id: string): boolean {
    return this.leaving().has(id);
  }

  clearFilters(): void {
    this.statusFilter.set("");
    this.tagFilter.set("");
    this.refresh();
  }

  barWidth(value: number): number {
    const highest = Math.max(1, ...this.workloadRows().map(([, total]) => total));
    return Math.round((value / highest) * 100);
  }

  /** The field's own message, so the error renders against the input that caused it. */
  errorFor(field: "title" | "priority" | "assignee"): string | null {
    const found = this.errors().find((message) => message.startsWith(field));
    return found ?? null;
  }

  refresh(): void {
    this.loading.set(true);
    this.tracker.list({ status: this.statusFilter(), tag: this.tagFilter() }).subscribe({
      next: (items) => {
        const known = new Set(this.items().map((item) => item.id));
        const fresh = items.filter((item) => !known.has(item.id)).map((item) => item.id);
        this.items.set(items);
        this.failed.set(false);
        this.loading.set(false);
        if (fresh.length && known.size) this.markArrivals(fresh);
      },
      error: () => {
        // An empty list and a backend that did not answer are different states and must
        // not render the same. The empty state offers to clear filters; this one offers
        // to retry, and says which backend failed.
        this.items.set([]);
        this.failed.set(true);
        this.loading.set(false);
      },
    });
  }

  /** B4. Re-subscribe on every backend change; the old stream's teardown closes it. */
  private listen(): void {
    this.liveUpdates?.unsubscribe();
    this.liveUpdates = changes(this.backend.base()).subscribe((event) => {
      this.liveEvents.update((n) => n + 1);
      // Unmissable: the row animates and this says what happened, because a change made in
      // another browser is the one thing a viewer will otherwise miss.
      this.notify(`${event?.kind ?? "change"} ${event?.id ?? ""}`.trim());
      // The event is a notification, not a payload: re-read rather than patch, so the
      // list is whatever the backend says it is.
      this.refresh();
    });
  }

  switchBackend(id: string): void {
    // No rebuild and no reload: the store is a signal, every URL is built from it at call
    // time, and the next request goes somewhere else.
    this.backend.select(id);
    this.listen();
    if (this.runtimeShown()) void this.loadRuntime();
    this.workload.set(null);
    this.rejection.set(null);
    this.refresh();
  }

  setStatus(value: string): void {
    this.statusFilter.set(value);
    this.refresh();
  }

  setTag(value: string): void {
    this.tagFilter.set(value);
    this.refresh();
  }

  setSort(value: SortKey): void {
    this.sortKey.set(value);
  }

  move(item: WorkItem, next: Status): void {
    if (next === item.status) return;
    this.rejection.set(null);
    this.tracker.transition(item.id, next).subscribe((result) => {
      if (result.rejected) {
        // The state machine refused. Show why, and leave the row as it was.
        this.rejection.set(result.rejected);
      }
      this.refresh();
    });
  }

  archive(item: WorkItem): void {
    // Animate the row out first, then refresh. Removing it instantly is correct and reads
    // as the list flickering; the exit is what tells the viewer which row went.
    this.leaving.set(new Set([...this.leaving(), item.id]));
    setTimeout(() => {
      this.tracker.archive(item.id).subscribe(() => {
        const rest = new Set(this.leaving());
        rest.delete(item.id);
        this.leaving.set(rest);
        this.refresh();
      });
    }, 240);
  }

  runWorkload(): void {
    this.workloadLoading.set(true);
    // Real progress rather than the word "loading": the aggregate is a deliberately slow
    // fan-out of one computation per assignee, so the bar advances against how long that
    // is expected to take and completes when the answer lands.
    this.workloadProgress.set(0);
    const expectedMs = Math.max(400, this.items().length * 120);
    const started = Date.now();
    this.progressTimer = setInterval(() => {
      const done = Math.min(95, ((Date.now() - started) / expectedMs) * 100);
      this.workloadProgress.set(done);
    }, 60);
    this.tracker.workload().subscribe({
      next: (rows) => {
        this.workloadProgress.set(100);
        this.workload.set(rows);
        this.stopProgress();
      },
      error: () => this.stopProgress(),
    });
  }

  private stopProgress(): void {
    if (this.progressTimer) clearInterval(this.progressTimer);
    this.progressTimer = null;
    this.workloadLoading.set(false);
  }

  submit(event: Event): void {
    event.preventDefault();
    const found = this.validate();
    this.errors.set(found);
    if (found.length) return;

    this.tracker
      .create({
        id: `WI-${Date.now().toString().slice(-6)}`,
        title: this.title().trim(),
        status: "OPEN",
        priority: Number(this.priority()),
        assignee: this.assignee().trim(),
        tags: [],
      })
      .subscribe({
        next: () => {
          this.title.set("");
          this.priority.set("");
          this.assignee.set("");
          this.refresh();
        },
        error: () => this.errors.set(["the backend refused this item"]),
      });
  }

  private validate(): string[] {
    const found: string[] = [];
    if (this.title().trim().length < 3) found.push("title needs at least three characters");
    const priority = Number(this.priority());
    if (!this.priority().trim() || Number.isNaN(priority) || priority < 1 || priority > 10) {
      found.push("priority must be a number from one to ten");
    }
    if (!this.assignee().trim()) found.push("assignee is required");
    return found;
  }
}
