import { Component } from "@angular/core";
import { RouterOutlet } from "@angular/router";

/**
 * The slot the router renders into.
 *
 * This module registered routes for a long time and never rendered one. It bootstrapped
 * the tracker component directly, so there was no <router-outlet> anywhere in it. The
 * router resolved a route correctly, had nowhere to put the result, and every URL showed
 * the tracker. Both the board and the detail view were reachable only from their unit
 * tests: green, and unreachable, which is the shape this repository exists to catch.
 *
 * The tracker is still what the application IS: it is the default route, it is what the
 * side-by-side page embeds, and "/" is unchanged for every existing consumer. What moves
 * is that the other two are now on a served path, which is the standard the rest of this
 * repository already holds itself to.
 */
@Component({
  selector: "app-shell",
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class ShellComponent {}
