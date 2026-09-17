package com.abyss.polyglot.springboot;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.abyss.polyglot.springboot.domain.Status;
import com.abyss.polyglot.springboot.domain.WorkItemEntity;
import com.abyss.polyglot.springboot.domain.WorkItemRepository;
import com.abyss.polyglot.springboot.web.WorkloadController;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Executable proof that @WebMvcTest starts the web layer and nothing below it: the
 * repository has to be supplied as a mock because JPA was never configured.
 *
 * Unlike the rest of this module, a test harness is not reachable from a served request
 * path; it exists only to be run.
 */
@Tag("web-mvc-test-slice")
@WebMvcTest(WorkloadController.class)
class WebMvcTestSliceTest {

    @Autowired
    MockMvc mockMvc;

    @MockitoBean
    WorkItemRepository repository;

    /**
     * A slice: the web layer and nothing below it. @WebMvcTest starts the dispatcher, the
     * converters, the validator and the advice, and leaves out the datasource, JPA and
     * every other auto-configuration, which is why the repository has to be supplied as
     * a mock rather than being available.
     *
     * Against the traditional module's standalone MockMvc, the difference is what is
     * real: standalone wires the controller by hand and tests no configuration, while
     * this boots the actual web configuration and tests it.
     */
    @Test
    void theWebLayerAndNothingBelowIt() throws Exception {
        Instant now = Instant.now();
        when(repository.liveByPriority())
                .thenReturn(List.of(new WorkItemEntity("WI-1", "one", Status.OPEN, 5,
                        "avery", now, now, "backend", null)));

        mockMvc.perform(get("/workload"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.byAssignee.avery").value(5));
    }
}
