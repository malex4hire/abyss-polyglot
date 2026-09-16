package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that AuditTrail is handed its subject instead of inheriting it. */
@Tag("inheritance-vs-composition")
class InheritanceVsCompositionTest {

    @Test
    void theAuditedSubjectIsPassedInRatherThanInheritedFrom() {
        AuditTrail trail = new AuditTrail();
        Instant t = Instant.parse("2026-01-01T00:05:00Z");
        // The subject overrides the default method rather than inheriting it. That keeps
        // this test independent of the default-method test next door, and overriding is
        // exactly what a default method permits.
        Auditable subject = new Auditable() {
            @Override public Instant createdAt() { return Instant.parse("2026-01-01T00:00:00Z"); }
            @Override public Instant updatedAt() { return Instant.parse("2026-01-01T00:00:00Z"); }
            @Override public long secondsSinceTouched(Instant now) { return 42; }
        };

        AuditTrail.Entry entry = trail.record("WI-1", "transition", subject, t);

        assertEquals("WI-1", entry.itemId());
        assertEquals("transition", entry.what());
        // 42, not some other fixed number: the subject is passed in and its own
        // computation must be the source of the value. A version that took timing from an
        // inherited hook instead would answer with whatever that hook hardcodes,
        // regardless of what this particular subject reports — coincidentally 300 before
        // this fixture changed, which is exactly why that value never caught it.
        assertEquals(42, entry.staleSeconds());
        assertEquals(1, trail.entries().size());
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
