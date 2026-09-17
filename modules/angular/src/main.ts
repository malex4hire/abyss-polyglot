// The JIT compiler, because templates are compiled in the browser rather than by a
// build plugin. See vite.config.ts for why.
// The design system, generated from design/tokens.yaml, and the one shared
// stylesheet both applications use.
import "./tokens.generated.css";
import "./app.generated.css";
import "./accent.generated.css";

import "@angular/compiler";
import "zone.js";
import { bootstrapApplication } from "@angular/platform-browser";
import { provideHttpClient } from "@angular/common/http";
import { provideRouter } from "@angular/router";
import { BoardComponent } from "./app/board.component";
import { TrackerComponent } from "./app/tracker.component";
import { DetailComponent } from "./app/detail.component";
import { ShellComponent } from "./app/shell.component";
import { provideBoardSettings } from "./lib/providers";
import { API_BASE } from "./lib/types";
import { reportHeightToEmbedder } from "./lib/embed";

reportHeightToEmbedder();

bootstrapApplication(ShellComponent, {
  providers: [
    provideHttpClient(),
    // The tracker is the default route rather than the bootstrapped component, so the
    // board and the detail view are reachable in the running application instead of only
    // from their tests. "/" is unchanged for everything that already points at it.
    provideRouter([
      { path: "", component: TrackerComponent },
      { path: "components", component: BoardComponent },
      { path: "items/:id", component: DetailComponent },
    ]),
    provideBoardSettings({ pageSize: 5, apiBase: API_BASE }),
  ],
}).catch((error) => console.error(error));
