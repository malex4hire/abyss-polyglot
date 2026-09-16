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

/** Executable proof that the fan-out gets one virtual thread per task, not a pool. */
@Tag("virtual-threads")
class VirtualThreadsTest {

    @Test
    void oneThreadPerTaskWithNoPoolToSize() {
        Map<String, List<WorkItem>> grouped = Map.of(
                "avery", List.of(item("WI-1", Status.OPEN, 5, "avery")),
                "briar", List.of(item("WI-2", Status.OPEN, 8, "briar")),
                "casey", List.of(item("WI-3", Status.OPEN, 2, "casey")));

        Set<Thread> ran = ConcurrentHashMap.newKeySet();

        long started = System.nanoTime();
        Map<String, Integer> scores = Workload.virtual(grouped, ran::add);
        long elapsedMillis = (System.nanoTime() - started) / 1_000_000;

        assertEquals(3, scores.size());
        assertEquals(15, scores.values().stream().mapToInt(Integer::intValue).sum());

        // The assertion that distinguishes virtual threads from a bounded pool. Elapsed
        // time alone proves the tasks overlapped, which a cached platform pool does too;
        // it is a proof of concurrency, not of virtual threads.
        assertEquals(3, ran.size(), "one thread per task, not a pool handing out reused threads");
        assertTrue(ran.stream().allMatch(Thread::isVirtual),
                "every task ran on a virtual thread: "
                        + ran.stream().map(t -> t + " virtual=" + t.isVirtual()).toList());
        assertTrue(elapsedMillis < 150,
                "blocking tasks overlap rather than queueing: " + elapsedMillis + "ms");
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
