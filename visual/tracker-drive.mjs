// Drives both trackers through the interface, the way a person would.
//
// Every query is scoped to [data-testid=tracker]. The React module renders the component
// board on the same page and it carries a data-testid=row of its own, so an unscoped
// query read the wrong table and timed out looking for controls that were never there.
import { chromium } from "playwright";
import { requireEnv } from "./env.mjs";

const base = requireEnv("APP");
const label = process.env.LABEL ?? base;
const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));

const out = [];
const ok = (n, d = "") => out.push(`  OK    ${n}${d ? "  (" + d + ")" : ""}`);
const bad = (n, d = "") => { out.push(`  FAIL  ${n}${d ? "  (" + d + ")" : ""}`); process.exitCode = 1; };

await page.goto(base + "/", { waitUntil: "domcontentloaded" });
await page.waitForSelector("[data-testid=tracker] [data-testid=row]", { timeout: 30000 });
const app = page.locator("[data-testid=tracker]");
const at = (id) => app.locator(`[data-testid=${id}]`);

// create, refused by validation and surfaced to the user
await at("new-title").fill("no");
await at("new-priority").fill("99");
await at("create").click();
const errs = await app.locator("[data-testid=create-errors] li").allTextContents();
errs.length >= 3 ? ok("create validation is surfaced", `${errs.length} errors`)
                 : bad("create validation is surfaced", JSON.stringify(errs));

// create, accepted
const startRows = await at("row").count();
await at("new-title").fill("Drive check item");
await at("new-priority").fill("4");
await at("new-assignee").fill("driver");
await at("create").click();
await page.waitForTimeout(1500);
const afterCreate = await at("row").count();
afterCreate === startRows + 1 ? ok("create adds a row", `${startRows} -> ${afterCreate}`)
                              : bad("create adds a row", `${startRows} -> ${afterCreate}`);

// B1 status filter
await at("filter-status").selectOption("OPEN");
await page.waitForTimeout(1000);
const byStatus = await at("row").count();
byStatus > 0 && byStatus < afterCreate ? ok("status filter narrows", `${afterCreate} -> ${byStatus}`)
                                       : bad("status filter narrows", `${afterCreate} -> ${byStatus}`);
await at("filter-status").selectOption("");
await page.waitForTimeout(1000);

// B1 tag filter
await at("filter-tag").fill("legacy");
await page.waitForTimeout(1200);
const byTag = await at("row").count();
byTag > 0 && byTag < afterCreate ? ok("tag filter narrows", `${afterCreate} -> ${byTag}`)
                                 : bad("tag filter narrows", `${afterCreate} -> ${byTag}`);
await at("filter-tag").fill("");
await page.waitForTimeout(1200);

// B1 sort
await at("sort").selectOption("title");
await page.waitForTimeout(400);
const titles = await app.locator("[data-testid=row] td:nth-child(2)").allTextContents();
const expected = [...titles].sort((a, b) => a.localeCompare(b));
JSON.stringify(titles) === JSON.stringify(expected) ? ok("sort by title reorders", titles[0])
                                                    : bad("sort by title reorders", titles.join(" | "));
await at("sort").selectOption("priority");
await page.waitForTimeout(400);

// B2 refused
const rows = at("row");
let refused = false;
for (let i = 0; i < await rows.count(); i++) {
  const select = rows.nth(i).locator("[data-testid=row-status]");
  if ((await select.inputValue()) === "OPEN") {
    await select.selectOption("DONE");
    await page.waitForTimeout(1500);
    refused = (await at("rejection").count()) > 0;
    break;
  }
}
refused ? ok("illegal transition refused and shown", (await at("rejection").innerText()).trim().slice(0, 48))
        : bad("illegal transition refused and shown");

// B2 applied
let applied = false;
for (let i = 0; i < await rows.count(); i++) {
  const select = rows.nth(i).locator("[data-testid=row-status]");
  if ((await select.inputValue()) === "OPEN") {
    await select.selectOption("IN_PROGRESS");
    await page.waitForTimeout(1500);
    applied = (await at("row-status").evaluateAll((els) => els.filter((e) => e.value === "IN_PROGRESS").length)) > 0;
    break;
  }
}
applied ? ok("legal transition applies") : bad("legal transition applies");

// B3, and whichever of the two states the click produces first.
//
// This counted [data-testid=workload-loading] immediately after the click and failed when
// it found none. The count was not zero because the answer arrived first. It was zero
// because NEITHER FRONTEND CARRIED THAT TEST ID. Both render a loading card with a
// progress bar and neither labelled it, so the check was red on every run for the life of
// the build and its failure message blamed the machine being fast. The test id is now on
// both, which is what makes the assertion below able to pass at all.
//
// Racing the two outcomes rather than counting one: the loading card can legitimately be
// gone by the time a fast machine looks, and a check that fails on speed measures the
// machine. Either state is a pass, the report says which was seen, and neither within the
// timeout is the real failure.
await at("run-workload").click();
const outcome = await Promise.race([
  at("workload-loading").first().waitFor({ timeout: 30000 }).then(() => "loading"),
  app.locator("[data-testid=workload]").waitFor({ timeout: 30000 }).then(() => "answer"),
]).catch(() => null);
await app.locator("[data-testid=workload]").waitFor({ timeout: 30000 });
const workload = (await at("workload").innerText()).replace(/\s+/g, " ").trim();
outcome
  ? ok(`aggregate responds to the click (saw the ${outcome} state first)`,
       workload.slice(0, 44))
  : bad("aggregate produced neither a loading state nor an answer");

// archive
const beforeArchive = await at("row").count();
await at("archive").first().click();
await page.waitForTimeout(1500);
const afterArchive = await at("row").count();
afterArchive === beforeArchive - 1 ? ok("archive removes the row", `${beforeArchive} -> ${afterArchive}`)
                                   : bad("archive removes the row", `${beforeArchive} -> ${afterArchive}`);

// backend switch with no reload
await page.evaluate(() => { window.__stillHere = true; });
await at("backend-select").selectOption("spring-boot");
await page.waitForTimeout(2000);
const survived = await page.evaluate(() => window.__stillHere === true);
const afterSwitch = await at("row").count();
survived && afterSwitch > 0 ? ok("backend switches with no reload", `spring-boot, ${afterSwitch} rows`)
                            : bad("backend switches with no reload", `reloaded=${!survived} rows=${afterSwitch}`);

await page.screenshot({ path: `/w/shots/${process.env.SHOT ?? "tracker"}.png`, fullPage: true });
console.log(`\n  ${label}`);
console.log(out.join("\n"));
console.log(errors.length ? "  PAGE ERRORS: " + errors.slice(0, 2).join(" ~ ") : "  no page errors");
await browser.close();
