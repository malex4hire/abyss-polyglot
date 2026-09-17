package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.config.StartupReport;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** Executable proof that the application starts a servlet container inside itself: the
 *  reported name is read off the container bean the context actually built. */
@Tag("embedded-server")
@SpringBootTest
class EmbeddedServerTest {

    @Autowired
    StartupReport report;

    @Autowired
    org.springframework.context.ApplicationContext context;

    @Test
    void theApplicationStartsAServerInsideItself() {
        // Asserted against the bean, not against the word. "contains tomcat" was true of
        // a hardcoded string, so the test could not tell a reading from a claim, and a
        // claim stays right until somebody swaps the container, which is when you need it.
        var factory = context.getBean(
                org.springframework.boot.web.server.servlet.ServletWebServerFactory.class);

        assertEquals(factory.getClass().getSimpleName(), report.embeddedServer(),
                "the name is read off the container bean the application actually built");
    }
}
