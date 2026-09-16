package com.abyss.polyglot.springtraditional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.abyss.polyglot.springtraditional.web.InstrumentationController;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.context.support.GenericApplicationContext;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

/**
 * Executable proof that standaloneSetup routes a real request to a single controller with
 * no servlet container and no application context behind it.
 *
 * It drives the one controller in this module that no other test is written against.
 * Every other controller is the subject of its own test, and standing one of those up
 * here would make a break in it redden this test as well — collateral damage, not a
 * signal.
 */
@Tag("mockmvc-standalone")
class MockMvcStandaloneTest {

    /**
     * The MVC stack without a container and without a context. standaloneSetup builds
     * just enough dispatcher to route to one controller, so the test exercises real
     * request mapping, argument binding and message conversion while starting nothing —
     * milliseconds rather than the seconds a full context costs.
     *
     * What it does not test is the wiring. Nothing here proves the controller would be
     * found by a component scan, or that its dependencies would resolve, because this
     * test constructed it by hand. That is the trade being made, and it is the reason the
     * Boot module's slice test exists alongside it.
     */
    @Test
    void theMvcStackWithoutAContainer() throws Exception {
        var controller = new InstrumentationController(new GenericApplicationContext());

        MockMvcBuilders.standaloneSetup(controller)
                .build()
                .perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
    }
}
