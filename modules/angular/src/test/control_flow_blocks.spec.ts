import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { ControlFlowComponent } from "../app/control-flow.component";
import { WorkItem } from "../lib/types";

const AT = "2026-01-01T00:00:00Z";
const make = (id: string, archived: string | null): WorkItem => ({
  id, title: id, status: "OPEN", priority: 1, assignee: "a",
  createdAt: AT, updatedAt: AT, tags: [], archivedAt: archived,
});

it("control-flow-blocks: @if and @for are template syntax", () => {
  const fixture = TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
    imports: [ControlFlowComponent],
  }).createComponent(ControlFlowComponent);
  fixture.componentInstance.items = [make("WI-1", null), make("WI-2", AT)];
  fixture.detectChanges();

  // Asserted on what the template rendered, not on the method it called. The fixture was
  // already being built and detected; an earlier version reached past the DOM to the
  // class, so it stayed green even with the template gutted.
  const list = fixture.nativeElement.querySelector("[data-testid=cf-list]");
  expect(list.textContent).toContain("WI-1");
  expect(list.textContent).not.toContain("WI-2");
  expect(list.querySelectorAll("li").length).toBe(1);

  // @for's filtering is asserted above by what reached the DOM. The @else branch is not
  // exercised here: re-rendering it needs a second fixture under zoneless change
  // detection, and one rendered assertion already fails if the template is removed,
  // which is what this spec has to prove.
});

it("control-flow-blocks: the block syntax needs no directive imported", () => {
  // The structural-directive form renders identical DOM — that is the whole contrast, so
  // no assertion about what is on screen can separate them. What @if and @for change is
  // that control flow became part of the template language: it is compiled in, where
  // *ngIf and *ngFor are directives the component must declare before its template will
  // compile. That difference is visible on the component itself.
  const definition = (ControlFlowComponent as unknown as {
    ɵcmp: { dependencies?: unknown[] | (() => unknown[]) };
  }).ɵcmp;
  const declared = typeof definition.dependencies === "function"
    ? definition.dependencies()
    : definition.dependencies ?? [];

  expect(declared).toHaveLength(0);
});
