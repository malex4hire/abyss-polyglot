package com.abyss.polyglot.javamodern;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** In-memory store. The point here is the collections API, not persistence. */
public final class Repository {

    private final Map<String, WorkItem> items = new LinkedHashMap<>();

    public void put(WorkItem item) {
        items.put(item.id(), item);
    }

    /**
     * B5. Insert only if the key is free, and say which happened.
     *
     * putIfAbsent returns the incumbent or null, so the caller learns the outcome from
     * the operation rather than by testing first and writing second — which is two
     * decisions about a map that can change between them.
     */
    public Optional<WorkItem> putIfAbsent(WorkItem item) {
        return Optional.ofNullable(items.putIfAbsent(item.id(), item));
    }

    /**
     * B5. Compare and set: replace only if the stored status is still the one the caller
     * decided against. Returns empty when it was not, which is the caller's signal that
     * somebody else already moved it.
     */
    public Optional<WorkItem> replaceIfStatusIs(String id, Status expected, WorkItem next) {
        WorkItem current = items.get(id);
        if (current == null || current.status() != expected) {
            return Optional.empty();
        }
        items.put(id, next);
        return Optional.of(next);
    }

    public int size() {
        return items.size();
    }

    /**
     * Every live item, insertion-ordered. LinkedHashMap because iteration order is part
     * of the contract here; a plain HashMap would make the query endpoint's output vary
     * between runs. The returned list is a copy, so a caller cannot reach back through
     * it and mutate the store.
     */
    public List<WorkItem> all() {
        List<WorkItem> live = new ArrayList<>(items.size());
        for (WorkItem item : items.values()) {
            if (!item.isArchived()) {
                live.add(item);
            }
        }
        return List.copyOf(live);
    }

    /**
     * Look up by id. Optional in the return type makes "might not be there" part of the
     * signature, so the caller cannot forget the case the way a null return lets them.
     */
    public Optional<WorkItem> findById(String id) {
        return Optional.ofNullable(items.get(id));
    }
}
