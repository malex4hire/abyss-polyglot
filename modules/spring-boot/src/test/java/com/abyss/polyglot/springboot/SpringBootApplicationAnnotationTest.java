package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.domain.WorkItemRepository;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Executable proof that one annotation plus one call produces a running context, with
 * component scanning and auto-configuration both already done.
 *
 * An earlier version only read the annotation reflectively. That asserts the annotation
 * is written, not that it does anything: it passed just as happily with the bootstrap
 * stubbed out. This runs the bootstrap and inspects what it produced.
 */
@Tag("spring-boot-application-annotation")
class SpringBootApplicationAnnotationTest {

    @Test
    void oneCallAgainstOneAnnotatedClassProducesARunningContext() {
        // A throwaway context on an ephemeral port, closed on the way out.
        try (var context = Application.start(new String[]{
                "--server.port=0",
                "--spring.main.banner-mode=off",
        })) {
            assertTrue(context.isRunning(), "the bootstrap returned a started context");
            assertNotNull(context.getBean(WorkItemRepository.class),
                    "component scanning found this package, which nothing stated");
            assertNotNull(context.getBean(javax.sql.DataSource.class),
                    "auto-configuration contributed a datasource this module never declared");
            assertNotNull(Application.class.getAnnotation(SpringBootApplication.class),
                    "and all of it hangs off the one annotation");
        }
    }
}
