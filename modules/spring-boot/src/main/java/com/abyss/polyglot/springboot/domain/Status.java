package com.abyss.polyglot.springboot.domain;

import java.util.Set;

/** Lifecycle states, in the shape the shared OpenAPI contract gives every backend. */
public enum Status {
    OPEN(Set.of("IN_PROGRESS", "CANCELLED")),
    IN_PROGRESS(Set.of("BLOCKED", "DONE", "CANCELLED")),
    BLOCKED(Set.of("IN_PROGRESS", "CANCELLED")),
    DONE(Set.of()),
    CANCELLED(Set.of());

    private final Set<String> allowed;

    Status(Set<String> allowed) {
        this.allowed = allowed;
    }

    public boolean canTransitionTo(Status next) {
        return allowed.contains(next.name());
    }
}
