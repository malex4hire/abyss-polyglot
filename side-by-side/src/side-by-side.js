// One selector, both frames.
//
// Re-pointing an iframe at the same application with a backend named in the query string
// is the whole mechanism: each application already reads that parameter on arrival, so
// nothing here knows anything about either framework — not a component name, not a route,
// not a bundle. The page could not tell you which frame is Angular.

// --- frames size themselves ------------------------------------------------------
//
// Each application posts its own height (modules/*/src/lib/embed.ts) because this page
// cannot read it: the frames are a different origin. The fixed height in the stylesheet is
// only what they start at, before the first message arrives.

const framed = new Map(
  [...document.querySelectorAll("[data-app-frame]")].map(
    (frame) => [new URL(frame.getAttribute("src"), location.href).origin, frame],
  ),
);

window.addEventListener("message", (event) => {
  // Only from an origin we actually embedded. `postMessage` is reachable by anything that
  // can get a handle on this window, so the sender is checked before the payload is.
  const frame = framed.get(event.origin);
  if (!frame) return;

  const message = event.data;
  if (!message || message.type !== "abyss:frame-height") return;

  const height = Number(message.height);
  // A bounded, positive number. An unbounded one is a frame that can be told to be a
  // hundred thousand pixels tall by whatever is inside it.
  if (!Number.isFinite(height) || height <= 0 || height > 20000) return;

  // The reported height is CONTENT. This stylesheet puts a border on the frame and sets
  // box-sizing: border-box, so assigning the content height directly leaves the border
  // eating two pixels off it — enough for a scrollbar to appear inside a frame that was
  // just sized to need none. offsetHeight - clientHeight is exactly that difference,
  // measured rather than assumed, so a border change does not silently reintroduce it.
  const chrome = frame.offsetHeight - frame.clientHeight;
  frame.style.height = `${Math.ceil(height) + chrome}px`;
});


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
