import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { FilterBoxComponent } from "../app/filter-box.component";

it("output-event: the child reports upward and the parent decides", () => {
  const fixture = TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
    imports: [FilterBoxComponent],
  }).createComponent(FilterBoxComponent);
  const seen: string[] = [];
  fixture.componentInstance.changed.subscribe((v: string) => seen.push(v));

  fixture.componentInstance.onInput("  backend  ");

  expect(seen).toEqual(["backend"]);
  expect(fixture.componentInstance.current).toBe("backend");
});
