package com.abyss.polyglot.javamodern;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.Executors;

/**
 * The HTTP layer: com.sun.net.httpserver, hand-rolled routing, no framework.
 *
 * The routing is written out rather than annotated, which is what puts the sealed types
 * and the pattern-matching switch on the real request path instead of in a demo. Every
 * language feature this module shows off is reached from one of the handlers below.
 */
public final class App {

    private static final Repository REPO = new Repository();
    private static final AuditTrail TRAIL = new AuditTrail();

    public static void main(String[] args) throws IOException {
        Instant now = Instant.now();
        for (WorkItem item : Seed.load(now)) {
            REPO.put(item);
        }

        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        // The whole server runs on virtual threads. One line, and every handler becomes
        // cheap to block in, which is exactly what the workload endpoint relies on.
        server.setExecutor(Executors.newVirtualThreadPerTaskExecutor());

        server.createContext("/health", exchange ->
                text(exchange, 200, Banner.text(System.getProperty("java.version"), REPO.size())));
        server.createContext("/__instrumentation/identity", exchange ->
                json(exchange, 200, Instrumentation.report(server)));
        // B4. Held open per subscriber; the virtual-thread executor above is what makes
        // one parked thread per stream affordable.
        server.createContext("/events", Changes::subscribe);
        server.createContext("/work-items", guarded(App::workItems));
        server.createContext("/workload", guarded(App::workload));

        server.start();
        System.out.println(Banner.text(System.getProperty("java.version"), REPO.size()));
    }

    /**
     * Turn a bad request into a client error instead of a dropped connection.
     *
     * Without this an unparseable enum or a missing field propagates out of the handler,
     * the server closes the socket, and the caller sees a transport failure rather than
     * the 400 the contract promises. Hand-rolled routing means hand-rolled error
     * translation. The framework stacks get this from an exception resolver.
     */
    private static com.sun.net.httpserver.HttpHandler guarded(com.sun.net.httpserver.HttpHandler inner) {
        return exchange -> {
            try {
                inner.handle(exchange);
            } catch (IllegalArgumentException | NullPointerException e) {
                json(exchange, 400, Map.of("error", "bad request",
                        "detail", String.valueOf(e.getMessage())));
            } catch (RuntimeException e) {
                json(exchange, 500, Map.of("error", "internal", "detail", String.valueOf(e.getMessage())));
            }
        };
    }

    /**
     * The methods each shape under /work-items answers to.
     *
     * A route table rather than a chain of prefix guesses, because the chain ended in a
     * single fallthrough that answered 405 to everything it had not matched, and 405 is a
     * claim that the path exists and the method does not. Any unmatched sub-path inherited
     * that claim, so it was never one wrong endpoint. With no framework the routing is
     * ours, which means routing correctness is ours too; this is where it is stated once.
     */
    private static java.util.Set<String> allowedFor(String path) {
        String[] parts = path.split("/", -1);   // "", "work-items", ...
        if (parts.length == 2) {
            return java.util.Set.of("GET", "POST");
        }
        if (parts.length == 3 && !parts[2].isEmpty()) {
            return java.util.Set.of("GET");
        }
        if (parts.length == 4 && !parts[2].isEmpty()
                && (parts[3].equals("archive") || parts[3].equals("transition"))) {
            return java.util.Set.of("POST");
        }
        return java.util.Set.of();              // no such path
    }

