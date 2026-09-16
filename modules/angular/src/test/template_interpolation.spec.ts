import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { BadgeComponent } from "../app/badge.component";

it("template-interpolation: writes an expression result as text", () => {
  const fixture = TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
    imports: [BadgeComponent],
  }).createComponent(BadgeComponent);
  fixture.componentInstance.status = "DONE";
  fixture.detectChanges();

  expect(fixture.nativeElement.querySelector("[data-testid=badge]").textContent)
    .toContain("complete (DONE)");
});

it("template-interpolation: the value is interpolated, not bound as a property", () => {
  // Binding [textContent] puts the same text in the same element, so the rendered DOM is
  // identical and nothing on screen can separate them — a correct counter proved it. The
  // difference is in what Angular compiled the template to: an interpolation emits a
  // textInterpolate instruction, a property binding emits property. The assertion has to
  // discriminate the two, and compiled output is the one layer where it can.
  const compiled = String(
    (BadgeComponent as unknown as { ɵcmp: { template: unknown } }).ɵcmp.template,
  );

  expect(compiled).toMatch(/textInterpolate/);
  expect(compiled).not.toMatch(/\bproperty\(/);
});
