package com.abyss.polyglot.springboot.config;

import com.abyss.polyglot.springboot.domain.Status;
import com.abyss.polyglot.springboot.domain.WorkItemEntity;
import com.abyss.polyglot.springboot.domain.WorkItemRepository;
import java.time.Instant;
import java.util.List;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Seed data, identical across every backend schema (Additional Constraints).
 *
 * Archive is a soft delete everywhere in this repo: nothing here or anywhere else
 * removes a row.
 */
@Configuration
public class Seeder {

    private record Row(String id, String title, Status status, int priority, String assignee, String tags) {}

    private static final List<Row> ROWS = List.of(
            new Row("WI-001", "Migrate batch scheduler", Status.OPEN, 5, "avery", "backend;legacy"),
            new Row("WI-002", "Rewrite claims parser", Status.IN_PROGRESS, 8, "briar", "backend;parser"),
            new Row("WI-003", "Retire SOAP endpoint", Status.OPEN, 3, "avery", "legacy"),
            new Row("WI-004", "Add audit trail export", Status.BLOCKED, 6, "casey", "audit"),
            new Row("WI-005", "Tune connection pool", Status.IN_PROGRESS, 7, "briar", "backend;performance"),
            new Row("WI-006", "Document transition rules", Status.OPEN, 2, "casey", "docs"));

    @Bean
    public ApplicationRunner seed(WorkItemRepository repository) {
        return args -> {
            Instant now = Instant.now();
            for (Row row : ROWS) {
                if (repository.findById(row.id()).isEmpty()) {
                    repository.save(new WorkItemEntity(row.id(), row.title(), row.status(),
                            row.priority(), row.assignee(), now, now, row.tags(), null));
                }
            }
        };
    }
}
