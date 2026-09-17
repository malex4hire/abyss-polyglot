package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.config.StartupReport;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** Executable proof that startup applied dozens of auto-configurations this module never
 *  declared, counted from Boot's live condition-evaluation report. */
@Tag("auto-configuration")
@SpringBootTest
class AutoConfigurationTest {

    @Autowired
    StartupReport report;

    @Test
    void conventionIsAReadableReportNotVagueness() {
        // "> 0" was the original bar, and a stub returning a constant cleared it. A real
        // Boot application matches dozens of conditions at startup (web, jackson, jpa,
        // datasource, transaction, actuator), so the bar that separates a report from a
        // number somebody wrote is an order of magnitude, not one.
        int applied = report.autoConfigurationsApplied();

        assertTrue(applied > 10,
                "a report of what convention contributed, not a number somebody wrote: "
                        + applied);
    }
}
