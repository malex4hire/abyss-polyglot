import { AbstractControl, ValidationErrors, ValidatorFn } from "@angular/forms";

/**
 * A range validator, in the ordinary shape: null when valid, an error object when not.
 *
 * Nothing is demonstrated here on purpose. Angular runs every validator when the
 * FormGroup is constructed, so a fault inside one breaks any test that builds the form.
 * Three unrelated specs went red rather than the one that covers validation.
 */
export function priorityRange(min: number, max: number): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = Number(control.value);
    if (control.value === null || control.value === "") {
      return { required: true };
    }
    if (!Number.isInteger(value) || value < min || value > max) {
      return { range: { min, max, actual: control.value } };
    }
    return null;
  };
}

/**
 * Turn a control's errors into something a person can read.
 *
 * This is the half of validation the framework does not do. Angular decides validity and
 * populates an errors object; what those keys mean to a user is the application's
 * problem, and every project writes this function. The keys are the contract between a
 * validator and its message: `required` and `minlength` come from the built-ins,
 * `range` from the validator above.
 *
 * It runs when a message is rendered rather than when the form is built, which is why a
 * fault here fails only the specs about messages, not every test that builds a form.
 *
 * React has no equivalent because it has no errors object: validation there returns
 * whatever shape the author chose, and the message usually is the value.
 */
export function describeErrors(control: AbstractControl): string[] {
  const errors: ValidationErrors | null = control.errors;
  if (!errors) {
    return [];
  }
  return Object.entries(errors).map(([key, detail]) => {
    switch (key) {
      case "required":
        return "this field is required";
      case "minlength":
        return `at least ${(detail as { requiredLength: number }).requiredLength} characters`;
      case "range": {
        const range = detail as { min: number; max: number };
        return `must be between ${range.min} and ${range.max}`;
      }
      default:
        return key;
    }
  });
}
