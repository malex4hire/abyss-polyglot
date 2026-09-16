package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.transaction.annotation.Transactional;

/**
 * Executable proof that @Transactional marks a real write path: the annotated method
 * runs, commits, and is public, since a non-public method is never proxied.
 *
 * An earlier version only read the annotation reflectively. That asserts the annotation
 * is written, not that the method it marks does anything — gut the method body and such a
 * test stays green, which makes it no proof at all. This runs the annotated method and
 * checks what it wrote.
 */
@Tag("transactional-annotation")
class TransactionalAnnotationTest {

    private static JdbcTemplate template() {
        var source = new DriverManagerDataSource();
        source.setDriverClassName("org.postgresql.Driver");
        source.setUrl(System.getenv("DB_URL"));
        source.setUsername(System.getenv("DB_USER"));
        source.setPassword(System.getenv("DB_PASSWORD"));
        return new JdbcTemplate(source);
    }

    @Test
    void theUnitOfWorkRunsAndIsMarkedAtTheBoundaryTheProxyCrosses() throws Exception {
        var repository = new WorkItemRepository(template());
        var service = new WorkItemService(repository);
        String id = "TX-" + System.nanoTime();
        Instant now = Instant.now();
        repository.insert(new WorkItem(id, "transaction probe", Status.OPEN, 4, "suite",
                now, now, List.of("probe"), null));

        service.archive(id, Instant.now());

        var stored = repository.findById(id).orElseThrow();
        assertTrue(stored.isArchived(), "the annotated method ran and committed its write");
        assertNotNull(stored.archivedAt(), "archive is a soft delete: the row stays, marked");

        var method = WorkItemService.class.getDeclaredMethod(
                "archive", String.class, Instant.class);
        assertNotNull(method.getAnnotation(Transactional.class),
                "and the write path is the transaction boundary");
        assertTrue(java.lang.reflect.Modifier.isPublic(method.getModifiers()),
                "a non-public method is never proxied, so the annotation would be silently inert");
    }
}
