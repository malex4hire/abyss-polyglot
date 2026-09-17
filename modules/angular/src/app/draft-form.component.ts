import { Component, EventEmitter, Output, inject } from "@angular/core";
import { FormBuilder, ReactiveFormsModule, Validators } from "@angular/forms";
import { describeErrors, priorityRange } from "../lib/validation";

@Component({
  selector: "app-draft-form",
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form data-testid="draft-form" [formGroup]="form" (ngSubmit)="submit()">
      <input aria-label="title" formControlName="title" />
      <input aria-label="priority" formControlName="priority" />
      <input aria-label="assignee" formControlName="assignee" />
      <button type="submit" [disabled]="form.invalid">add</button>
      @if (form.controls.title.touched && form.controls.title.invalid) {
        @for (message of titleErrors(); track message) {
          <p data-testid="error-title">{{ message }}</p>
        }
      }
    </form>
  `,
})
export class DraftFormComponent {
  private readonly fb = inject(FormBuilder);
  @Output() submitted = new EventEmitter<unknown>();

  readonly form = this.buildForm();

  /**
   * The form as a model in the class, not state scraped from the DOM.
   *
   * A FormGroup owns the values and the validity, and the template binds to it rather
   * than defining it. That inversion is the whole difference from template-driven forms:
   * the model is testable without rendering anything, and validity is derived from the
   * controls rather than tracked by hand.
   *
   * React's counterpart is state plus a validate function the component calls itself:
   * less machinery, and no framework-owned validity to ask.
   */
  private buildForm() {
    return this.fb.nonNullable.group({
      title: ["", [Validators.required, Validators.minLength(3)]],
      priority: ["", [priorityRange(1, 10)]],
      assignee: ["", [Validators.required]],
    });
  }

  titleErrors(): string[] {
    return describeErrors(this.form.controls.title);
  }

  submit(): void {
    if (this.form.valid) {
      this.submitted.emit(this.form.getRawValue());
      this.form.reset();
    }
  }
}
