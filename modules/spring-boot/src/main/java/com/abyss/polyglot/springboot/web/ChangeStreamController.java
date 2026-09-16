package com.abyss.polyglot.springboot.web;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * B4 with the framework's emitter.
 *
 * The paired traditional module writes this against the servlet API: startAsync by hand, a
 * timeout to set, a completion listener and an error listener to register, a writer to
 * hold. Here the return type is the mechanism. Spring sees an SseEmitter, detaches the
 * request itself, and hands back an object whose whole surface is send, complete, and the
 * callbacks for when either happens.
 *
 * The timeout still has to be chosen — the default would end the stream — which is the
 * honest limit of the abstraction: it removes the plumbing, not the decision.
 */
@RestController
public class ChangeStreamController {

    private static final List<SseEmitter> SUBSCRIBERS = new CopyOnWriteArrayList<>();

    /**
     * Return an emitter and the framework does the rest.
     *
     * No startAsync, no response configuration, no writer: returning this type is what
     * tells Spring to detach the request and stream. Registering the removal callbacks is
     * the one piece of lifecycle left, and it is a callback rather than a listener
     * interface with four methods, three of which the traditional side has to implement to
     * ignore.
     *
     * Long.MAX_VALUE because a change stream has no natural end; the default timeout would
     * close it mid-demo and look like a client bug.
     */
    @GetMapping(path = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
        SUBSCRIBERS.add(emitter);
        emitter.onCompletion(() -> SUBSCRIBERS.remove(emitter));
        emitter.onTimeout(() -> SUBSCRIBERS.remove(emitter));
        emitter.onError(error -> SUBSCRIBERS.remove(emitter));
        try {
            emitter.send(SseEmitter.event().comment("open"));
        } catch (IOException gone) {
            SUBSCRIBERS.remove(emitter);
        }
        return emitter;
    }

    /** Announce a change to every subscriber. A dead one is completed and dropped. */
    public static void emit(String kind, String id) {
        for (SseEmitter emitter : SUBSCRIBERS) {
            try {
                emitter.send(SseEmitter.event()
                        .name("change")
                        .data(Map.of("kind", kind, "id", id)));
            } catch (Exception gone) {
                // Deliberately broad. A dead subscriber surfaces as an IOException, an
                // IllegalStateException from the container, or an
                // AsyncRequestNotUsableException depending on how far the response got —
                // and an uncaught one here fails the create that triggered the
                // notification. A stream nobody is reading must never break the write it
                // was reporting.
                SUBSCRIBERS.remove(emitter);
                try {
                    emitter.complete();
                } catch (Exception alreadyDone) {
                    // The container finished it between the send failing and this call.
                }
            }
        }
    }
}
