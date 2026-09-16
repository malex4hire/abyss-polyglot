package com.abyss.polyglot.javamodern;

import java.util.Comparator;
import java.util.List;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/** B1 Query: multi-field sort, status filter, tag containment. */
public final class Queries {

    private Queries() {
    }

    /**
     * Build the filter for a request. Predicate is a functional interface, so each clause
     * is a lambda and {@code and} composes them into one without any of them knowing about
     * the others. Absent criteria contribute an always-true clause rather than a branch.
     */
    public static Predicate<WorkItem> filterFor(Status status, String tag) {
        Predicate<WorkItem> byStatus = status == null ? item -> true : item -> item.status() == status;
        // Contains, not equals: a filter box that only answers to a whole tag asks the
        // person to type the answer. Lowercased on both sides so the match is on the text,
        // not on how it was typed.
        Predicate<WorkItem> byTag = tag == null || tag.isBlank()
                ? item -> true
                : item -> item.tags().stream()
                        .anyMatch(candidate -> candidate.toLowerCase().contains(tag.toLowerCase()));
        return byStatus.and(byTag);
    }

    /**
     * The query pipeline. A stream states what happens to the data rather than how to
     * walk it: filter, then a multi-field sort built by chaining comparators, then
     * collect into an unmodifiable list. Priority descends, then title ascends, so the
     * ordering is total and the endpoint is deterministic.
     */
    public static List<WorkItem> query(List<WorkItem> source, Predicate<WorkItem> filter) {
        return source.stream()
                .filter(filter)
                .sorted(Comparator.comparingInt(WorkItem::priority).reversed()
                        .thenComparing(WorkItem::title))
                .collect(Collectors.toUnmodifiableList());
    }

    /**
     * The first {@code limit} elements in natural order. The bound {@code T extends
     * Comparable<T>} is what makes {@code sorted()} legal: without it the compiler has no
     * evidence the elements can be ordered. The bound buys the capability, and it is
     * checked once here rather than at every call site.
     */
    public static <T extends Comparable<T>> List<T> firstInOrder(List<T> values, int limit) {
        return values.stream()
                .sorted()
                .limit(Math.max(0, limit))
                .toList();
    }
}
