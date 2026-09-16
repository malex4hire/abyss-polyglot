import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { WorkItemRowComponent } from "../app/work-item-row.component";
import { WorkItem } from "../lib/types";

const AT = "2026-01-01T00:00:00Z";
const item: WorkItem = {
  id: "WI-1", title: "migrate", status: "OPEN", priority: 7, assignee: "avery",
  createdAt: AT, updatedAt: AT, tags: ["backend"], archivedAt: null,
};

it("standalone-component: declares its own dependencies, no NgModule", () => {
  const fixture = TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
    imports: [WorkItemRowComponent],
  }).createComponent(WorkItemRowComponent);
  fixture.componentInstance.item = item;
  fixture.detectChanges();

  const text = fixture.nativeElement.textContent;
  expect(text).toContain("migrate");
  expect(text).toContain("OPEN");
  const described = fixture.componentInstance.describeSelf();
  expect(described.standalone).toBe(true);
  expect(described.selector).toBe("app-work-item-row");
  expect(described.inputs).toContain("item");
});
