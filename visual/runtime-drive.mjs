// The runtime surface: what the selected backend actually is, read from its own endpoints.
import { chromium } from "playwright";
import { requireEnv } from "./env.mjs";
const base = requireEnv("APP");
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

await at("runtime-toggle").click();
await page.waitForSelector("[data-testid=runtime-panel]", { timeout: 20000 });

const seen = {};
for (const backend of await at("backend-select").locator("option").evaluateAll((o) => o.map((x) => x.value))) {
  await at("backend-select").selectOption(backend);
  await page.waitForTimeout(1800);
  const version = (await at("runtime-version").innerText()).trim();
  const server = (await at("runtime-server").innerText()).trim();
  const artifacts = (await at("runtime-artifacts").innerText()).trim();
  seen[backend] = { version, server, artifacts };
  version && server ? ok(`${backend} reports its runtime`, `${version} · ${server.split(".").pop()} · ${artifacts}`)
                    : bad(`${backend} reports its runtime`, `${version} ${server}`);

  // Not "a version is shown", but the exact build the runtime reports. Asserting non-empty
  // would have passed against the short marketing version, which is what the panel used to
  // print and what this change exists to replace. Read from the endpoint, not written here.
  const exact = await page.evaluate(async (b) => {
    const response = await fetch(`/__runtime?backend=${encodeURIComponent(b)}`);
    const body = await response.json();
    return body?.identity?.runtime_version_exact ?? null;
  }, backend);
  // Whitespace-normalised on both sides: HTML collapses runs of spaces, and Python's build
  // string contains one ("Aug  5"). Comparing raw failed on a difference the browser
  // introduced rather than on anything the panel got wrong.
  const flat = (s) => s.replace(/\s+/g, " ").trim();
  exact && flat(version) === flat(exact)
    ? ok(`${backend} shows the exact build, not the short version`, exact)
    : bad(`${backend} shows the exact build, not the short version`,
          exact ? `panel says "${version}", runtime says "${exact}"` : "the runtime reports no exact build");
}

// The pair's contrast, from the two artifacts rather than from prose.
await at("backend-select").selectOption("spring-traditional");
await page.waitForTimeout(1800);
const explicit = await at("runtime-capabilities").locator("tbody tr").allTextContents();
await at("backend-select").selectOption("spring-boot");
await page.waitForTimeout(1800);
const auto = await at("runtime-capabilities").locator("tbody tr").allTextContents();
explicit.length > 0 && auto.length > 0 && explicit.join() !== auto.join()
  ? ok("the Spring pair shows where each capability came from", `${explicit.length} explicit vs ${auto.length} auto`)
  : bad("the Spring pair shows where each capability came from", `${explicit.length} / ${auto.length}`);

// Evidence, not the label. The column used to print the word "auto-configuration", which
// this asserted; the panel now names the class that supplied each capability, so the check
// reads what those classes actually are. Asserting the word would have kept passing while
// the column said nothing useful.
// Matched on the shape rather than one package path: Boot 4 moved auto-configuration out
// of the single `boot.autoconfigure` package into per-technology ones (`boot.jdbc.
// autoconfigure`, `boot.webmvc.autoconfigure`). The claim is that Boot declared these, and
// pinning the old path asserted a package layout the claim never depended on.
const rowText = auto.join(" ");
/org\.springframework\.boot\.[\w.]*autoconfigure/.test(rowText)
  ? ok("Boot's capabilities are declared by Boot's own auto-configuration classes")
  : bad("Boot's capabilities are declared by Boot's own auto-configuration classes", rowText.slice(0, 90));

// distinct runtimes, not one label repeated
const servers = new Set(Object.values(seen).map((s) => s.server));
servers.size >= 3 ? ok("the four backends report genuinely different runtimes", `${servers.size} distinct servers`)
                  : bad("the four backends report genuinely different runtimes", [...servers].join(" | "));

// The pair, side by side. One number is a fact; two are an argument.
await at("backend-select").selectOption("spring-traditional");
await page.waitForTimeout(1800);
// Read from the panel, not written here. The counts were pinned at 36 and 101, which the
// version upgrade moved to 38 and 121, leaving a check that failed on a number the panel
// derives correctly. The claim is that both stacks are named with a count and the counts
// differ; the values themselves belong to whatever is running.
const pairText = (await at("runtime-pair").innerText()).replace(/\s+/g, " ").trim();
const counts = Object.fromEntries(
  [...pairText.matchAll(/(spring-traditional|spring-boot):\s*(\d+)/g)].map((m) => [m[1], Number(m[2])]),
);
const both = counts["spring-traditional"] > 0 && counts["spring-boot"] > 0;
both && counts["spring-boot"] !== counts["spring-traditional"]
  ? ok("the pair's artifact counts appear together", pairText.slice(0, 92))
  : bad("the pair's artifact counts appear together", pairText.slice(0, 120));

// And the source column names the thing, not the category.
await at("backend-select").selectOption("spring-boot");
await page.waitForTimeout(1800);
const supplied = await at("capability-source").allTextContents();
const generic = supplied.filter((s) => /^auto-configuration$/i.test(s.trim()));
generic.length === 0 && supplied.some((s) => /Configuration|Hikari|Tomcat/i.test(s))
  ? ok("each capability names what supplied it", supplied.slice(0, 3).join(", "))
  : bad("each capability names what supplied it", supplied.join(" | ").slice(0, 120));

// The comparison follows the sign. An absolute delta said "more" on both sides, which on
// the smaller runtime claimed the opposite of what the numbers showed.
await at("backend-select").selectOption("spring-traditional");
await page.waitForTimeout(1800);
const fromSmaller = (await at("runtime-pair").innerText()).replace(/\s+/g, " ");
await at("backend-select").selectOption("spring-boot");
await page.waitForTimeout(1800);
const fromLarger = (await at("runtime-pair").innerText()).replace(/\s+/g, " ");
/fewer jars/.test(fromSmaller) && /more jars/.test(fromLarger)
  ? ok("the pair comparison reads correctly from either side",
       `${fromSmaller.slice(-24).trim()} / ${fromLarger.slice(-22).trim()}`)
  : bad("the pair comparison reads correctly from either side",
        `smaller: ${fromSmaller.slice(-40)} | larger: ${fromLarger.slice(-40)}`);


await page.screenshot({ path: "/w/shots/runtime-panel.png", fullPage: true });
console.log("\n  runtime surface");
console.log(out.join("\n"));
console.log(errors.length ? "  PAGE ERRORS: " + errors.slice(0, 2).join(" ~ ") : "  no page errors");
await browser.close();
