import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { provideHttpClient } from "@angular/common/http";
import { HttpTestingController, provideHttpClientTesting } from "@angular/common/http/testing";
import { WorkItemService } from "../lib/work-item.service";

it("service-injection: one instance, shared by the root injector", () => {
  TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection(), provideHttpClient(), provideHttpClientTesting()],
  });

  const first = TestBed.inject(WorkItemService);
  const second = TestBed.inject(WorkItemService);
  expect(first).toBe(second);

  // list() uses the injected client directly, so this exercises the injection rather
  // than the shared loader, which another spec already covers.
  const seen: unknown[] = [];
  first.list({ tag: "backend" }).subscribe((items) => seen.push(items));
  const request = TestBed.inject(HttpTestingController).expectOne(
    (candidate) =>
      candidate.url.split("?")[0].endsWith("/work-items") &&
      candidate.params.get("tag") === "backend",
  );
  request.flush({ items: [] });
  expect(seen).toHaveLength(1);
});
