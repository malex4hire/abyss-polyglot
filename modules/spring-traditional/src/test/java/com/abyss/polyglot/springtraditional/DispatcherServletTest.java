package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.web.context.support.GenericWebApplicationContext;

/** Executable proof that the front controller is registered and mapped by hand, with
 *  its name, its url pattern and its startup order all stated rather than defaulted. */
@Tag("dispatcher-servlet")
class DispatcherServletTest {

    @Test
    void theFrontControllerIsMappedByHand() {
        var servletContext = new RecordingServletContext();
        // A bare context, not the one rootContext() builds: that is a separate lesson.
        var root = new GenericWebApplicationContext();

        new AppInitializer().registerDispatcher(servletContext, root);

        assertTrue(servletContext.servlets.containsKey("dispatcher"),
                "registered under a name we chose");
        assertTrue(servletContext.mappings.get("dispatcher").contains("/"),
                "and mapped at the root, explicitly");
        assertEquals(1, servletContext.startupOrder.get("dispatcher"),
                "startup order is a stated decision, not a default");
        root.close();
    }
}
