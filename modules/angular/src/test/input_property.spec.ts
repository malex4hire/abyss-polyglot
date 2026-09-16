import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection, reflectComponentType } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { FilterBoxComponent } from "../app/filter-box.component";

it("input-property: a setter observes the value changing", () => {
  const fixture = TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
    imports: [FilterBoxComponent],
  }).createComponent(FilterBoxComponent);

  fixture.componentInstance.value = "backend";
  fixture.componentInstance.value = "docs";

  expect(fixture.componentInstance.current).toBe("docs");
  expect(fixture.componentInstance.seen).toEqual(["backend", "docs"]);
});

it("input-property: the setter is declared as an input, not just a setter", () => {
  // Assigning the property directly exercises the setter and passes whether or not the
  // decorator is there — TEST-AUDIT filed this as vacuous, and a rival version without
  // @Input proved it. What @Input adds is that the property joins the component's
  // public interface, so a template can bind to it with [] and Angular sets it during
  // change detection. That is metadata, and it is readable.
  const mirror = reflectComponentType(FilterBoxComponent);

  expect(mirror).not.toBeNull();
  expect(mirror!.inputs.map((input) => input.propName)).toContain("value");
});
