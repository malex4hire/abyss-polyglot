package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that a bounded pool runs every task on its own threads. */
@Tag("executor-service")
class ExecutorServiceTest {

    @Test
    void aBoundedPoolCompletesEveryTaskItWasGiven() {
        Map<String, List<WorkItem>> grouped = Map.of(
                "avery", List.of(item("WI-1", Status.OPEN, 5, "avery")),
                "briar", List.of(item("WI-2", Status.OPEN, 8, "briar")));

        Map<String, Integer> scores = Workload.pooled(grouped);

        assertEquals(2, scores.size());
        assertEquals(5, scores.get("avery"));
        assertEquals(8, scores.get("briar"));
    }

    @Test
    void tasksRunOnPoolThreadsNotTheCallingThread() {
        // Scores alone cannot tell a pool from a loop — both produce the same numbers.
        // Every task reports the thread it ran on: a bounded pool never hands work to the
        // thread that called it, and a serial loop never hands it to anything else.
        Map<String, List<WorkItem>> grouped = Map.of(
                "avery", List.of(item("WI-1", Status.OPEN, 5, "avery")),
                "briar", List.of(item("WI-2", Status.OPEN, 8, "briar")));
        Set<Thread> seen = ConcurrentHashMap.newKeySet();
        Thread callingThread = Thread.currentThread();

        Workload.pooled(grouped, seen::add);

        assertEquals(2, seen.size(), "each task must run, and report the thread it ran on");
        assertTrue(seen.stream().noneMatch(t -> t == callingThread),
                "a bounded pool runs tasks on its own threads, never the caller's");
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
