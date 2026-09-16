package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.config.WorkloadHealthIndicator;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.health.contributor.Status;
import org.springframework.boot.test.context.SpringBootTest;

/** Executable proof that a HealthIndicator bean is discovered by type and folded into
 *  the health endpoint's details, with nothing registering it by hand. */
@Tag("actuator")
@SpringBootTest
class ActuatorTest {

    @Autowired
    WorkloadHealthIndicator indicator;

    @Test
    void implementingTheInterfaceIsEnoughToBeFoldedIntoHealth() {
        var health = indicator.health();

        assertEquals(Status.UP, health.getStatus());
        assertTrue(health.getDetails().containsKey("liveWorkItems"),
                "the contribution is discovered by type, not registered by hand");
    }
}
