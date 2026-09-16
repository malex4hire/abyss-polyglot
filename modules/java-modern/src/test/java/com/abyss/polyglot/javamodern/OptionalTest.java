package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that absence lives in findById's return type, not in a null. */
@Tag("optional")
class OptionalTest {

    @Test
    void absenceIsPartOfTheSignature() {
        Repository repo = new Repository();
        repo.put(item("WI-1", Status.OPEN, 5, "avery"));

        Optional<WorkItem> found = repo.findById("WI-1");
        Optional<WorkItem> missing = repo.findById("nope");

        assertTrue(found.isPresent());
        assertEquals("WI-1", found.get().id());
        assertTrue(missing.isEmpty(), "a missing id is empty, not null");
        assertEquals("fallback", missing.map(WorkItem::id).orElse("fallback"));
    }

    @Test
    void absenceLivesInFindByIdItselfNotABehindTheScenesNullableHelper() throws NoSuchMethodException {
        // findById's own callers already see Optional either way, so calling it cannot
        // distinguish "absence is the type" from "absence is null, wrapped for you at the
        // boundary." What differs is whether a second, nullable-returning method exists at
        // all: a lookup that can only ever answer through Optional has no such door left
        // open for a future caller to walk through and forget to check.
        assertThrows(NoSuchMethodException.class,
                () -> Repository.class.getMethod("findByIdOrNull", String.class),
                "a nullable-returning lookup must not exist alongside the Optional-returning one");
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
