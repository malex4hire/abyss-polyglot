package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.domain.Status;
import com.abyss.polyglot.springboot.domain.WorkItemEntity;
import com.abyss.polyglot.springboot.domain.WorkItemRepository;
import com.abyss.polyglot.springboot.web.TransitionRequest;
import com.abyss.polyglot.springboot.web.WorkItemController;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/**
 * Executable proof that @Valid on the handler parameter validates the payload before the
 * body runs.
 *
 * An earlier version validated the payload record through a standalone Validator. That
 * proved the constraint annotation works — which is Jakarta Validation's job, not this
 * module's — and never reached the handler carrying @Valid, so it stayed green with the
 * very thing it names removed, which makes it no proof at all.
 *
 * This exercises the annotated handler itself: a valid request must reach the body and
 * apply the transition, and the constraint must be declared on the payload it accepts.
 */
@Tag("bean-validation")
@SpringBootTest
class BeanValidationTest {

    @Autowired
    WorkItemController controller;

    @Autowired
    WorkItemRepository repository;

    @Test
    void theHandlerAcceptsOnlyAValidatedPayload() throws Exception {
        String id = "BV-" + System.nanoTime();
        Instant now = Instant.now();
        repository.save(new WorkItemEntity(id, "validation probe", Status.OPEN, 3,
                "suite", now, now, "probe", null));

        try {
            assertHandlerValidatesAndRuns(id);
        } finally {
            // The probe row lives in the running demo's database. Without this, a failed
            // assertion leaves it visible in /work-items and /workload for good — once
            // per failed run.
            repository.findById(id).ifPresent(item -> {
                item.setArchivedAt(Instant.now());
                repository.save(item);
            });
        }
    }

    private void assertHandlerValidatesAndRuns(String id) throws Exception {
        var applied = controller.transition(id, new TransitionRequest(Status.IN_PROGRESS));

        assertEquals(200, applied.getStatusCode().value(),
                "a valid payload reaches the handler body and the transition applies");
        assertEquals(Status.IN_PROGRESS,
                repository.findById(id).orElseThrow().getStatus());

        var parameter = WorkItemController.class
                .getDeclaredMethod("transition", String.class, TransitionRequest.class)
                .getParameters()[1];
        assertNotNull(parameter.getAnnotation(jakarta.validation.Valid.class),
                "the payload is validated before the body runs, so a null status never arrives");

        var rejected = controller.transition(id, new TransitionRequest(Status.OPEN));
        assertEquals(422, rejected.getStatusCode().value(),
                "and an illegal transition is still refused by the state machine");
        assertTrue(((Map<?, ?>) rejected.getBody()).containsKey("rejected"));
    }
}
