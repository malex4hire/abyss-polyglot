// One selector, both frames.
//
// Re-pointing an iframe at the same application with a backend named in the query string
// is the whole mechanism: each application already reads that parameter on arrival, so
// nothing here knows anything about either framework — not a component name, not a route,
// not a bundle. The page could not tell you which frame is Angular.

const control = document.querySelector("[data-testid=split-backend]");

if (control) {
  control.addEventListener("change", () => {
    document.querySelectorAll("[data-app-frame]").forEach((frame) => {
      const base = new URL(frame.getAttribute("src"), location.href);
      base.searchParams.set("backend", control.value);
      frame.setAttribute("src", base.toString());
    });
  });
}
