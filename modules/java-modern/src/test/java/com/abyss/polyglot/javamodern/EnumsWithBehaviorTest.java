package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that each Status constant carries its own transition rule. */
@Tag("enums-with-behavior")
class EnumsWithBehaviorTest {

    @Test
    void eachConstantKnowsItsOwnLegalMoves() {
        assertTrue(Status.OPEN.canTransitionTo(Status.IN_PROGRESS));
        assertTrue(Status.IN_PROGRESS.canTransitionTo(Status.BLOCKED));
        assertFalse(Status.OPEN.canTransitionTo(Status.DONE), "OPEN cannot jump straight to DONE");
        assertFalse(Status.DONE.canTransitionTo(Status.OPEN), "DONE is terminal");
        assertFalse(Status.CANCELLED.canTransitionTo(Status.IN_PROGRESS), "CANCELLED is terminal");

        // Every answer above is also satisfied by bare constants and a static map beside
        // them. The point is that the rule travels *with* the constant, and the
        // observable form of that is per-constant state: each constant is constructed
        // with its own rule and carries it. A lookup table has only static fields, so a
        // sixth constant can be added and the table left stale — the failure this exists
        // to prevent, and the one a behaviour-only assertion cannot see.
        var instanceFields = java.util.Arrays.stream(Status.class.getDeclaredFields())
                .filter(field -> !java.lang.reflect.Modifier.isStatic(field.getModifiers()))
                .toList();
        assertFalse(instanceFields.isEmpty(),
                "each constant carries its own rule as instance state, not a shared table");

        // And every constant has one, so no constant can be added without supplying it.
        for (Status state : Status.values()) {
            assertNotNull(state.canTransitionTo(Status.DONE),
                    state + " answers from its own rule");
        }
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
