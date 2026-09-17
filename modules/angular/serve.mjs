// A static server with no dependencies and no child processes.
//
// The frontends previously ran `vite dev`, which spawns an esbuild child per transform
// and does not reap them: a healthcheck polling every few seconds left hundreds of zombie
// processes and a heavily loaded machine after an hour. A dev server is for developing,
// not for being left running.
//
// This serves the bundle built at image build time. The toolchain stays in the image so
// the test suite can still run inside the running container against bind-mounted source,
// but nothing compiles at demo time, which is also what lets the demo run with no
// network.
import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer, request as proxyRequest } from "node:http";
import { extname, join, normalize } from "node:path";

const ROOT = new URL("./dist/", import.meta.url).pathname;
const PORT = Number(process.env.PORT ?? 8080);

// Vite inlines import.meta.env at build time, so a runtime API base never reaches a built
// bundle. The page fetched from its own origin and rendered nothing. Rather than bake a
// URL into the image, the contract paths are proxied to the backend named at runtime,
// which also makes every request same-origin and removes CORS from the picture.
const API = new URL(process.env.API_BASE ?? "http://localhost:8080");
const PROXIED = ["/work-items", "/workload", "/health"];

// Every selectable backend, injected from stacks/manifest.yaml via .env. The frontend
// never carries a stack list: it asks here, at runtime, and a backend activated in the
// manifest appears as an option with no change to any frontend source.
const BACKENDS = JSON.parse(process.env.BACKENDS_JSON ?? "{}");

// The framework version, not the JVM underneath it. spring-boot and spring-traditional
// both run the same base image, so their runtime_version is identical by construction.
// Showing it as "the version" told a reader nothing about which framework they were
// actually comparing. Read from the artifact whose name and version the framework itself
// ships as, which is the same jar-suffix pattern the host-side runtime-identity check
// uses to read version floors.
const VERSION_IN_JAR = /-(\d+(?:\.\d+)*)(?:\.[A-Za-z][\w.]*)?\.jar$/;
function frameworkVersion(frameworkArtifact, identity) {
  if (!frameworkArtifact || !identity?.artifacts) {
    return null;
  }
  for (const entry of identity.artifacts) {
    if (entry.startsWith(`${frameworkArtifact}-`)) {
      const match = VERSION_IN_JAR.exec(entry);
      if (match) {
        return match[1];
      }
    }
  }
  return null;
}

function upstreamFor(pathname) {
  // /api/<backend-id>/<contract path>: the id chosen in the browser, resolved here.
  const match = /^\/api\/([^/]+)(\/.*)$/.exec(pathname);
  if (match && BACKENDS[match[1]]) {
    return { origin: new URL(BACKENDS[match[1]].origin), path: match[2] };
  }
  if (PROXIED.some((prefix) => pathname.startsWith(prefix))) {
    return { origin: API, path: pathname };
  }
  return null;
}

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".ico": "image/x-icon",
};

