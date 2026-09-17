package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that the status code comes from an exhaustive pattern switch. */
@Tag("pattern-matching-switch")
class PatternMatchingSwitchTest {

    @Test
    void switchDestructuresEachVariantExhaustively() {
        WorkItem live = item("WI-1", Status.IN_PROGRESS, 5, "avery");
        Instant t = Instant.parse("2026-03-01T00:00:00Z");

        assertEquals(200, Workflow.statusCodeFor(new TransitionResult.Applied(live)));
        assertEquals(409, Workflow.statusCodeFor(new TransitionResult.Applied(live.archived(t))),
                "the guarded case matches before the general one");
        assertEquals(422, Workflow.statusCodeFor(
                new TransitionResult.Rejected(Status.DONE, Status.OPEN, "terminal")));

        // The status codes above are also satisfied by an if/instanceof/cast chain,
        // which is the spelling a pattern switch replaces, so on their own they prove
        // nothing. Exhaustiveness is a compile-time property with no runtime handle, but
        // the mechanism leaves a mark: a pattern switch compiles to an invokedynamic
        // against SwitchBootstraps.typeSwitch, and a chain of instanceof does not.
        assertTrue(compiledFormOf(Workflow.class).contains("typeSwitch"),
                "the switch compiles to a typeSwitch bootstrap; an instanceof chain does not");
    }

    /** The class file as loaded, read as latin-1 so the constant pool is searchable text. */
    private static String compiledFormOf(Class<?> type) {
        String resource = "/" + type.getName().replace('.', '/') + ".class";
        try (var stream = type.getResourceAsStream(resource)) {
            assertNotNull(stream, "the compiled class is on the classpath: " + resource);
            return new String(stream.readAllBytes(), java.nio.charset.StandardCharsets.ISO_8859_1);
        } catch (java.io.IOException e) {
            throw new IllegalStateException("could not read " + resource, e);
        }
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
