import { expect, it } from "vitest";
import { FormControl, Validators } from "@angular/forms";
import { describeErrors } from "../lib/validation";

it("form-validation: error keys are the contract between a validator and its message", () => {
  const empty = new FormControl("", [Validators.required]);
  expect(describeErrors(empty)).toEqual(["this field is required"]);

  const short = new FormControl("no", [Validators.minLength(3)]);
  short.updateValueAndValidity();
  expect(describeErrors(short)).toEqual(["at least 3 characters"]);

  const valid = new FormControl("plenty long", [Validators.required]);
  expect(describeErrors(valid)).toEqual([]);
});
