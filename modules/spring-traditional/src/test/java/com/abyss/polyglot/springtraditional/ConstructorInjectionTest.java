package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springtraditional.web.WorkloadController;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

/** Executable proof that the dependency is visible in the constructor signature, so the
 *  object cannot exist half-wired and no @Autowired is needed. */
@Tag("constructor-injection")
class ConstructorInjectionTest {

    @Test
    void theObjectCannotExistHalfWired() {
        var service = new WorkItemService(
                new WorkItemRepository(new JdbcTemplate(new DriverManagerDataSource())));

        var controller = new WorkloadController(service);

        assertNotNull(controller);
        assertEquals(1, WorkloadController.class.getDeclaredConstructors().length,
                "a single constructor needs no @Autowired — the container infers it");
        assertEquals(WorkItemService.class,
                WorkloadController.class.getDeclaredConstructors()[0].getParameterTypes()[0],
                "the dependency is visible in the signature, not hidden in a field");
    }
}
