package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.request;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.abyss.polyglot.springtraditional.web.ChangeStreamController;
import jakarta.servlet.AsyncListener;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockAsyncContext;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

/**
 * Executable proof that startAsync is what keeps the response open after a void handler
 * returns, and that every step Boot's SseEmitter hides is an explicit act here.
 *
 * The Boot module's counterpart asserts that returning a type was enough. Here the
 * assertions are the plumbing itself, because the plumbing is the whole lesson: the
 * handler returns void, so the only thing keeping the response open is the startAsync
 * call, and everything the container would otherwise have done has to be visible.
 *
 * Each assertion names one of those acts — the detach, the timeout that has to be chosen,
 * the listeners that have to be registered because nothing will close this for us. A
 * handler that wrote the same bytes without startAsync passes none of them, and would also
 * be a stream the container closes the moment the method returns.
 */
@Tag("sse-async-context")
class SseAsyncContextTest {

    private final MockMvc mvc =
            MockMvcBuilders.standaloneSetup(new ChangeStreamController()).build();

    @Test
    void startAsyncIsWhatKeepsTheResponseOpenAfterTheHandlerReturns() throws Exception {
        MvcResult result = mvc.perform(get("/events"))
                .andExpect(status().isOk())
                // The handler returns void. Without startAsync there is nothing to dispatch
                // later and the container ends the response here.
                .andExpect(request().asyncStarted())
                .andReturn();

        assertTrue(result.getResponse().getContentType().startsWith("text/event-stream"),
                "the response was configured by hand: " + result.getResponse().getContentType());
        assertEquals("no-cache", result.getResponse().getHeader("Cache-Control"),
                "no framework set this header; the handler did");
    }

    @Test
    void theTimeoutAndTheListenersAreTheHandlersToChoose() throws Exception {
        MvcResult result = mvc.perform(get("/events")).andReturn();
        MockAsyncContext context = (MockAsyncContext) result.getRequest().getAsyncContext();

        assertNotNull(context, "startAsync produced the context the rest of this depends on");
        // Zero means no timeout. The container's default would end the stream, so leaving
        // this alone is a decision and not an omission.
        assertEquals(0, context.getTimeout(),
                "the timeout is chosen here, not inherited");

        java.util.List<AsyncListener> listeners = context.getListeners();
        assertEquals(1, listeners.size(),
                "nothing closes this stream for us, so a listener is registered to clean up");
    }

    @Test
    void theWriterIsHeldOpenRatherThanClosedWithTheHandler() throws Exception {
        MvcResult result = mvc.perform(get("/events")).andReturn();

        // Written through the held writer before the handler returned, and still readable
        // after: the response was not finished when the method was.
        assertTrue(result.getResponse().getContentAsString().startsWith(": open"),
                "the opening comment frame was written by hand and flushed");
        // Committed, because flushing a frame commits it — and still async, because the
        // detach is what keeps it usable afterwards. Committed is not closed, which is the
        // distinction this stream depends on and the reason nothing here asserts otherwise.
        assertTrue(result.getRequest().isAsyncStarted(),
                "the request is still detached after the handler returned");
    }

    /*
     * There is deliberately no assertion here that emit() reaches this response.
     *
     * MockAsyncContext holds whatever response startAsync was given, and the no-argument
     * form gives it none — so context.getResponse() is null under MockMvc, emit()'s writer
     * lookup throws, and the broad catch drops the subscriber without a sound. An assertion
     * on the response content would therefore have been reading an object the operation
     * never touched, and it would have passed or failed for reasons unrelated to async
     * dispatch. Under a real container the same call binds the live response, which is why
     * this is a limit of the mock rather than a defect in the controller.
     *
     * Delivery is proven where it is real: the live-update browser check watches a change
     * made in one frontend appear in the other with no user action, against the running
     * backend. That is the assertion this one would have been pretending to be.
     */
}
