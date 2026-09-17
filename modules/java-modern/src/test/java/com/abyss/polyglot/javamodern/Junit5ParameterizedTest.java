package com.abyss.polyglot.javamodern;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Method;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.platform.engine.TestExecutionResult;
import org.junit.platform.engine.discovery.DiscoverySelectors;
import org.junit.platform.launcher.Launcher;
import org.junit.platform.launcher.LauncherDiscoveryRequest;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;

/**
 * Executable proof that each CsvSource row becomes its own named invocation.
 *
 * It exercises grouping rather than the transition table. An earlier version called
 * Status.canTransitionTo, which another test already covers, so breaking that method
 * reddened this test too. A test demonstrating a mechanism should reach for the
 * least-covered code it can.
 */
@Tag("junit5-parameterized")
class Junit5ParameterizedTest {

    /**
     * One test method, many cases. Each row of the CsvSource becomes its own invocation
     * with its own name, its own pass or fail, and its own entry in the report, so a
     * failure names the case that broke rather than the loop that contained it, which is
     * what a hand-written for-loop over the same data cannot tell you.
     */
    @ParameterizedTest(name = "[{index}] {0} -> {1} assignees")
    @CsvSource({
            "avery,                 1",
            "avery;avery,           1",
            "avery;briar,           2",
            "avery;briar;avery,     2",
            "avery;briar;casey,     3",
    })
    void grouping(String assignees, int expectedGroups) {
        Instant at = Instant.parse("2026-01-01T00:00:00Z");
        String[] names = assignees.split(";");
        List<WorkItem> items = new ArrayList<>();
        for (int i = 0; i < names.length; i++) {
            items.add(new WorkItem("WI-" + i, "t", Status.OPEN, 1, names[i].trim(),
                    at, at, List.of(), null));
        }

        assertEquals(expectedGroups, Workload.groupByAssignee(items).size(),
                "one group per distinct assignee");
    }

    /**
     * A test cannot count its own invocations from inside itself, but it can run itself
     * through the platform's own Launcher and read what the runner recorded one layer up.
     * @ParameterizedTest gives each CsvSource row its own invocation with a display name
     * built from that row; a hand-rolled @Test looping over the same rows is a single
     * invocation named after the method. This assertion lives outside grouping() so a
     * rewritten grouping() cannot drop it, and it does not care what grouping() asserts
     * internally, only how many times, and under what names, the engine reports it ran.
     */
    @Test
    void theInvocationCarriesOneDisplayNamePerCase() {
        List<String> displayNames = new CopyOnWriteArrayList<>();
        TestExecutionListener collector = new TestExecutionListener() {
            @Override
            public void executionFinished(TestIdentifier testIdentifier, TestExecutionResult result) {
                if (testIdentifier.isTest()) {
                    displayNames.add(testIdentifier.getDisplayName());
                }
            }
        };

        // Reflect for the method rather than naming its parameter types: selectMethod's
        // string form resolves by reflectively looking up a method with that exact
        // signature and fails discovery (not falls back to a name-only match), the one
        // time it does not match, confirmed by running discovery standalone and reading
        // the exception. A rewritten grouping() need not keep (String, int); finding it
        // by name first and building the selector from the java.lang.reflect.Method this
        // class actually declares works regardless of what its parameter list becomes.
        Method groupingMethod = Arrays.stream(Junit5ParameterizedTest.class.getDeclaredMethods())
                .filter(m -> m.getName().equals("grouping"))
                .findFirst()
                .orElseThrow(() -> new AssertionError(
                        "no method named grouping() declared on " + Junit5ParameterizedTest.class));

        LauncherDiscoveryRequest request = LauncherDiscoveryRequestBuilder.request()
                .selectors(DiscoverySelectors.selectMethod(Junit5ParameterizedTest.class, groupingMethod))
                .build();
        Launcher launcher = LauncherFactory.create();
        launcher.registerTestExecutionListeners(collector);
        launcher.execute(request);

        assertEquals(5, displayNames.size(),
                "one invocation per CsvSource row, not one for the whole method: " + displayNames);
        assertTrue(displayNames.stream().allMatch(name -> name.matches("\\[\\d+].*assignees.*")),
                "each invocation named from its own case: " + displayNames);
    }
}
