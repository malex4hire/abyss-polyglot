package com.abyss.polyglot.javamodern;

import java.util.Set;

/**
 * The work item lifecycle. An enum that carries behaviour rather than a bare label:
 * each constant knows which states it may move to, so the state machine lives with the
 * data instead of in a switch somewhere else.
 */
public enum Status {
    OPEN(Set.of("IN_PROGRESS", "CANCELLED")),
    IN_PROGRESS(Set.of("BLOCKED", "DONE", "CANCELLED")),
    BLOCKED(Set.of("IN_PROGRESS", "CANCELLED")),
    DONE(Set.of()),
    CANCELLED(Set.of());

    /** Each constant is constructed with its own rule, so the rule travels with it. */
    private final Set<String> allowed;

    Status(Set<String> allowed) {
        this.allowed = allowed;
    }

    /**
     * Whether this state may move to {@code next}. The rule belongs to the constant, so
     * adding a state cannot leave a transition table somewhere else out of date.
     */
    public boolean canTransitionTo(Status next) {
        return allowed.contains(next.name());
    }
}
