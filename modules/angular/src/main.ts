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
import { reportHeightToEmbedder } from "./lib/embed";

reportHeightToEmbedder();

bootstrapApplication(TrackerComponent, {
  providers: [
    provideHttpClient(),
    provideRouter([
      { path: "items/:id", component: DetailComponent },
      // KNOWN GAP, stated rather than implied: these routes are registered and never
      // render. This application bootstraps TrackerComponent directly and there is no
      // <router-outlet> anywhere in the module, so BoardComponent and DetailComponent are
      // reachable only from their unit tests. React's equivalent works because it reads
      // location.pathname itself (main.tsx) rather than going through a router.
      //
      // Left as a gap rather than papered over: closing it means bootstrapping a shell
      // component with an outlet, which is a change to how the application starts, and
      // this file is not the place to make that quietly. A comment claiming the gallery
      // "stays reachable" stood here first, which is the worse of the two states — an
      // untrue comment is read as a fact and costs the next person the time to disprove it.
      { path: "components", component: BoardComponent },
    ]),
    provideBoardSettings({ pageSize: 5, apiBase: API_BASE }),
  ],
}).catch((error) => console.error(error));
