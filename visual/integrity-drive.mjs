// Checks the application does what it says, on the page a person actually opens.
//
// The host suite verifies structure and provenance: that the manifest and compose agree,
// that identity matches the live classpath, that the contract passes against every
// backend. None of it verifies that the application WORKS on screen. Every defect found
// by looking at a running page has been invisible to all of it, so these live here and
// run against the served document.
import { chromium } from "playwright";
import { requireEnv } from "./env.mjs";

const base = requireEnv("APP");
const label = process.env.LABEL ?? base;
const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
const out = [];
const ok = (n, d = "") => out.push(`  OK    ${n}${d ? "  — " + d : ""}`);
const bad = (n, d = "") => { out.push(`  FAIL  ${n}${d ? "  — " + d : ""}`); process.exitCode = 1; };

await page.goto(base + "/", { waitUntil: "domcontentloaded" });
await page.waitForSelector("[data-testid=tracker] [data-testid=row]", { timeout: 30000 });
await page.waitForTimeout(800);

const app = page.locator("[data-testid=tracker]");
const at = (id) => app.locator(`[data-testid=${id}]`);

// Every active backend, read from the running application, which reads it from the
// manifest. These checks found twelve defects while running against one of four runtimes;
// a defect that only appears against Spring Boot would have passed every time.
const backends = await at("backend-select").locator("option").evaluateAll(
  (options) => options.map((option) => option.value),
);
backends.length > 1
  ? ok("checks run against every active backend", backends.join(", "))
  : bad("checks run against every active backend", `only ${backends.join(",") || "none"} offered`);

// Document-level facts, checked once: they cannot depend on which backend is selected.
const trackers = await page.locator("[data-testid=tracker]").count();
trackers === 1 ? ok("the document contains exactly one tracker")
               : bad("the document contains exactly one tracker", `found ${trackers}`);

const headings = await page.locator("h1").allTextContents();
headings.length === 1 ? ok("one application heading on the page", headings[0])
                      : bad("two applications stacked in one document", headings.join(" | "));

const forms = await page.locator("form").count();
const trackerForms = await page.locator("[data-testid=tracker] form").count();
forms === trackerForms ? ok("every form on the page belongs to the application", `${forms}`)
                       : bad("every form on the page belongs to the application",
                             `${forms} total, ${trackerForms} in the tracker`);

// Behaviour, checked against each runtime in turn.
for (const backend of backends) {
  await at("backend-select").selectOption(backend);
  await page.waitForTimeout(1500);
  await page.waitForSelector("[data-testid=tracker] [data-testid=row]", { timeout: 30000 });

  const before = await at("row").count();
  const title = `Integrity ${backend} ${Date.now().toString().slice(-5)}`;
  await at("new-title").fill(title);
  await at("new-priority").fill("6");
  await at("new-assignee").fill("integrity");
  await at("create").click();
  await page.waitForTimeout(2200);

  const after = await at("row").count();
  const present = await app.locator(`[data-testid=row]:has-text("${title}")`).count();
  after === before + 1 && present === 1
    ? ok(`create adds a row [${backend}]`, `${before} -> ${after}`)
    : bad(`create adds a row [${backend}]`, `${before} -> ${after}, matching row ${present}`);

  // Internal agreement: any count the page displays must match the rows beside it.
  const rows = await at("row").count();
  const text = await page.locator("body").innerText();
  const claims = [...text.matchAll(/(\d+)\s+items?\b/gi)].map((m) => Number(m[1]));
  const wrong = claims.filter((n) => n !== rows);
  wrong.length === 0
    ? ok(`displayed counts agree with the rows [${backend}]`, `${rows} rows`)
    : bad(`displayed counts agree with the rows [${backend}]`,
          `${rows} rows on screen, page claims ${wrong.join(", ")}`);
}

out.push("  note  this run created rows on every backend; make demo-reset restores seed state");

await page.screenshot({ path: `/w/shots/${process.env.SHOT ?? "integrity"}.png`, fullPage: true });
console.log(`\n  ${label}`);
console.log(out.join("\n"));
console.log(errors.length ? "  PAGE ERRORS: " + errors.slice(0, 3).join(" ~ ") : "  no page errors");
await browser.close();
