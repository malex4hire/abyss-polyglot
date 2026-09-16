import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { CounterComponent } from "../app/counter.component";

it("property-binding: sets a DOM property, not an attribute", () => {
  const fixture = TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
    imports: [CounterComponent],
  }).createComponent(CounterComponent);
  fixture.componentRef.setInput("busy", true);
  fixture.detectChanges();

  const button = fixture.nativeElement.querySelector(
    "[data-testid=counter]",
  ) as HTMLButtonElement;

  // The lesson, and the thing that fails against `disabled="{{ isBusy }}"`. Square
  // brackets assign the node's *property*, so it is a real boolean and no attribute is
  // written. The interpolated-attribute spelling sets the attribute to the string
  // "false", which is present and therefore truthy — the button disables forever.
  expect(typeof button.disabled).toBe("boolean");
  expect(button.disabled).toBe(true);

  // setInput, not field assignment: assigning the field leaves the view unmarked and
  // no amount of detectChanges re-renders it, which is the lesson next door.
  fixture.componentRef.setInput("busy", false);
  fixture.detectChanges();

  // The discriminating case, and the bug itself. A property binding assigns `false` and
  // writes no attribute. `disabled="{{ isBusy }}"` writes the attribute as the string
  // "false" — present, therefore truthy, therefore disabled forever. When it is true the
  // browser reflects the property back to the attribute, so only the false case can tell
  // the two spellings apart.
  expect(button.disabled).toBe(false);
  expect(button.getAttribute("disabled")).toBeNull();

  // [attr.aria-label] is the other half of the same distinction: an attribute binding,
  // written differently precisely because it is not a property.
  expect(button.getAttribute("aria-label")).toBe("increment");
});