createServer((request, response) => {
  const url = new URL(request.url, "http://localhost");

  if (url.pathname === "/__instrumentation/identity") {
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({
      runtime_version: process.versions.node,
      // Node's own version is already exact; what the panel was missing is which
      // engine is under it, since that is what actually runs the shipped code.
      runtime_version_exact: `${process.version} (V8 ${process.versions.v8})`,
      runtime_vendor: `V8 ${process.versions.v8}`,
      http_server_class: "node.http.Server",
      artifacts: JSON.parse(process.env.RESOLVED_ARTIFACTS ?? "[]"),
    }));
    return;
  }

  if (url.pathname === "/__backends") {
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({
      backends: Object.entries(BACKENDS).map(([id, spec]) => ({ id, label: spec.label })),
    }));
    return;
  }


  if (url.pathname === "/__runtime") {
    // What the selected backend actually is, read from the artifact rather than described.
    // Proxied through here for the same reason the backend list is: the browser must not
    // need CORS configured on four services to see what it is talking to.
    const id = url.searchParams.get("backend") ?? "";
    const spec = BACKENDS[id];
    if (!spec) {
      response.writeHead(404, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ error: `unknown backend ${id}` }));
      return;
    }
    const origin = new URL(spec.origin);
      const partnerId = spec.pair && BACKENDS[spec.pair] ? spec.pair : "";
      const partner = partnerId ? new URL(BACKENDS[partnerId].origin) : null;
      const fetchFrom = (target, path) =>
        new Promise((resolve) => {
          proxyRequest(
            { hostname: target.hostname, port: target.port, path, method: "GET" },
            (upstream) => {
              let raw = "";
              upstream.on("data", (chunk) => (raw += chunk));
              upstream.on("end", () => {
                try {
                  resolve(upstream.statusCode === 200 ? JSON.parse(raw) : null);
                } catch {
                  resolve(null);
                }
              });
            },
          ).on("error", () => resolve(null)).end();
        });
    const fetchJson = (path) =>
      new Promise((resolve) => {
        proxyRequest(
          { hostname: origin.hostname, port: origin.port, path, method: "GET" },
          (upstream) => {
            let raw = "";
            upstream.on("data", (chunk) => (raw += chunk));
            upstream.on("end", () => {
              // A stack without this endpoint is a fact about that stack, not an error:
              // only the Spring pair has beans and auto-configuration to report.
              try {
                resolve(upstream.statusCode === 200 ? JSON.parse(raw) : null);
              } catch {
                resolve(null);
              }
            });
          },
        ).on("error", () => resolve(null)).end();
      });

    Promise.all([
      fetchJson("/__instrumentation/identity"),
      fetchJson("/__instrumentation/beans"),
      fetchJson("/__instrumentation/autoconfig"),
      partner ? fetchFrom(partner, "/__instrumentation/identity") : Promise.resolve(null),
    ]).then(([identity, beans, autoconfig, partnerIdentity]) => {
      response.writeHead(200, { "Content-Type": "application/json" });
      response.end(JSON.stringify({
        backend: id,
        identity,
        beans,
        autoconfig,
        frameworkVersion: frameworkVersion(spec.framework_artifact, identity),
        // The pair, side by side. 36 artifacts against 101 is the argument, and it is
        // only an argument when both numbers are on screen at once.
        pair: partnerId
          ? {
              backend: partnerId,
              identity: partnerIdentity,
              frameworkVersion: frameworkVersion(BACKENDS[partnerId].framework_artifact, partnerIdentity),
            }
          : null,
      }));
    });
    return;
  }

  const target = upstreamFor(url.pathname);
  if (target) {
    const upstream = proxyRequest(
      {
        hostname: target.origin.hostname,
        port: target.origin.port,
        path: target.path + url.search,
        method: request.method,
        headers: { ...request.headers, host: target.origin.host },
      },
      (upstreamResponse) => {
        response.writeHead(upstreamResponse.statusCode ?? 502, upstreamResponse.headers);
        upstreamResponse.pipe(response);
        // An upstream that dies mid-body leaves the browser waiting on a response that
        // will never end. pipe() forwards data and not failure, so this is stated.
        upstreamResponse.on("error", () => response.destroy());
      },
    );
    upstream.on("error", () => {
      // Only before the headers go out. After that the status line is already written and
      // writeHead throws, which takes the process down rather than the request.
      if (!response.headersSent) {
        response.writeHead(502, { "Content-Type": "application/json" });
        response.end(JSON.stringify({ error: "backend unreachable" }));
      } else {
        response.destroy();
      }
    });
    // When the client goes away, let go of the backend.
    //
    // /events is held open forever by design, so without this every closed tab, every
    // navigation and every re-subscribe left a live upstream connection behind. They do
    // not time out (the server has nothing to time out, it is streaming), so they
    // accumulate for as long as the demo runs.
    response.on("close", () => {
      if (!upstream.destroyed) {
        upstream.destroy();
      }
    });
    request.pipe(upstream);
    return;
  }

  // Single-page app: anything that is not a file falls back to the entry document.
  const requested = normalize(join(ROOT, decodeURIComponent(url.pathname)));
  const path = requested.startsWith(ROOT) && existsSync(requested) && statSync(requested).isFile()
    ? requested
    : join(ROOT, "index.html");

  response.writeHead(200, { "Content-Type": TYPES[extname(path)] ?? "application/octet-stream" });
  createReadStream(path).pipe(response);
}).listen(PORT, "0.0.0.0");
