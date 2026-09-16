package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that the query sorts on two fields and collects an immutable list. */
@Tag("streams-collectors")
class StreamsCollectorsTest {

    @Test
    void multiFieldSortIsTotalAndTheResultIsUnmodifiable() {
        List<WorkItem> source = List.of(
                item("WI-1", Status.OPEN, 5, "avery"),
                item("WI-2", Status.OPEN, 9, "briar"),
                item("WI-3", Status.DONE, 9, "casey"));

        List<WorkItem> result = Queries.query(source, candidate -> candidate.status() == Status.OPEN);

        assertEquals(List.of("WI-2", "WI-1"), result.stream().map(WorkItem::id).toList(),
                "priority descends, then title ascends");
        assertThrows(UnsupportedOperationException.class, () -> result.add(source.get(0)));
        // Both a stream collected via Collectors.toUnmodifiableList() and a mutable list
        // wrapped in Collections.unmodifiableList() reject a mutation, so that assertion
        // alone cannot tell them apart — the manual wrap is a view over the original list,
        // the collector produces a real, independent copy, and the JDK gives each a
        // different concrete class for exactly that reason.
        assertTrue(result.getClass().getName().startsWith("java.util.ImmutableCollections$"),
                "expected a real ImmutableCollections instance from the collector, got: "
                        + result.getClass().getName());
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
