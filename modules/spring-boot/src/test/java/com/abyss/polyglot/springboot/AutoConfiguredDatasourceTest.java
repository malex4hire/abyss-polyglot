package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.config.StartupReport;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** Executable proof that nothing in this module constructs the DataSource: Boot picked a
 *  pooled implementation off the classpath and wired it. */
@Tag("auto-configured-datasource")
@SpringBootTest
class AutoConfiguredDatasourceTest {

    @Autowired
    StartupReport report;

    @Test
    void nobodyInThisModuleConstructedIt() {
        var detail = report.datasourceDetail();
        assertEquals("false", detail.get("declaredInThisModule"));
        assertTrue(detail.get("implementation").toLowerCase().contains("hikari"),
                "Boot chose a pooled implementation from what was on the classpath");
    }
}
