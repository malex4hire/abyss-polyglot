package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that one Comparable-bounded method orders strings and ints alike. */
@Tag("generics-bounded")
class GenericsBoundedTest {

    @Test
    void theBoundIsWhatMakesOrderingLegal() {
        assertEquals(List.of("alpha", "beta"), Queries.firstInOrder(List.of("gamma", "beta", "alpha"), 2));
        assertEquals(List.of(1, 2, 3), Queries.firstInOrder(List.of(3, 1, 2), 5),
                "the same method serves any Comparable, checked once at the bound");
        assertEquals(List.of(), Queries.firstInOrder(List.of("a"), 0));
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
