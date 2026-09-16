package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.config.StartupReport;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** Executable proof that one starter on the build line resolves a coherent set of jars
 *  onto the runtime classpath, read back from what actually resolved. */
@Tag("starter-dependencies")
@SpringBootTest
class StarterDependenciesTest {

    @Autowired
    StartupReport report;

    @Test
    void oneBuildLineBringsACoherentSetAndItsAutoConfiguration() {
        var starters = report.starters();
        assertFalse(starters.isEmpty(), "starters resolved onto the runtime classpath");
        assertTrue(starters.stream().anyMatch(s -> s.contains("starter-web")),
                "the web starter is what put a server and a converter here");
    }
}
