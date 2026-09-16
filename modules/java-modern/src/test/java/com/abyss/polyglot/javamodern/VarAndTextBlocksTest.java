package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that the banner text block keeps its shape but not its indent. */
@Tag("var-and-text-blocks")
class VarAndTextBlocksTest {

    @Test
    void theBlockKeepsItsShapeWithoutCarryingItsIndentation() {
        String banner = Banner.text("21.0.3", 6);

        assertTrue(banner.contains("com.sun.net.httpserver"));
        assertTrue(banner.contains("runtime : 21.0.3"));
        assertTrue(banner.contains("items   : 6"));
        assertFalse(banner.contains("                "),
                "incidental indentation is stripped by the text block");
    }

    /** Fixtures are built here rather than borrowed from the code another test
     *  covers, so a failure names the thing that actually broke. */
    static WorkItem item(String id, Status status, int priority, String assignee, String... tags) {
        Instant t = Instant.parse("2026-01-01T00:00:00Z");
        return new WorkItem(id, "title-" + id, status, priority, assignee, t, t, List.of(tags), null);
    }
}
