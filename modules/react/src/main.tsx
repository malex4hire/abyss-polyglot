// The design system, generated from design/tokens.yaml, and the one shared
// stylesheet both applications use.
import "./tokens.generated.css";
import "./app.generated.css";
import "./accent.generated.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Board } from "./components/Board";
import { Tracker } from "./components/Tracker";
import { BoardSettingsProvider } from "./lib/BoardContext";
import { API_BASE } from "./lib/types";
import { reportHeightToEmbedder } from "./lib/embed";

reportHeightToEmbedder();

// Board is the component gallery: it renders every component in this module, so none of
// them is dead code kept alive only by a test. It was mounted below the tracker to keep
// them on a served path, and that put a second application in the same document: its own
// form, its own list, its own item count computed from its own fetch. A person typing
// into the wrong form saw nothing happen, and the page claimed a count that disagreed
// with the rows on screen.
//
// It is still served, at its own route, which keeps every component reachable without
// the application having a gallery stapled underneath it. The static server falls back to
// this document for unknown paths, so the route below resolves with no router.
const showGallery = location.pathname.replace(/\/+$/, "") === "/components";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BoardSettingsProvider value={{ apiBase: API_BASE, pageSize: 5 }}>
      {showGallery ? <Board /> : <Tracker />}
    </BoardSettingsProvider>
  </StrictMode>,
);
