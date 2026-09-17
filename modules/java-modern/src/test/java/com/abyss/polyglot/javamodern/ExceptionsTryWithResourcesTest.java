package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that the seed reader closes up and suppresses a close failure. */
@Tag("exceptions-try-with-resources")
class ExceptionsTryWithResourcesTest {

    @Test
    void everyResourceClosesAndTheSeedParses() {
        Instant now = Instant.parse("2026-01-01T00:00:00Z");

        List<WorkItem> loaded = Seed.load(now);

        assertFalse(loaded.isEmpty(), "seed.csv is on the classpath and was read");
        WorkItem first = loaded.get(0);
        assertEquals("WI-001", first.id());
        assertEquals(Status.OPEN, first.status());
        assertTrue(first.tags().contains("backend"));
    }

    @Test
    void aCloseFailureWhileAnExceptionIsInFlightIsAttachedAsSuppressed() throws Exception {
        // load(Instant) hardcodes its classpath resource, so there is no seam to hand it a
        // resource whose close() throws on demand, so the suppression behaviour has to be
        // read from what the compiler actually emitted instead. try-with-resources
        // generates a call to Throwable.addSuppressed for exactly this case; a
        // hand-written finally block with an empty catch (the plainer alternative)
        // never emits one. This is the compiled-output layer, not a guess about source.
        Path classFile = Path.of(Seed.class.getResource("Seed.class").toURI());
        Process javap = new ProcessBuilder("javap", "-p", "-c", classFile.toString())
                .redirectErrorStream(true)
                .start();
        String disassembly = new String(javap.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        int exit = javap.waitFor();
        assertEquals(0, exit, "javap failed to disassemble Seed.class:\n" + disassembly);
        assertTrue(disassembly.contains("Throwable.addSuppressed"),
                "try-with-resources must attach a close failure as suppressed, which only "
                        + "the compiler emits for the try-with-resources form:\n" + disassembly);
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
