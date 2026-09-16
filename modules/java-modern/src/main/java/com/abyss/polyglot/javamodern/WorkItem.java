package com.abyss.polyglot.javamodern;

import java.time.Instant;
import java.util.List;

/**
 * The domain value. A record: the compiler supplies the constructor, accessors, equals,
 * hashCode and toString, and the type is immutable, so a state change produces a new
 * value rather than mutating this one.
 */
public record WorkItem(
        String id,
        String title,
        Status status,
        int priority,
        String assignee,
        Instant createdAt,
        Instant updatedAt,
        List<String> tags,
        Instant archivedAt) implements Auditable {

    /**
     * The compact constructor: the one place a record lets you touch the components on
     * the way in. Normalising here means no instance can exist with a null tag list.
     */
    public WorkItem {
        tags = tags == null ? List.of() : List.copyOf(tags);
    }

    /**
     * Derive a new item in a different state. Nothing here mutates: the record is
     * immutable, so the transition returns a value and the caller decides what to do
     * with it. The record header above is what makes that immutability free.
     */
    public WorkItem withStatus(Status next, Instant at) {
        return new WorkItem(id, title, next, priority, assignee,
                createdAt, at, tags, archivedAt);
    }

    /** Archive is a soft delete: the row stays, the timestamp marks it. */
    public WorkItem archived(Instant at) {
        return new WorkItem(id, title, status, priority, assignee,
                createdAt, at, tags, at);
    }

    public boolean isArchived() {
        return archivedAt != null;
    }
}
