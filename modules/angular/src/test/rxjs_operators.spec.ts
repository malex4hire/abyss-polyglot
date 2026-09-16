import { expect, it, vi } from "vitest";
import { TestBed } from "@angular/core/testing";

import { of, Subject } from "rxjs";
import { filtered } from "../lib/operators";
import { WorkItem } from "../lib/types";

const AT = "2026-01-01T00:00:00Z";
const make = (id: string, tags: string[]): WorkItem => ({
  id, title: id, status: "OPEN", priority: 1, assignee: "a",
  createdAt: AT, updatedAt: AT, tags, archivedAt: null,
});

it("rxjs-operators: a pipeline describes the data flow", async () => {
  const filter$ = new Subject<string>();
  const seen: WorkItem[][] = [];
  filtered(of([make("WI-1", ["backend"]), make("WI-2", ["docs"])]), filter$).subscribe(
    (items) => seen.push(items),
  );

  filter$.next("docs");
  await new Promise((resolve) => setTimeout(resolve, 200));

  expect(seen.at(-1)!.map((i) => i.id)).toEqual(["WI-2"]);
});