    /** B1 query, B5 fetch by id, plus B2 transition and archive on sub-paths. */
    private static void workItems(HttpExchange exchange) throws IOException {
        String path = exchange.getRequestURI().getPath();
        String method = exchange.getRequestMethod();

        java.util.Set<String> allowed = allowedFor(path);
        if (allowed.isEmpty()) {
            json(exchange, 404, Map.of("error", "no such path", "path", path));
            return;
        }
        if (!allowed.contains(method)) {
            // 405 has to say what is allowed; a client told only "not that" learns nothing.
            exchange.getResponseHeaders().add("Allow", String.join(", ", new java.util.TreeSet<>(allowed)));
            json(exchange, 405, Map.of("error", "method not allowed", "path", path,
                    "method", method, "allowed", new java.util.TreeSet<>(allowed)));
            return;
        }

        if (path.equals("/work-items") && method.equals("GET")) {
            Map<String, String> params = query(exchange);
            Status status = params.get("status") == null ? null : Status.valueOf(params.get("status"));
            List<WorkItem> found = Queries.query(REPO.all(), Queries.filterFor(status, params.get("tag")));
            String limit = params.get("limit");
            if (limit != null) {
                List<String> titles = Queries.firstInOrder(found.stream().map(WorkItem::title).toList(),
                        Integer.parseInt(limit));
                json(exchange, 200, Map.of("items", found, "titlesInOrder", titles));
                return;
            }
            json(exchange, 200, Map.of("items", found));
            return;
        }

        if (path.equals("/work-items") && method.equals("POST")) {
            var node = Json.read(new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
            Instant at = Instant.now();
            List<String> tags = new java.util.ArrayList<>();
            if (node.has("tags")) {
                node.get("tags").forEach(tag -> tags.add(tag.asText()));
            }
            // B5. The key is the row's identity, so it is checked before anything is
            // built. Reading a missing field with asText() yields "" and a JSON null
            // yields "null", and both are keys nobody can address, written silently.
            String key = node.hasNonNull("id") ? node.get("id").asText() : "";
            if (key.isBlank()) {
                json(exchange, 400, Map.of("error", "id is required", "field", "id"));
                return;
            }
            WorkItem created = new WorkItem(
                    key, node.get("title").asText(),
                    Status.valueOf(node.get("status").asText()), node.get("priority").asInt(),
                    node.get("assignee").asText(), at, at, tags, null);
            // The outcome comes from the write, not from a lookup before it.
            Optional<WorkItem> existing = REPO.putIfAbsent(created);
            if (existing.isPresent()) {
                // Nothing was written, so nothing is announced and nothing claims 201.
                json(exchange, 200, Map.of("item", existing.get()));
                return;
            }
            Changes.emit("created", created.id());
            json(exchange, 201, Map.of("item", created));
            return;
        }

        if (method.equals("GET") && path.split("/", -1).length == 3) {
            String id = path.substring("/work-items/".length());
            Optional<WorkItem> found = REPO.findById(id);
            if (found.isEmpty()) {
                json(exchange, 404, Map.of("error", "no such work item", "id", id));
                return;
            }
            // Archived items resolve: archive is a soft delete, so the list is the active
            // view and this addresses the record.
            json(exchange, 200, Map.of("item", found.get()));
            return;
        }

        if (method.equals("POST") && path.endsWith("/archive")) {
            String id = path.substring("/work-items/".length(), path.length() - "/archive".length());
            Optional<WorkItem> item = REPO.findById(id);
            if (item.isEmpty()) {
                json(exchange, 404, Map.of("error", "no such work item", "id", id));
                return;
            }
            REPO.put(item.get().archived(Instant.now()));
            Changes.emit("archived", id);
            json(exchange, 200, Map.of("archived", id));
            return;
        }

        if (method.equals("POST") && path.endsWith("/transition")) {
            String id = path.substring("/work-items/".length(), path.length() - "/transition".length());
            Optional<WorkItem> item = REPO.findById(id);
            if (item.isEmpty()) {
                json(exchange, 404, Map.of("error", "no such work item", "id", id));
                return;
            }
            String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            Status next = Status.valueOf(Json.read(body).get("status").asText());
            Instant at = Instant.now();

            // B5. Already there is not an illegal move, it is a move that has happened,
            // which is what a client retrying a dropped response is asking about. Only the
            // self-edge changes; everything the state machine refused, it still refuses.
            if (item.get().status() == next) {
                json(exchange, 200, Map.of("item", item.get(), "audit", TRAIL.entries()));
                return;
            }

            TransitionResult result = Workflow.apply(item.get(), next, at);
            int code = Workflow.statusCodeFor(result);
            if (result instanceof TransitionResult.Applied applied) {
                // Compare and set: the status this decision was made against is the
                // precondition of the write, so a concurrent move is not overwritten.
                Optional<WorkItem> stored =
                        REPO.replaceIfStatusIs(id, item.get().status(), applied.item());
                if (stored.isEmpty()) {
                    // Somebody moved it in between. Re-read and answer with what is true.
                    WorkItem now = REPO.findById(id).orElse(applied.item());
                    json(exchange, 200, Map.of("item", now, "audit", TRAIL.entries()));
                    return;
                }
                Changes.emit("transitioned", id);
                TRAIL.record(id, "transition", applied.item(), at);
                json(exchange, code, Map.of("item", applied.item(), "audit", TRAIL.entries()));
            } else if (result instanceof TransitionResult.Rejected rejected) {
                json(exchange, code, Map.of("rejected", rejected));
            }
            return;
        }

        // Unreachable: allowedFor admits only pairs handled above. Kept as a loud failure
        // rather than a silent fallthrough if a route is added to the table and not here.
        json(exchange, 500, Map.of("error", "route admitted but not handled",
                "path", path, "method", method));
    }

    /** B3 aggregate: the same rollup computed two ways, both on the request path. */
    private static void workload(HttpExchange exchange) throws IOException {
        Map<String, List<WorkItem>> grouped = Workload.groupByAssignee(REPO.all());
        Map<String, Object> doc = new LinkedHashMap<>();
        // byAssignee is the key every backend serves under the shared OpenAPI contract.
        // The two computations beside it are this stack's language lesson, not the shape.
        doc.put("byAssignee", Workload.virtual(grouped));
        doc.put("virtualThreads", Workload.virtual(grouped));
        doc.put("fixedPool", Workload.pooled(grouped));
        doc.put("totalPriority", Workload.totalPriority(REPO.all()));
        json(exchange, 200, doc);
    }

    private static Map<String, String> query(HttpExchange exchange) {
        Map<String, String> params = new LinkedHashMap<>();
        String raw = exchange.getRequestURI().getRawQuery();
        if (raw == null) {
            return params;
        }
        for (String pair : raw.split("&")) {
            int eq = pair.indexOf('=');
            if (eq > 0) {
                params.put(pair.substring(0, eq),
                        java.net.URLDecoder.decode(pair.substring(eq + 1), StandardCharsets.UTF_8));
            }
        }
        return params;
    }

    private static void json(HttpExchange exchange, int code, Object body) throws IOException {
        byte[] out = Json.write(body).getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type", "application/json");
        exchange.sendResponseHeaders(code, out.length);
        try (OutputStream stream = exchange.getResponseBody()) {
            stream.write(out);
        }
    }

    private static void text(HttpExchange exchange, int code, String body) throws IOException {
        byte[] out = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type", "text/plain; charset=utf-8");
        exchange.sendResponseHeaders(code, out.length);
        try (OutputStream stream = exchange.getResponseBody()) {
            stream.write(out);
        }
    }
}
