import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";

import { CounterComponent } from "../app/counter.component";

it("event-binding: binds an event to a statement", () => {
  const fixture = TestBed.configureTestingModule({
    providers: [provideZonelessChangeDetection()],
    imports: [CounterComponent],
  }).createComponent(CounterComponent);
  const seen: number[] = [];
  fixture.componentInstance.changed.subscribe((n: number) => seen.push(n));
  fixture.detectChanges();

  // A real click, not a call to the handler. Calling bump() directly asserts that a method
  // increments a field, which is true whether or not any binding exists. A counter that
  // attached the listener by hand in ngOnInit passed it unchanged. The binding is what
  // connects the element to the statement, so the element has to be clicked.
  const button: HTMLButtonElement = fixture.nativeElement.querySelector("button");
  button.click();
  button.click();

  expect(fixture.componentInstance.count).toBe(2);
  expect(seen).toEqual([1, 2]);
});

it("event-binding: the listener is declared in the template", () => {
  // Attaching the listener by hand in a lifecycle hook produces the same clicks and the
  // same count. A counter that does exactly that passes every assertion above. What the
  // binding adds is that the element declares what it does, and Angular compiles that into
  // a listener instruction. The compiled template is a function whose source a test reads.
  const compiled = String(
    (CounterComponent as unknown as { ɵcmp: { template: unknown } }).ɵcmp.template,
  );

  expect(compiled).toMatch(/listener/);
});
