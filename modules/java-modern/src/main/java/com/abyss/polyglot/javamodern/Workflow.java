package com.abyss.polyglot.javamodern;

import java.time.Instant;

/** B2 Transition: the state machine, and the typed rejection it produces. */
public final class Workflow {

    private Workflow() {
    }

    /**
     * Apply a requested transition. Orchestration only: the three units it chains are
     * each demonstrated on their own.
     */
    public static TransitionResult apply(WorkItem item, Status next, Instant at) {
        boolean allowed = item.status().canTransitionTo(next);
        WorkItem moved = allowed ? item.withStatus(next, at) : item;
        return TransitionResult.of(allowed, moved, item.status(), next);
    }

    /**
     * Turn the outcome into an HTTP status. Pattern matching for switch destructures each
     * variant and binds its components in the same breath as it matches. No default
     * branch: the type is sealed, so the compiler proves this is exhaustive, and a new
     * variant breaks the build here rather than falling through silently at runtime.
     */
    public static int statusCodeFor(TransitionResult result) {
        return switch (result) {
            case TransitionResult.Applied a when a.item().isArchived() -> 409;
            case TransitionResult.Applied ignored -> 200;
            case TransitionResult.Rejected ignored -> 422;
        };
    }
}
