import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { ActivatedRoute } from "@angular/router";
import { BehaviorSubject } from "rxjs";
import { convertToParamMap } from "@angular/router";
import { DetailComponent } from "../app/detail.component";

it("routing-with-params: paramMap is a stream, not a snapshot", () => {
  const paramMap = new BehaviorSubject(convertToParamMap({ id: "WI-1" }));
  TestBed.configureTestingModule({
    imports: [DetailComponent],
    providers: [provideZonelessChangeDetection(), { provide: ActivatedRoute, useValue: { paramMap } }],
  });
  const fixture = TestBed.createComponent(DetailComponent);
  const seen: string[] = [];
  fixture.componentInstance.id$.subscribe((id) => seen.push(id));

  paramMap.next(convertToParamMap({ id: "WI-2" }));

  expect(seen).toEqual(["WI-1", "WI-2"]);
});
