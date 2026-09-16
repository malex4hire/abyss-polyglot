package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that the repository keeps insertion order and copies defensively. */
@Tag("collections-framework")
class CollectionsFrameworkTest {

    @Test
    void iterationOrderIsPartOfTheContractAndTheCopyIsDefensive() {
        Repository repo = new Repository();
        repo.put(item("WI-3", Status.OPEN, 1, "casey"));
        repo.put(item("WI-1", Status.OPEN, 9, "avery"));
        Instant t = Instant.parse("2026-01-05T00:00:00Z");
        repo.put(item("WI-2", Status.OPEN, 4, "briar").archived(t));

        List<WorkItem> all = repo.all();

        assertEquals(List.of("WI-3", "WI-1"), all.stream().map(WorkItem::id).toList(),
                "insertion order preserved, archived rows excluded");
        assertThrows(UnsupportedOperationException.class,
                () -> all.add(item("WI-9", Status.OPEN, 1, "x")),
                "the returned list is unmodifiable");
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
