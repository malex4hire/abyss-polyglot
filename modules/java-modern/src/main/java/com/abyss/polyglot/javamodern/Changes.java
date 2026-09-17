package com.abyss.polyglot.javamodern;

import com.sun.net.httpserver.HttpExchange;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * B4: the change stream, on the JDK HTTP server and nothing else.
 *
 * No language lesson is claimed here. Server-sent events on this stack are HTTP plumbing
 * (write a header, keep the socket open, flush a line), and `io` belongs to the framework
 * modules, so claiming a language fundamental for it would blur the split this module's
 * side of the demo depends on. The stack serves the endpoint for contract parity and says
 * nothing more.
 *
 * Each subscriber is a held response body. A virtual thread per request is what makes that
 * affordable: the server's executor is newVirtualThreadPerTaskExecutor, so a parked stream
 * costs a heap object rather than an OS thread, and holding a hundred of them is
 * unremarkable.
 */
final class Changes {

    private static final List<OutputStream> SUBSCRIBERS = new CopyOnWriteArrayList<>();

    private Changes() {
    }

    /** Hold the connection open and register it. The handler never returns until it drops. */
    static void subscribe(HttpExchange exchange) throws IOException {
        exchange.getResponseHeaders().add("Content-Type", "text/event-stream");
        exchange.getResponseHeaders().add("Cache-Control", "no-cache");
        exchange.getResponseHeaders().add("Connection", "keep-alive");
        exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
        exchange.sendResponseHeaders(200, 0);

        OutputStream body = exchange.getResponseBody();
        SUBSCRIBERS.add(body);
        try {
            // A comment line on connect, so a client knows the stream is live before the
            // first real change rather than after it.
            body.write(": open\n\n".getBytes(StandardCharsets.UTF_8));
            body.flush();
            while (!Thread.currentThread().isInterrupted()) {
                Thread.sleep(15_000);
                body.write(": keep-alive\n\n".getBytes(StandardCharsets.UTF_8));
                body.flush();
            }
        } catch (IOException | InterruptedException closed) {
            Thread.currentThread().interrupt();
        } finally {
            SUBSCRIBERS.remove(body);
            exchange.close();
        }
    }

    /** Announce a change. A dead subscriber is dropped rather than retried. */
    static void emit(String kind, String id) {
        String frame = "event: change\ndata: {\"kind\":\"%s\",\"id\":\"%s\"}\n\n"
                .formatted(kind, id);
        byte[] bytes = frame.getBytes(StandardCharsets.UTF_8);
        for (OutputStream subscriber : SUBSCRIBERS) {
            try {
                subscriber.write(bytes);
                subscriber.flush();
            } catch (IOException gone) {
                SUBSCRIBERS.remove(subscriber);
            }
        }
    }
}
