package com.abyss.polyglot.springtraditional;

import java.time.Instant;
import java.util.List;

/**
 * The domain value, identical in shape to every other backend's, because all four serve
 * the one OpenAPI contract in contract/openapi.yaml.
 *
 * Note what is NOT demonstrated here: this is a record, but records are a language
 * lesson and belong to the modern Java module. A framework module using modern Java
 * naturally is fine; a framework module claiming to teach the language would blur the
 * line between the two kinds of module this demo draws.
 */
public record WorkItem(
        String id, String title, Status status, int priority, String assignee,
        Instant createdAt, Instant updatedAt, List<String> tags, Instant archivedAt) {

    public WorkItem {
        tags = tags == null ? List.of() : List.copyOf(tags);
    }

    public boolean isArchived() {
        return archivedAt != null;
    }
}
