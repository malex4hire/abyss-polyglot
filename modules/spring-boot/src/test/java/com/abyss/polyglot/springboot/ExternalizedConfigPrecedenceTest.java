package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.config.StartupReport;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** Executable proof that property sources are consulted in a fixed order, and that
 *  environment variables override the packaged application.properties. */
@Tag("externalized-config-precedence")
@SpringBootTest
class ExternalizedConfigPrecedenceTest {

    @Autowired
    StartupReport report;

    @Test
    void theOrderIsTheContractAndFirstMatchWins() {
        var order = report.propertySourceOrder();
        assertFalse(order.isEmpty());
        int env = order.indexOf("systemEnvironment");
        int file = order.indexOf("Config resource 'class path resource [application.properties]' via location 'optional:classpath:/'");
        assertTrue(env >= 0, "environment variables are a source");
        // Was `if (file >= 0) { assertTrue(...) }` — a test that can pass having asserted
        // nothing about precedence at all, if a Spring upgrade ever reshapes this
        // property source's name. Asserting the lookup itself makes that failure loud
        // instead of silent: the ordering claim below only means something once this line
        // has already proven the source it is ordering against actually exists.
        assertTrue(file >= 0, "the packaged application.properties must be a resolvable "
                + "property source, or the precedence claim below has nothing to order against: " + order);
        assertTrue(env < file, "environment overrides the packaged file");
    }
}
