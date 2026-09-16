package com.abyss.polyglot.javamodern;

import java.time.Instant;

/**
 * Anything that records when it last changed. The default method gives implementors a
 * shared behaviour without a base class, which is the point of the feature.
 */
public interface Auditable {

    Instant createdAt();

    Instant updatedAt();

    /**
     * How long this item has been untouched, in seconds. A default method: behaviour on
     * an interface, available to every implementor, overridable by any of them, and
     * costing no place in the inheritance chain.
     */
    default long secondsSinceTouched(Instant now) {
        Instant last = updatedAt() == null ? createdAt() : updatedAt();
        return java.time.Duration.between(last, now).toSeconds();
    }
}
