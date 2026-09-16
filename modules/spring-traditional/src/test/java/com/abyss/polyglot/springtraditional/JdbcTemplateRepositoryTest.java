package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

/**
 * Executable proof that the SQL is visible in the repository, that the RowMapper says how
 * a row becomes an object, and that JdbcTemplate translates driver exceptions.
 *
 * Runs against the real database, in the running container, which is where the suite runs
 * it too. The SQL is the thing under test, so a stub datasource would prove nothing.
 */
@Tag("jdbc-template-repository")
class JdbcTemplateRepositoryTest {

    private static JdbcTemplate template() {
        var source = new DriverManagerDataSource();
        source.setDriverClassName("org.postgresql.Driver");
        source.setUrl(System.getenv("DB_URL"));
        source.setUsername(System.getenv("DB_USER"));
        source.setPassword(System.getenv("DB_PASSWORD"));
        return new JdbcTemplate(source);
    }

    @Test
    void theSqlIsVisibleAndTheRowMapperSaysHowARowBecomesAnObject() {
        var repository = new WorkItemRepository(template());
        String id = "JT-" + System.nanoTime();
        Instant now = Instant.now();
        repository.insert(new WorkItem(id, "jdbc probe", Status.OPEN, 4, "suite",
                now, now, List.of("probe"), null));

        List<WorkItem> all = repository.findAll();

        assertFalse(all.isEmpty(), "the query returned rows");
        var found = all.stream().filter(item -> item.id().equals(id)).findFirst();
        assertTrue(found.isPresent(), "the inserted row came back through the RowMapper");
        assertEquals(Status.OPEN, found.get().status(), "the mapper converted the enum column");
        assertEquals(List.of("probe"), found.get().tags(), "and split the delimited column");

        List<Integer> priorities = all.stream().map(WorkItem::priority).toList();
        assertEquals(priorities.stream().sorted(java.util.Comparator.reverseOrder()).toList(),
                priorities, "the ORDER BY in the SQL is the ordering that came back");

        // Archive is a soft delete; nothing here removes the row.
        repository.archive(id, Instant.now());
    }

    @Test
    void theTemplateTranslatesTheDriversExceptionIntoSpringsHierarchy() {
        // The rows-and-order assertions above pass just as well against raw JDBC written
        // by hand — identical results either way. What JdbcTemplate does that the JDBC
        // API does not is translate the driver's SQLException into Spring's
        // DataAccessException hierarchy, so callers depend on a portable exception rather
        // than on vendor error codes.
        //
        // Asserted through findAll(), not through a template built here: a probe that
        // queries its own JdbcTemplate never touches the repository at all, so replacing
        // the repository could not change its verdict — which is how the first version of
        // this assertion passed against the very alternative it was written to reject.
        var unreachable = new DriverManagerDataSource();
        unreachable.setDriverClassName("org.postgresql.Driver");
        unreachable.setUrl("jdbc:postgresql://127.0.0.1:1/nothing");
        unreachable.setUsername("nobody");
        unreachable.setPassword("nothing");
        var repository = new WorkItemRepository(new JdbcTemplate(unreachable));

        assertThrows(org.springframework.dao.DataAccessException.class,
                repository::findAll,
                "the template is in the path and translates; raw JDBC in its place surfaces "
                        + "the driver's own exception instead");
    }
}
