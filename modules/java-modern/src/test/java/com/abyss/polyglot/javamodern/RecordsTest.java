package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that WorkItem derives new values and compares componentwise. */
@Tag("records")
class RecordsTest {

    @Test
    void derivesANewValueInsteadOfMutating() {
        WorkItem original = item("WI-1", Status.OPEN, 5, "avery", "backend");
        Instant later = Instant.parse("2026-02-01T00:00:00Z");

        WorkItem moved = original.withStatus(Status.IN_PROGRESS, later);

        assertEquals(Status.IN_PROGRESS, moved.status(), "derived value carries the new status");
        assertEquals(Status.OPEN, original.status(), "the original is untouched, because records are immutable");
        assertEquals(original.id(), moved.id());
        assertEquals(later, moved.updatedAt());
        assertNotEquals(original, moved, "equals is componentwise, so a changed component changes equality");

        // Everything above is also satisfied by a hand-written final class with the
        // same accessors: assertNotEquals holds trivially under identity equality, which
        // is what a class without equals has. What the compiler supplies, and a hand-
        // written class silently does not, is only visible against a separately
        // constructed instance carrying identical components.
        WorkItem twin = item("WI-1", Status.OPEN, 5, "avery", "backend");
        assertNotSame(original, twin, "a distinct instance");
        assertEquals(original, twin, "equals is componentwise, not identity");
        assertEquals(original.hashCode(), twin.hashCode(), "and hashCode agrees with it");
        assertTrue(original.toString().contains("WI-1"),
                "toString names the components rather than an object address");
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
