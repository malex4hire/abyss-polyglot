package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import com.abyss.polyglot.springtraditional.web.WorkItemController;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

/** Executable proof that the handler declares only which requests it wants: the request
 *  parameters arrive bound and typed, and the return value becomes the response body. */

@Tag("controller-request-mapping")
class ControllerRequestMappingTest {

    @Test
    void theHandlerStatesOnlyWhichRequestsItWants() {
        var stub = new WorkItemService(new WorkItemRepository(
                new JdbcTemplate(new DriverManagerDataSource()))) {
            @Override
            public List<WorkItem> query(Status status, String tag) {
                Instant t = Instant.parse("2026-01-01T00:00:00Z");
                return List.of(new WorkItem("WI-1", "one", Status.OPEN, 5, "avery",
                        t, t, List.of("backend"), null));
            }
        };

        Map<String, List<WorkItem>> body = new WorkItemController(stub).list(Status.OPEN, "backend");

        assertEquals(1, body.get("items").size());
        assertEquals("WI-1", body.get("items").get(0).id());
    }
}
