import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  inject,
} from "@angular/core";
import { AsyncPipe } from "@angular/common";
import { BehaviorSubject, Observable, Subscription } from "rxjs";
import { WorkItemService } from "../lib/work-item.service";
import { filtered } from "../lib/operators";
import { WorkItem } from "../lib/types";
import { WorkItemRowComponent } from "./work-item-row.component";
import { FilterBoxComponent } from "./filter-box.component";
import { BadgeComponent } from "./badge.component";
import { CounterComponent } from "./counter.component";
import { TitlesComponent } from "./async-pipe.component";
import { ControlFlowComponent } from "./control-flow.component";
import { TotalsComponent } from "./onpush.component";
import { DraftFormComponent } from "./draft-form.component";
import { TickerComponent } from "./ticker.component";
import { EmptyStateComponent } from "./empty-state.component";
import { SelectionStore } from "../lib/selection.store";

@Component({
  selector: "app-board",
  standalone: true,
  imports: [
    AsyncPipe,
    WorkItemRowComponent,
    FilterBoxComponent,
    BadgeComponent,
    CounterComponent,
    TitlesComponent,
    ControlFlowComponent,
    TotalsComponent,
    DraftFormComponent,
    TickerComponent,
    EmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-filter-box [value]="filter" (changed)="setFilter($event)" />
    <p data-testid="count">{{ selectedCount() }} selected</p>

    @if (visible$ | async; as items) {
      @if (items.length) {
        <ul data-testid="list">
          @for (item of items; track item.id) {
            <app-work-item-row [item]="item" (select)="select($event)" />
          }
        </ul>
      } @else {
        <p data-testid="empty">nothing here yet</p>
      }
    } @else {
      <p data-testid="loading">loading…</p>
    }

    <app-badge [status]="'OPEN'" />
    <app-ticker />
    <app-empty-state />
    <app-draft-form (submitted)="onDrafted()" />
    <app-counter [busy]="false" label="select" (changed)="onCounted($event)" />
    <app-titles [items$]="visible$" />
    <app-control-flow [items]="rendered" />
    <app-totals [items]="rendered" />
  `,
})
export class BoardComponent implements OnInit, OnDestroy {
  private readonly service = inject(WorkItemService);
  private readonly filter$ = new BehaviorSubject<string>("");
  private subscription?: Subscription;

  filter = "";
  visible$!: Observable<WorkItem[]>;

  // (signals lives in SelectionStore)
  /**
   * State the framework can track at the value level.
   *
   * A signal holds a value and knows who read it, so a computed signal recomputes only
   * when something it actually read has changed — no dependency array to keep in step,
   * because the dependencies are discovered by reading them.
   *
   * That is the difference from RxJS here: a signal always has a current value and is
   * read synchronously, where an Observable is a stream you subscribe to and may never
   * emit. Signals are for state; streams are for events.
   */
  private readonly selection = inject(SelectionStore);
  readonly selectedCount = this.selection.count;

  select(id: string): void {
    this.selection.select(id);
  }
  

  // (lifecycle-hooks lives in TickerComponent)
  /**
   * Set up when the component starts, tear down when it ends.
   *
   * ngOnInit runs after the first inputs are set, which is why work depending on an
   * @Input belongs here and not in the constructor — at construction the inputs are
   * still undefined. ngOnDestroy is the other half, and the subscription below is
   * exactly the kind of thing that leaks without it.
   *
   * The hooks are interface methods the framework calls, so implementing OnInit is a
   * declaration of intent the compiler can check.
   */
  ngOnInit(): void {
    this.visible$ = filtered(this.service.all(), this.filter$.asObservable());
    this.subscription = this.visible$.subscribe((items) => (this.rendered = items));
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    this.filter$.complete();
  }
  

  rendered: WorkItem[] = [];

  onDrafted(): void {
    this.counted += 1;
  }

  onCounted(next: number): void {
    this.counted = next;
  }

  counted = 0;

  setFilter(next: string): void {
    this.filter = next;
    this.filter$.next(next);
  }
}
