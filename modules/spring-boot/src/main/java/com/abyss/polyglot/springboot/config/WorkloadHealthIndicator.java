package com.abyss.polyglot.springboot.config;

import com.abyss.polyglot.springboot.domain.WorkItemRepository;
import org.springframework.boot.health.contributor.Health;
import org.springframework.boot.health.contributor.HealthIndicator;
import org.springframework.stereotype.Component;

/** A custom contribution to the actuator health endpoint. */
@Component
public class WorkloadHealthIndicator implements HealthIndicator {

    private final WorkItemRepository repository;

    public WorkloadHealthIndicator(WorkItemRepository repository) {
        this.repository = repository;
    }

    /**
     * Operational surface as a first-class feature. Implementing HealthIndicator is
     * enough: the actuator starter finds every bean of this type and folds its result
     * into /actuator/health, alongside the database and disk checks it contributes on its
     * own. Metrics, environment and mappings arrive the same way.
     *
     * The traditional module has no equivalent. Operability there is something you build;
     * here it is something you receive and then decide how much of to expose.
     */
    @Override
    public Health health() {
        long live = repository.findByArchivedAtIsNullOrderByPriorityDescTitleAsc().size();
        return Health.up()
                .withDetail("liveWorkItems", live)
                .build();
    }
}
