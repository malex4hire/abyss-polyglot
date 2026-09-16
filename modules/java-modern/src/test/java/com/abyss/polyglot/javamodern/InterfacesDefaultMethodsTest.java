package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that a default method gives Auditable behaviour with no base class. */
@Tag("interfaces-default-methods")
class InterfacesDefaultMethodsTest {

    @Test
    void behaviourOnTheInterfaceCostsNoPlaceInTheHierarchy() {
        Instant created = Instant.parse("2026-01-01T00:00:00Z");
        Instant touched = Instant.parse("2026-01-01T00:01:00Z");
        Auditable subject = new Auditable() {
            @Override public Instant createdAt() { return created; }
            @Override public Instant updatedAt() { return touched; }
        };

        assertEquals(60, subject.secondsSinceTouched(Instant.parse("2026-01-01T00:02:00Z")));

        Auditable neverTouched = new Auditable() {
            @Override public Instant createdAt() { return created; }
            @Override public Instant updatedAt() { return null; }
        };
        assertEquals(120, neverTouched.secondsSinceTouched(Instant.parse("2026-01-01T00:02:00Z")),
                "falls back to createdAt");
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
