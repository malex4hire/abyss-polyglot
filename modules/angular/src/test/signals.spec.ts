import { expect, it } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";
import { SelectionStore } from "../lib/selection.store";

it("signals: a computed recomputes from what it read", () => {
  TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
  });
  const store = TestBed.inject(SelectionStore);

  expect(store.count()).toBe(0);
  store.select("WI-1");
  store.select("WI-1");
  store.select("WI-2");

  expect(store.count()).toBe(2);
});
