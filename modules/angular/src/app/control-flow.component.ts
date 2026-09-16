import { Component, Input } from "@angular/core";
import { WorkItem } from "../lib/types";

@Component({
  selector: "app-control-flow",
  standalone: true,
  template: `
    @if (visible().length) {
      <ul data-testid="cf-list">
        @for (item of visible(); track item.id) {
          <li>{{ item.title }}</li>
        } @empty {
          <li data-testid="cf-empty">none</li>
        }
      </ul>
    } @else {
      <p data-testid="cf-empty">none</p>
    }
  `,
})
export class ControlFlowComponent {
  @Input() items: WorkItem[] = [];

  /**
   * What the template's @if and @for iterate over.
   *
   * The block syntax replaced *ngIf and *ngFor: it is part of the template language
   * rather than a structural directive, so it needs no import, and @empty gives the
   * empty case a home instead of a second *ngIf beside the loop.
   *
   * track is mandatory now, which is the same decision React makes with key — and for
   * the same reason: without an identity, the framework rebuilds rows instead of moving
   * them, and any state inside a row follows the wrong item.
   */
  visible(): WorkItem[] {
    return this.items.filter((item) => item.archivedAt === null);
  }
}
