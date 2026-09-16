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
import { provideBoardSettings } from "./lib/providers";
import { API_BASE } from "./lib/types";

bootstrapApplication(TrackerComponent, {
  providers: [
    provideHttpClient(),
    provideRouter([
      { path: "items/:id", component: DetailComponent },
      // The component gallery stays reachable, so no component in this module is dead
      // code kept alive only by a test. The tracker is what the application is.
      { path: "components", component: BoardComponent },
    ]),
    provideBoardSettings({ pageSize: 5, apiBase: API_BASE }),
  ],
}).catch((error) => console.error(error));
