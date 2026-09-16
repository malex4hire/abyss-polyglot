package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.request;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.abyss.polyglot.springboot.web.ChangeStreamController;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

/**
 * Executable proof that returning an SseEmitter is itself what detaches the request and
 * turns the response into a stream.
 *
 * The return type is the mechanism, so the assertion is on what returning that type
 * causes: the request is detached from the container's thread and the
 * response is a stream. A handler returning a body — however correct that body is — leaves
 * the request synchronous and answers with a different content type, so this fails against
 * any implementation that is not streaming.
 *
 * Note what is deliberately absent. There is no startAsync to observe, no timeout to read
 * back, no listener registration to verify. That absence is the whole point, and it is
 * the paired traditional test that has all four.
 */
@Tag("sse-emitter")
class SseEmitterTest {

    private final MockMvc mvc =
            MockMvcBuilders.standaloneSetup(new ChangeStreamController()).build();

    @Test
    void returningAnEmitterIsWhatDetachesTheRequest() throws Exception {
        MvcResult result = mvc.perform(get("/events"))
                .andExpect(status().isOk())
                // The framework detached because of the return type. Nothing in the handler
                // asked it to, which is the whole difference from the traditional side.
                .andExpect(request().asyncStarted())
                .andReturn();
        assertNotNull(result.getRequest().getAsyncContext(),
                "the request outlived the handler, which is what the return type caused");

        // Asserted by calling the handler rather than through MvcResult.getAsyncResult(),
        // which blocks until the async result is set. This emitter's timeout is
        // Long.MAX_VALUE by design — a change stream has no natural end — so that call
        // waits forever. The first version of this test hung the suite for fifteen minutes.
        assertInstanceOf(
                org.springframework.web.servlet.mvc.method.annotation.SseEmitter.class,
                new ChangeStreamController().stream(),
                "the handler's return value is the emitter itself, not a body to convert");
    }

    @Test
    void theResponseIsAnEventStreamAndCarriesNamedChangeEvents() throws Exception {
        MvcResult result = mvc.perform(get("/events")).andReturn();

        assertTrue(result.getResponse().getContentType().startsWith("text/event-stream"),
                "a stream, not a document: got " + result.getResponse().getContentType());

        ChangeStreamController.emit("created", "WI-STREAM");

        String written = result.getResponse().getContentAsString();
        assertTrue(written.contains("event:change"),
                "the frame carries the event name the browser listens for: " + written);
        assertTrue(written.contains("WI-STREAM"),
                "the change reaches the open stream: " + written);
    }
}
