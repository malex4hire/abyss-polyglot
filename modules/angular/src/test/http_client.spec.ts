import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { provideHttpClient, HttpClient } from "@angular/common/http";
import { HttpTestingController, provideHttpClientTesting } from "@angular/common/http/testing";
import { loadItems } from "../lib/http-client";

it("http-client: cold observable, and non-2xx throws", () => {
  TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection(), provideHttpClient(), provideHttpClientTesting()],
  });
  const http = TestBed.inject(HttpClient);
  const controller = TestBed.inject(HttpTestingController);

  const stream = loadItems(http);
  controller.expectNone(() => true);

  const seen: unknown[][] = [];
  stream.subscribe((items) => seen.push(items));
  controller.expectOne((r) => r.url.endsWith("/work-items")).flush({ items: [] });
  expect(seen).toHaveLength(1);
});
