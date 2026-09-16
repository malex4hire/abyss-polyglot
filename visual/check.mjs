// Visual verification of the running demo, and the screenshots it leaves behind.
//
// The host suite proves the parts: that the manifest and compose agree, that identity
// matches the live classpath, that one contract suite passes against every backend. None
// of it looks at a rendered page. A page can satisfy every structural assertion and still
// be blank, unreadable or mis-laid-out — so this drives a real browser against the
// running stack, asserts what a viewer would actually see, and writes the shots out as
// evidence rather than as decoration.
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { requireEnv } from "./env.mjs";

// Resolved from this file, not the working directory: run from the repo root and from
// inside a container mounted on visual/ and both must land in the same place.
const HERE = new URL(".", import.meta.url).pathname;
const SHOTS = `${HERE}shots`;
mkdirSync(SHOTS, { recursive: true });

// Targets from the environment, supplied by scripts/visual.sh from the manifest.
// FRONTENDS is "name=origin name=origin ...".
const PAGE = requireEnv("SIDE_BY_SIDE");
const FRONTENDS = requireEnv("FRONTENDS")
  .split(/\s+/)
  .filter(Boolean)
  .map((entry) => entry.split("="));

const results = [];
function check(name, condition, detail = "") {
  results.push({ name, ok: Boolean(condition), detail });
  console.log(`  ${condition ? "OK  " : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`);
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

// --- the side-by-side page -------------------------------------------------
await page.goto(`${PAGE}/`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(2500);
await page.screenshot({ path: `${SHOTS}/01-side-by-side.png`, fullPage: true });

const frames = await page.$$eval("[data-app-frame]", (nodes) =>
  nodes.map((n) => n.dataset.appFrame));
check("the page puts both frontends side by side",
      frames.length === FRONTENDS.length, frames.join(", "));

// The identity treatment, read off the rendered page rather than off the token file. A
// token emitted and never bound to an element passes every structural check and renders
// a page where the distinction is invisible.
const chips = await page.$$eval(".chip", (nodes) =>
  nodes.map((n) => ({
    colour: getComputedStyle(n).backgroundColor,
    text: n.textContent.trim(),
  })));
check("each side carries a distinct identity colour",
      new Set(chips.map((c) => c.colour)).size === chips.length,
      chips.map((c) => c.colour).join(" / "));
check("each side is also named in text, not by colour alone",
      chips.length > 0 && chips.every((c) => c.text.length > 1),
      chips.map((c) => c.text).join(" / "));

const face = await page.$eval("h1", (n) => getComputedStyle(n).fontFamily);
check("the display face is the self-hosted one", /Fraunces/.test(face), face);

const options = await page.$$eval("[data-testid=split-backend] option", (n) => n.length);
check("every backend is selectable from one control", options > 1, `${options} options`);

// The frames must actually load. An iframe pointing at a dead origin renders an empty
// box, and the page above it looks entirely correct.
for (const [name] of FRONTENDS) {
  const frame = page.frameLocator(`[data-app-frame="${name}"]`);
  const loaded = await frame
    .locator("[data-testid=tracker]")
    .waitFor({ timeout: 20000 })
    .then(() => true)
    .catch(() => false);
  check(`the ${name} frame renders its application`, loaded);
}

// --- each frontend, on its own, against the live contract -------------------
for (const [name, origin] of FRONTENDS) {
  // domcontentloaded plus an explicit wait, not networkidle: a client-side app holds a
  // stream open, so "no network for 500ms" can simply never happen. Waiting for the thing
  // you care about is both faster and more honest than waiting for quiet.
  await page.goto(`${origin}/`, { waitUntil: "domcontentloaded" });
  await page
    .waitForFunction(
      () => document.querySelectorAll("[data-testid=tracker] [data-testid=row]").length > 0,
      null, { timeout: 20000 })
    .catch(() => undefined);
  await page.screenshot({ path: `${SHOTS}/02-${name}.png`, fullPage: true });

  const rows = await page.$$eval("[data-testid=tracker] [data-testid=row]", (n) => n.length);
  check(`${name} renders work items from the backend`, rows > 0, `${rows} rows`);

  const codeFace = await page
    .$eval("[data-testid=tracker]", (n) => getComputedStyle(n).fontFamily)
    .catch(() => "");
  check(`${name} is typeset from the generated tokens`, /Public Sans/.test(codeFace), codeFace);
}

await browser.close();
writeFileSync(`${HERE}results.json`, JSON.stringify(results, null, 2));
const failed = results.filter((r) => !r.ok);
console.log(`\n  ${results.length - failed.length}/${results.length} visual checks passed`);
process.exit(failed.length ? 1 : 0);
