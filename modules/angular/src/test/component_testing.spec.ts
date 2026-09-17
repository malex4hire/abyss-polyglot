import { expect, it } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";
import { EmptyStateComponent } from "../app/empty-state.component";

/**
 * Test a component through TestBed, the framework's own harness.
 *
 * TestBed builds a miniature injector and compiles the component for real, so what is
 * under test is the rendered output and the wiring rather than the class in isolation. A
 * ComponentFixture gives access to both the instance and the DOM it produced.
 *
 * detectChanges is the part that surprises people: Angular does not re-render because a
 * field changed, it re-renders when change detection runs, and in a test that is manual.
 * Forgetting it is why an assertion sees the previous value, which is asserted below
 * rather than described, because it is the whole difference from a framework that
 * re-renders on its own.
 *
 * Declared demo_only: a test harness is not on a served request path by construction.
 */
it("component-testing: compiles for real, and change detection is manual", () => {
  TestBed.configureTestingModule({
    imports: [EmptyStateComponent],
    providers: [provideZonelessChangeDetection()],
  });
  const fixture = TestBed.createComponent(EmptyStateComponent);

  fixture.detectChanges();
  expect(fixture.nativeElement.textContent).toContain("nothing selected");

  // setInput is how the framework sets an input, and how a test should: assigning the
  // field directly leaves the view unmarked, so no amount of detectChanges re-renders it.
  fixture.componentRef.setInput("message", "pick one");
  expect(fixture.nativeElement.textContent).toContain("nothing selected");

  fixture.detectChanges();
  expect(fixture.nativeElement.textContent).toContain("pick one");
});
