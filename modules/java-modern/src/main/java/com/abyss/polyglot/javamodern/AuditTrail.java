package com.abyss.polyglot.javamodern;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/**
 * Change history.
 *
 * This class is composed into the service rather than extended by it. Inheritance would
 * couple the service to this class's shape forever and spend its single superclass slot;
 * composition keeps the relationship a field, which can be swapped, wrapped, or dropped
 * without touching the type hierarchy.
 */
public final class AuditTrail {

    public record Entry(String itemId, String what, Instant at, long staleSeconds) {}

    private final List<Entry> entries = new ArrayList<>();

    public List<Entry> entries() {
        return List.copyOf(entries);
    }

    /**
     * Record a change. The audited object is passed in rather than inherited from: this
     * class has no base class and imposes none, so anything Auditable can be recorded
     * here without joining a hierarchy. "Has a trail" rather than "is a trail".
     */
    public Entry record(String itemId, String what, Auditable subject, Instant at) {
        Entry entry = new Entry(itemId, what, at, subject.secondsSinceTouched(at));
        entries.add(entry);
        return entry;
    }
}
