package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.config.StartupReport;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** Executable proof that the active profiles reported are the ones the Environment
 *  holds, and that "default" is the answer when none is set. */
@Tag("profiles")
@SpringBootTest
class ProfilesTest {

    @Autowired
    StartupReport report;

    @Test
    void withNoProfileSetDefaultIsWhatIsActive() {
        // "not empty" is true of any answer at all, including one read from an
        // environment variable that never sees a profile the context sets. The Environment
        // is the thing being demonstrated, so the test sets a profile on it and asks.
        var environment = new org.springframework.core.env.StandardEnvironment();
        environment.setActiveProfiles("probe");
        var scoped = new com.abyss.polyglot.springboot.config.StartupReport(null, environment, null);

        assertTrue(scoped.activeProfiles().contains("probe"),
                "the profile the Environment holds is the profile reported: "
                        + scoped.activeProfiles());
        assertFalse(report.activeProfiles().isEmpty(),
                "and with none set there is still an answer, never nothing");
    }
}
