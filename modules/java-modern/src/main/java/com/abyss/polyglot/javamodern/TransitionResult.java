package com.abyss.polyglot.javamodern;

/**
 * The outcome of a requested state change, as a closed set of possibilities.
 *
 * Sealed: the compiler knows Applied and Rejected are the only implementations, which is
 * what lets a switch over this type be exhaustive with no default branch. Add a third
 * variant and every switch stops compiling until it is handled — the failure lands at
 * build time instead of at runtime.
 */
public sealed interface TransitionResult permits TransitionResult.Applied, TransitionResult.Rejected {

    record Applied(WorkItem item) implements TransitionResult {}

    record Rejected(Status from, Status to, String reason) implements TransitionResult {}

    /**
     * Build the outcome. The return type names the closed hierarchy, so a caller cannot
     * receive some other implementation of this interface — there are no others. It is
     * the sealed declaration above that makes that guarantee.
     */
    static TransitionResult of(boolean allowed, WorkItem moved, Status from, Status to) {
        return allowed
                ? new Applied(moved)
                : new Rejected(from, to, "%s cannot move to %s".formatted(from, to));
    }
}
