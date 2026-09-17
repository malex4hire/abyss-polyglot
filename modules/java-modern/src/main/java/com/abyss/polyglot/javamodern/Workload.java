package com.abyss.polyglot.javamodern;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * B3 Aggregate: per-assignee rollup, fanned out over deliberately slow per-assignee work.
 * The slowness is the point, because it is what makes the concurrency model visible.
 */
public final class Workload {

    private Workload() {
    }

    /** Deliberately slow per-assignee computation. Blocking, not spinning.
     *
     *  Sums inline rather than calling totalPriority: that method has its own test, and
     *  routing the concurrency work through it would make one broken method redden three
     *  unrelated tests. */
    static int scoreFor(String assignee, List<WorkItem> items) {
        try {
            Thread.sleep(50);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        int sum = 0;
        for (WorkItem item : items) {
            sum += item.priority();
        }
        return sum;
    }

    /**
     * Sum of priorities. The accumulator is {@code int}, a primitive: a value held
     * directly, with no identity and no null. Had it been {@code Integer}, every addition
     * would unbox and rebox through a heap object, and an unset total would be null
     * rather than zero. Reference types answer "which object"; primitives only ever
     * answer "what value", which is all a sum needs.
     */
    static int totalPriority(List<WorkItem> items) {
        int total = 0;
        for (WorkItem item : items) {
            total += item.priority();
        }
        return total;
    }

    static Map<String, List<WorkItem>> groupByAssignee(List<WorkItem> items) {
        Map<String, List<WorkItem>> grouped = new LinkedHashMap<>();
        for (WorkItem item : items) {
            grouped.computeIfAbsent(item.assignee(), key -> new ArrayList<>()).add(item);
        }
        return grouped;
    }

    /**
     * Fan out over a fixed pool. The pool is a bounded resource: submit returns a Future
     * immediately, the work queues behind however many platform threads exist, and the
     * caller blocks on get. Sizing it is a real decision, because each thread costs a
     * megabyte-scale stack, and try-with-resources shuts it down on the way out.
     */
    static Map<String, Integer> pooled(Map<String, List<WorkItem>> grouped) {
        return pooled(grouped, thread -> { });
    }

    /**
     * The same, with each task reporting the thread it ran on.
     *
     * Scores alone cannot tell a bounded pool from a loop that fans out nothing. Both
     * produce the same numbers for the same input. The observer is how the property
     * becomes checkable from outside, the same move {@code virtual} already makes below.
     */
    static Map<String, Integer> pooled(Map<String, List<WorkItem>> grouped,
            java.util.function.Consumer<Thread> onThread) {
        Map<String, Integer> scores = new LinkedHashMap<>();
        try (ExecutorService pool = Executors.newFixedThreadPool(4)) {
            Map<String, Future<Integer>> pending = new LinkedHashMap<>();
            for (Map.Entry<String, List<WorkItem>> entry : grouped.entrySet()) {
                Callable<Integer> task = () -> {
                    onThread.accept(Thread.currentThread());
                    return scoreFor(entry.getKey(), entry.getValue());
                };
                pending.put(entry.getKey(), pool.submit(task));
            }
            for (Map.Entry<String, Future<Integer>> entry : pending.entrySet()) {
                try {
                    scores.put(entry.getKey(), entry.getValue().get());
                } catch (Exception e) {
                    throw new IllegalStateException("workload task failed", e);
                }
            }
        }
        return scores;
    }

    /**
     * The same fan-out on virtual threads. One thread per task, no pool to size: a virtual
     * thread parked on a blocking call releases its carrier, so the cost of waiting is a
     * heap object rather than an OS thread. The code is the ordinary blocking shape, and
     * that is the whole argument for the feature. Structured concurrency: the executor
     * closes only when every task it started has finished.
     */
    static Map<String, Integer> virtual(Map<String, List<WorkItem>> grouped) {
        return virtual(grouped, thread -> { });
    }

    /**
     * The same, with each task reporting the thread it ran on.
     *
     * Timing alone cannot tell virtual threads from a cached platform pool. Both overlap
     * blocking work and both finish this fan-out in well under the serial time. A test
     * that measures only elapsed milliseconds passes identically against the fixed pool
     * this method exists to contrast with, which makes it a proof of concurrency and not
     * of virtual threads. The observer is how the property becomes checkable from
     * outside.
     */
    static Map<String, Integer> virtual(Map<String, List<WorkItem>> grouped,
            java.util.function.Consumer<Thread> onThread) {
        Map<String, Integer> scores = new LinkedHashMap<>();
        try (ExecutorService threads = Executors.newVirtualThreadPerTaskExecutor()) {
            Map<String, Future<Integer>> pending = new LinkedHashMap<>();
            for (Map.Entry<String, List<WorkItem>> entry : grouped.entrySet()) {
                pending.put(entry.getKey(), threads.submit(() -> {
                    onThread.accept(Thread.currentThread());
                    return scoreFor(entry.getKey(), entry.getValue());
                }));
            }
            for (Map.Entry<String, Future<Integer>> entry : pending.entrySet()) {
                try {
                    scores.put(entry.getKey(), entry.getValue().get());
                } catch (Exception e) {
                    throw new IllegalStateException("workload task failed", e);
                }
            }
        }
        return scores;
    }
}
