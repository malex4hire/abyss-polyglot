package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.web.WorkItemController;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.annotation.AnnotatedElementUtils;
import org.springframework.web.bind.annotation.ResponseBody;

/** Executable proof that @RestController puts @ResponseBody on the class, so every
 *  return value is serialised as the response body rather than resolved as a view. */
@Tag("rest-controller")
@SpringBootTest
class RestControllerTest {

    @Autowired
    WorkItemController controller;

    @Test
    void everyReturnValueGoesThroughAMessageConverter() {
        var body = controller.list(null, null);

        assertTrue(body.containsKey("items"),
                "the return value is the response body, not a view name");
    }

    @Test
    void theResponseBodyDecisionAppliesToTheClassNotOneMethodAtATime() {
        // The two forms are wire-identical for this one endpoint. Calling the method
        // directly, or even dispatching the request, cannot tell @RestController apart
        // from @Controller plus a per-method @ResponseBody, because both cover this
        // handler. What differs is whether the *next* handler is covered without anyone
        // remembering to say so, and that is a class-level fact, readable by reflection:
        // @RestController composes @ResponseBody onto the class, a per-method
        // @ResponseBody does not.
        assertTrue(AnnotatedElementUtils.hasAnnotation(WorkItemController.class, ResponseBody.class),
                "@RestController must put @ResponseBody on the class, not just on one method");
    }
}
