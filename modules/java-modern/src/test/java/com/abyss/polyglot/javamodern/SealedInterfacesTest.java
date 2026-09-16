package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that TransitionResult is a closed hierarchy the JVM can confirm. */
@Tag("sealed-interfaces")
class SealedInterfacesTest {

    @Test
    void theClosedHierarchyIsTheReturnType() {
        WorkItem moved = item("WI-1", Status.IN_PROGRESS, 5, "avery");

        TransitionResult applied = TransitionResult.of(true, moved, Status.OPEN, Status.IN_PROGRESS);
        TransitionResult rejected = TransitionResult.of(false, moved, Status.DONE, Status.OPEN);

        assertInstanceOf(TransitionResult.Applied.class, applied);
        assertInstanceOf(TransitionResult.Rejected.class, rejected);
        assertEquals(moved, ((TransitionResult.Applied) applied).item());
        assertTrue(((TransitionResult.Rejected) rejected).reason().contains("DONE"),
                "the rejection carries why, not just that");

        // Every assertion above is also satisfied by an ordinary interface with the
        // same two records. Sealing is not a behaviour, it is a fact about the type, and
        // the JVM carries it: the permitted set is in the class file and readable here.
        assertTrue(TransitionResult.class.isSealed(),
                "the hierarchy is closed, which is what makes an exhaustive switch legal");
        assertEquals(2, TransitionResult.class.getPermittedSubclasses().length,
                "and the compiler knows exactly which two implementations exist");
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
