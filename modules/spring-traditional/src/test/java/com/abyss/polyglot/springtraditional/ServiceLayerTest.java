package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

/** Executable proof that the transition rule lives in the service, not in the
 *  controller or the repository: an illegal move is refused and nothing is written. */

@Tag("service-layer")
class ServiceLayerTest {

    static class RecordingRepository extends WorkItemRepository {
        WorkItem current;
        int updates;

        RecordingRepository(WorkItem seed) {
            super(new JdbcTemplate(new DriverManagerDataSource()));
            this.current = seed;
        }

        @Override public Optional<WorkItem> findById(String id) { return Optional.of(current); }

        // B5: the precondition travels with the write, and the write reports rows
        // affected. A stub that ignored `expected` would let the service pass a
        // compare-and-set it never actually performs.
        @Override public int updateStatus(String id, Status expected, Status status, Instant at) {
            if (current.status() != expected) {
                return 0;
            }
            updates++;
            current = new WorkItem(current.id(), current.title(), status, current.priority(),
                    current.assignee(), current.createdAt(), at, current.tags(), current.archivedAt());
            return 1;
        }
    }

    @Test
    void theDomainRuleLivesHereNotInTheControllerOrTheRepository() {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        var repo = new RecordingRepository(new WorkItem("WI-1", "one", Status.OPEN, 5, "avery",
                t, t, List.of(), null));
        var service = new WorkItemService(repo);

        assertTrue(service.transition("WI-1", Status.IN_PROGRESS, t).isPresent(), "legal move applied");
        assertEquals(1, repo.updates);

        repo.current = new WorkItem("WI-2", "two", Status.DONE, 5, "avery", t, t, List.of(), null);
        assertTrue(service.transition("WI-2", Status.OPEN, t).isEmpty(), "illegal move refused");
        assertEquals(1, repo.updates, "and nothing was written");
    }
}
