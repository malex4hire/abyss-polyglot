import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { DraftFormComponent } from "../app/draft-form.component";

it("reactive-form: the model owns validity, not the template", () => {
  const fixture = TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
    imports: [DraftFormComponent],
  }).createComponent(DraftFormComponent);
  const form = fixture.componentInstance.form;

  expect(form.invalid).toBe(true);
  form.patchValue({ title: "migrate scheduler" });
  expect(form.controls.title.valid).toBe(true);
  form.controls.title.setValue("no");
  expect(form.controls.title.hasError("minlength")).toBe(true);
  expect(form.invalid).toBe(true);
});
