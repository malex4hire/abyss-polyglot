package com.abyss.polyglot.springtraditional;

import java.util.Set;

/** Lifecycle states. Same contract as every other backend. */
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
