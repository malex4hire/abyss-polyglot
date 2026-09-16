package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that the priority sum is a primitive accumulator, never null. */
@Tag("primitives-vs-references")
class PrimitivesVsReferencesTest {

    @Test
    void aPrimitiveAccumulatorHasValueAndNoIdentity() {
        List<WorkItem> items = List.of(
                item("WI-1", Status.OPEN, 5, "avery"),
                item("WI-2", Status.OPEN, 8, "avery"));

        assertEquals(13, Workload.totalPriority(items));
        assertEquals(0, Workload.totalPriority(List.of()), "an empty sum is zero, never null");
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
