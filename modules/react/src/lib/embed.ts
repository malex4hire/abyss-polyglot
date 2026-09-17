// Report our own height to a page that has embedded us.
//
// The side-by-side page shows both applications in iframes. It is served from a different
// origin than either of them, so it cannot read scrollHeight across the boundary and has
// no way to size a frame to its contents. The frame therefore got a fixed height, and a
// fixed height is wrong at every width except the one it was measured at.
//
// Two things happen here, and the first is the one that matters:
//
//  1. The application stops asserting `min-height: 100vh`. Inside an iframe `100vh` is the
//     FRAME's height, not the window's, so a frame taller than the content stretched the
//     layout and dropped the slack between the filter rail and the table, which left a
//     391px hole in the middle of the screen that did not exist when the app was viewed
//     on its own.
//     It also makes the measurement below a ratchet: the content can never report itself
//     shorter than the frame it is already in.
//
//  2. It reports its real height, and keeps reporting as that height changes: a row
//     added, a filter narrowing the list, the workload panel opening.
//
// This file is byte-identical in both frontends and the suite checks that it stays so.
// Sizing an embedded frame is not framework work, and a difference here would be one
// application being given an advantage the other does not have.

const MESSAGE = "abyss:frame-height";

export function reportHeightToEmbedder(): void {
  if (window.parent === window) {
    return;
  }

  // Layout first, measurement second. See (1) above.
  document.documentElement.classList.add("embedded");

  let last = 0;
  const report = (): void => {
    // The BODY box, not documentElement.scrollHeight.
    //
    // documentElement fills the viewport when the content is shorter than it, so once the
    // frame had been made taller than the content it reported the frame's own height
    // back, which is a measurement that could only ever grow. It got there via a transient
    // scrollbar: the frame starts short, the content overflows, a scrollbar appears, the
    // narrower content is 46px taller, the frame is set to that, the scrollbar goes away
    // and the real height is never reported again.
    //
    // body carries no margin here and is not stretched, so its box is the content.
    const height = Math.ceil(document.body.getBoundingClientRect().height);
    // Only on a real change. A ResizeObserver fires for its own effects, and posting on
    // every one of them is a message loop with a repaint in it.
    if (height > 0 && height !== last) {
      last = height;
      window.parent.postMessage({ type: MESSAGE, height }, "*");
    }
  };

  new ResizeObserver(report).observe(document.body);
  window.addEventListener("load", report);
  report();
}
