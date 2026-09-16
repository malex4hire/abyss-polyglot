package com.abyss.polyglot.springtraditional;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** The service layer: where the transaction boundary and the domain rules live. */
@Service
public class WorkItemService {

    private final WorkItemRepository repository;

    public WorkItemService(WorkItemRepository repository) {
        this.repository = repository;
    }

    /**
     * Where the domain decision lives: not in the controller, which should only translate
     * HTTP, and not in the repository, which should only move rows. Putting the
     * transition rule here is what lets the same rule serve a controller, a scheduled job
     * or a test with no HTTP in sight.
     */
    public Optional<WorkItem> transition(String id, Status next, Instant at) {
        Optional<WorkItem> current = repository.findById(id);
        if (current.isEmpty()) {
            return Optional.empty();
        }
        // B5. Already there is not an illegal move, it is a move that has happened, which
        // is what a client retrying a dropped response is asking about. Only the self-edge
        // changes; every genuine refusal below still refuses.
        if (current.get().status() == next) {
            return current;
        }
        if (!current.get().status().canTransitionTo(next)) {
            return Optional.empty();
        }
        applyTransition(id, current.get().status(), next, at);
        return repository.findById(id);
    }

    @Transactional
    public void applyTransition(String id, Status expected, Status next, Instant at) {
        // The precondition travels with the write. Zero rows means somebody moved it
        // between the read and here, and the caller re-reads rather than overwriting.
        repository.updateStatus(id, expected, next, at);
    }

    /**
     * One unit of work. The proxy opens a transaction on entry and commits on return, or
     * rolls back if a runtime exception escapes. It is silently inert without the
     * transaction manager bean declared in RootConfig, and inert again when called from
     * inside this class, because the proxy is only crossed from outside.
     */
    @Transactional
    public void archive(String id, Instant at) {
        repository.archive(id, at);
    }

    @SuppressWarnings("unchecked")
    @Transactional
    public CreateResult create(java.util.Map<String, Object> body, Instant at) {
        List<String> tags = (List<String>) body.getOrDefault("tags", List.of());
        WorkItem item = new WorkItem(
                key(body), String.valueOf(body.get("title")),
                Status.valueOf(String.valueOf(body.get("status"))),
                ((Number) body.get("priority")).intValue(),
                String.valueOf(body.get("assignee")), at, at, tags, null);
        // B5. Rows written decides the answer. Zero means the key was taken and this
        // call created nothing, so the caller gets the row that is actually there.
        if (repository.insert(item) == 0) {
            return new CreateResult(repository.findById(item.id()).orElse(item), false);
        }
        return new CreateResult(item, true);
    }

    /**
     * B5. The key, or a refusal. String.valueOf turns an absent id into the literal
     * "null" and a JSON null into the same, which is a row nobody can address, written
     * without a word.
     */
    public static String key(java.util.Map<String, Object> body) {
        Object raw = body.get("id");
        String id = raw == null ? "" : String.valueOf(raw).trim();
        if (id.isEmpty() || id.equals("null")) {
            throw new IllegalArgumentException("id is required");
        }
        return id;
    }

    /** B5. What the create did, carried out of the method that knows. */
    public record CreateResult(WorkItem item, boolean created) {}

    public Optional<WorkItem> findById(String id) {
        return repository.findById(id);
    }

    public List<WorkItem> query(Status status, String tag) {
        return repository.findAll().stream()
                .filter(item -> status == null || item.status() == status)
                .filter(item -> tag == null || tag.isBlank()
                        || item.tags().stream().anyMatch(
                                candidate -> candidate.toLowerCase().contains(tag.toLowerCase())))
                .toList();
    }

    /** B3 aggregate, sequential here; concurrency is a language-module lesson, not this
     *  module's. */
    public Map<String, Integer> workload() {
        Map<String, Integer> byAssignee = new LinkedHashMap<>();
        for (WorkItem item : repository.findAll()) {
            byAssignee.merge(item.assignee(), item.priority(), Integer::sum);
        }
        return byAssignee;
    }
}
