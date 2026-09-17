package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that the query clauses are composable lambdas, not inner classes. */
@Tag("lambdas-functional-interfaces")
class LambdasFunctionalInterfacesTest {

    @Test
    void clausesComposeWithoutKnowingAboutEachOther() {
        WorkItem backendOpen = item("WI-1", Status.OPEN, 5, "avery", "backend");
        WorkItem backendDone = item("WI-2", Status.DONE, 5, "avery", "backend");
        WorkItem docsOpen = item("WI-3", Status.OPEN, 5, "casey", "docs");

        assertTrue(Queries.filterFor(Status.OPEN, "backend").test(backendOpen));
        assertFalse(Queries.filterFor(Status.OPEN, "backend").test(backendDone));
        assertFalse(Queries.filterFor(Status.OPEN, "backend").test(docsOpen));
        assertTrue(Queries.filterFor(null, null).test(docsOpen), "absent criteria filter nothing out");
    }

    @Test
    void theClausesAreLambdasNotAnonymousClasses() {
        // Identical filtering is not identical bytecode. A lambda compiles to an
        // invokedynamic call site resolved by LambdaMetafactory at first use, so the
        // instance it produces carries a synthetic "$$Lambda" class name and no compiled
        // .class file of its own. An anonymous inner class instead gets a real, numbered
        // nested class (Queries$1, Queries$2, ...) that the compiler writes to disk. Both
        // produce a working Predicate; only one is what "lambda" claims.
        String className = Queries.filterFor(null, null).getClass().getName();
        assertTrue(className.contains("Lambda"),
                "expected a lambda-generated class name (containing \"Lambda\"), got: " + className);
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
