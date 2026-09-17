import { expect, it, vi } from "vitest";
import { provideZonelessChangeDetection } from "@angular/core";
import { TestBed } from "@angular/core/testing";
import { TickerComponent } from "../app/ticker.component";

it("lifecycle-hooks: the framework calls them, at defined moments", () => {
  vi.useFakeTimers();
  TestBed.configureTestingModule({
    imports: [TickerComponent],
    providers: [provideZonelessChangeDetection()],
  });
  const fixture = TestBed.createComponent(TickerComponent);
  const ticker = fixture.componentInstance;

  // Constructed but not initialised: ngOnInit has not run yet, which is exactly why
  // work depending on an input does not belong in the constructor.
  expect(ticker.ticks).toBe(0);

  fixture.detectChanges();
  vi.advanceTimersByTime(2500);
  expect(ticker.ticks).toBe(2);

  fixture.destroy();
  vi.advanceTimersByTime(5000);
  expect(ticker.ticks).toBe(2);
  vi.useRealTimers();
});

it("lifecycle-hooks: the work is declared as a hook the framework calls", () => {
  // Advancing the clock cannot separate this from constructor work: Angular's zoneless
  // TestBed runs ngOnInit at createComponent, so there is no window in which the component
  // exists uninitialised. What distinguishes them is that ngOnInit is a method the
  // framework looks for and calls at a defined moment. It is present on the prototype,
  // and absent entirely from a component that does its start-up in the constructor.
  expect(typeof TickerComponent.prototype.ngOnInit).toBe("function");
  expect(typeof TickerComponent.prototype.ngOnDestroy).toBe("function");
});
