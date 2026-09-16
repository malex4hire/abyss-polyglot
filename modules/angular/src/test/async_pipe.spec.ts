import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { of } from "rxjs";
import { TitlesComponent } from "../app/async-pipe.component";
import { WorkItem } from "../lib/types";

const AT = "2026-01-01T00:00:00Z";
const make = (id: string): WorkItem => ({
  id, title: `t-${id}`, status: "OPEN", priority: 1, assignee: "a",
  createdAt: AT, updatedAt: AT, tags: [], archivedAt: null,
});

it("async-pipe: the template owns the subscription", () => {
  const fixture = TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
    imports: [TitlesComponent],
  }).createComponent(TitlesComponent);
  fixture.componentInstance.items$ = of([make("WI-1"), make("WI-2")]);
  fixture.detectChanges();

  expect(fixture.nativeElement.querySelector("[data-testid=titles]").textContent)
    .toContain("t-WI-1, t-WI-2");
});
