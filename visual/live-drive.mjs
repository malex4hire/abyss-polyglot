// A change made in one frontend appears in the other with nobody touching it.
//
// This is the one claim in the repository that nothing short of a browser settles. Two
// framework implementations, two separate pages, one backend: create in the left and it
// must arrive in the right; archive in the right and it must leave the left. No refresh,
// no click on the far side, no polling loop anywhere in either application.
//
// Both directions are driven deliberately. One direction can pass by accident (a
// re-fetch the receiving framework was going to do anyway), and the framework whose
// change detection is doing the noticing is different in each direction, which is
// exactly the asymmetry a single-direction check would hide.
import { chromium } from "playwright";
import { requireEnv } from "./env.mjs";

// Two frontends and the backend to point them both at, supplied by scripts/visual.sh
// from stacks/manifest.yaml. Nothing here names a framework or a port.
const [leftName, leftUrl] = requireEnv("LEFT").split("=");
const [rightName, rightUrl] = requireEnv("RIGHT").split("=");
const BACKEND = requireEnv("BACKEND");

const browser = await chromium.launch();
const left = await browser.newPage();
const right = await browser.newPage();

const out = [];
const ok = (n, d = "") => out.push(`  OK    ${n}${d ? "  (" + d + ")" : ""}`);
const bad = (n, d = "") => {
  out.push(`  FAIL  ${n}${d ? "  (" + d + ")" : ""}`);
  process.exitCode = 1;
};

const rowsOf = (page) => page.locator("[data-testid=tracker] [data-testid=row]");

// Both pages onto the SAME backend. Without this they can be reading two different
// stores, and "it did not arrive" would be correct behaviour reported as a failure.
for (const [page, url] of [[left, leftUrl], [right, rightUrl]]) {
  await page.goto(url + "/", { waitUntil: "domcontentloaded" });
  await page.waitForSelector("[data-testid=tracker] [data-testid=row]", { timeout: 30000 });
  await page.locator("[data-testid=backend-select]").selectOption(BACKEND);
  await page.waitForTimeout(1500);
}

const before = await rowsOf(right).count();
const title = `Live ${Date.now().toString().slice(-5)}`;

// --- created on the left, and it must appear on the right -------------------
const form = left.locator("[data-testid=tracker]");
await form.locator("[data-testid=new-title]").fill(title);
await form.locator("[data-testid=new-priority]").fill("7");
await form.locator("[data-testid=new-assignee]").fill("live");
await form.locator("[data-testid=create]").click();

await right
  .waitForFunction((t) => document.body.innerText.includes(t), title, { timeout: 20000 })
  .then(() => ok(`a change in ${leftName} appears in ${rightName} with no user action`, title))
  .catch(async () =>
    bad(`a change in ${leftName} appears in ${rightName} with no user action`,
        `${before} rows before, ${await rowsOf(right).count()} after`));

// --- and the other direction: archived on the right, gone from the left -----
//
// Not a symmetry check for its own sake. The receiving framework is the other one this
// time, with a completely different model for noticing that data changed, so this is the
// half that says the stream is doing the work rather than one framework's own refresh.
const target = rowsOf(right).filter({ hasText: title }).first();
const leftBefore = await rowsOf(left).count();
await target.locator("[data-testid=archive]").click();

await left
  .waitForFunction(
    (n) => document.querySelectorAll("[data-testid=tracker] [data-testid=row]").length < n,
    leftBefore, { timeout: 20000 })
  .then(() => ok(`an archive in ${rightName} reaches ${leftName} with no user action`))
  .catch(async () =>
    bad(`an archive in ${rightName} reaches ${leftName} with no user action`,
        `${leftBefore} rows before, ${await rowsOf(left).count()} after`));

console.log(`\n  live update: ${leftName} <-> ${rightName} over ${BACKEND}`);
console.log(out.join("\n"));
await browser.close();
