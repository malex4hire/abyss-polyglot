package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.domain.WorkItemRepository;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;

/**
 * Executable proof that @SpringBootTest boots the real context, wiring included, rather
 * than a trimmed slice of it.
 *
 * Unlike the rest of this module, a test harness is not reachable from a served request
 * path; it exists only to be run.
 */
@Tag("spring-boot-test")
@SpringBootTest
class SpringBootTestSliceTest {

    @Autowired
    ApplicationContext context;

    @Autowired
    WorkItemRepository repository;

    /**
     * The whole application, started for a test. @SpringBootTest boots the real context
     * (every auto-configuration, the real datasource, the real repository proxy), so what
     * is exercised is the wiring as well as the code.
     *
     * That is the trade against the traditional module's standalone MockMvc setup: this
     * catches a broken bean graph, and costs seconds per context rather than milliseconds.
     * Spring caches the context across test classes precisely because the cost is real.
     */
    @Test
    void theRealContextIncludingItsWiring() {
        assertNotNull(context.getBean(WorkItemRepository.class),
                "a proxy Spring Data built at startup, not a class in this module");
        assertSame(repository, context.getBean(WorkItemRepository.class),
                "the same singleton the application serves requests with");
        assertTrue(context.getBeanDefinitionCount() > 100,
                "the real context, not a trimmed one");
    }
}
