package com.abyss.polyglot.springtraditional.web;

import jakarta.servlet.AsyncContext;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * B4 on the servlet API, the way it was done before a framework abstraction existed.
 *
 * The paired stack writes this with SseEmitter and returns it. Here the request is detached
 * from the request-handling thread by hand, the response is configured by hand, the writer
 * is held by hand, and the timeout, the completion listener and the error listener are all
 * ours to set. That is the era contrast on a problem the servlet API was not designed for:
 * a long-lived response predates the API, so what Boot supplies as a return type is here a
 * lifecycle to manage.
 */
@Controller
public class ChangeStreamController {

    private static final List<AsyncContext> SUBSCRIBERS = new CopyOnWriteArrayList<>();

    /**
     * Detach the request from the container's thread and keep the response open.
     *
     * startAsync is the whole mechanism. Without it the container closes the response when
     * this method returns and every client sees an immediately-finished stream. With it,
     * the request survives the handler and the writer stays usable — which also means
     * nothing will ever close it for us, so the listeners below are not optional.
     *
     * Timeout zero means no timeout. The container's default would otherwise end the
     * stream after thirty seconds, which looks exactly like a client-side bug.
     */
    @GetMapping("/events")
    public void stream(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
        response.setContentType("text/event-stream");
        response.setCharacterEncoding("UTF-8");
        response.setHeader("Cache-Control", "no-cache");
        response.setHeader("Connection", "keep-alive");
        response.setHeader("Access-Control-Allow-Origin", "*");

        AsyncContext context = request.startAsync();
        context.setTimeout(0);
        SUBSCRIBERS.add(context);
        context.addListener(new jakarta.servlet.AsyncListener() {
            @Override public void onComplete(jakarta.servlet.AsyncEvent event) {
                SUBSCRIBERS.remove(context);
            }
            @Override public void onTimeout(jakarta.servlet.AsyncEvent event) {
                SUBSCRIBERS.remove(context);
                context.complete();
            }
            @Override public void onError(jakarta.servlet.AsyncEvent event) {
                SUBSCRIBERS.remove(context);
                context.complete();
            }
            @Override public void onStartAsync(jakarta.servlet.AsyncEvent event) {
            }
        });

        PrintWriter writer = response.getWriter();
        writer.write(": open\n\n");
        writer.flush();
    }

    /** Announce a change to every held response. A dead one is completed and dropped. */
    public static void emit(String kind, String id) {
        String frame = "event: change\ndata: {\"kind\":\"%s\",\"id\":\"%s\"}\n\n".formatted(kind, id);
        for (AsyncContext context : SUBSCRIBERS) {
            try {
                PrintWriter writer = context.getResponse().getWriter();
                writer.write(frame);
                writer.flush();
            } catch (Exception gone) {
                // Broad for the same reason as the paired module: a dead subscriber must
                // never fail the mutation whose notification it is.
                SUBSCRIBERS.remove(context);
                try {
                    context.complete();
                } catch (IllegalStateException alreadyDone) {
                    // Completed by the container between the write failing and this call.
                }
            }
        }
    }
}
