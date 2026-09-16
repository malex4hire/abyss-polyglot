package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import jakarta.servlet.ServletContext;
import jakarta.servlet.ServletRegistration;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.web.context.support.GenericWebApplicationContext;

/**
 * Executable proof that onStartup is the interface hook Spring calls, and that the order
 * of the three steps it composes is stated here rather than defaulted.
 *
 * Each of those three steps has its own test, so this one stubs them and asserts only the
 * composition. Calling the real ones would make a break in any one of them redden this
 * test too, which is collateral damage rather than a signal.
 */
@Tag("web-application-initializer")
class WebApplicationInitializerTest {

    @Test
    void startupIsAnInterfaceHookThatOrchestratesNamedSteps() throws Exception {
        List<String> calls = new ArrayList<>();

        var initializer = new AppInitializer() {
            @Override GenericWebApplicationContext rootContext() {
                calls.add("rootContext");
                return new GenericWebApplicationContext();
            }

            @Override int scanPackages(GenericWebApplicationContext context) {
                calls.add("scanPackages");
                return 0;
            }

            @Override ServletRegistration.Dynamic registerDispatcher(
                    ServletContext servletContext, GenericWebApplicationContext root) {
                calls.add("registerDispatcher");
                return null;
            }
        };

        initializer.onStartup(new RecordingServletContext());

        assertEquals(List.of("rootContext", "scanPackages", "registerDispatcher"), calls,
                "the bootstrap order is ours to state, and this is the order");
    }
}
