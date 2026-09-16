import { Component, OnDestroy, OnInit } from "@angular/core";

@Component({
  selector: "app-ticker",
  standalone: true,
  template: `<span data-testid="ticker">{{ ticks }}</span>`,
})
export class TickerComponent implements OnInit, OnDestroy {
  ticks = 0;
  private handle?: ReturnType<typeof setInterval>;

  /**
   * Set up when the component starts, tear down when it ends.
   *
   * ngOnInit runs after the first inputs are set, which is why work depending on an
   * @Input belongs here rather than in the constructor — at construction the inputs are
   * still undefined. ngOnDestroy is the other half, and an interval is exactly the kind
   * of thing that outlives its component without it.
   *
   * They are interface methods the framework calls, so implementing OnInit is a
   * declaration of intent the compiler checks rather than a name it hopes you spelled
   * correctly.
   */
  ngOnInit(): void {
    this.handle = setInterval(() => (this.ticks += 1), 1000);
  }

  ngOnDestroy(): void {
    if (this.handle !== undefined) {
      clearInterval(this.handle);
    }
  }
}
