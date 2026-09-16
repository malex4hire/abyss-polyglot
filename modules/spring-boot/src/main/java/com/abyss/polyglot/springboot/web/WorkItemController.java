package com.abyss.polyglot.springboot.web;

import com.abyss.polyglot.springboot.domain.Status;
import com.abyss.polyglot.springboot.domain.WorkItemEntity;
import com.abyss.polyglot.springboot.domain.WorkItemRepository;
import jakarta.validation.Valid;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Serves the shared OpenAPI contract, identically to every other backend. */
@RestController
@RequestMapping("/work-items")
public class WorkItemController {

    private final WorkItemRepository repository;

    public WorkItemController(WorkItemRepository repository) {
        this.repository = repository;
    }

    /**
     * @RestController is @Controller plus @ResponseBody: every return value goes through
     * a message converter instead of being resolved as a view name. The converter itself
     * arrived from the web starter — nothing in this module registers one, which is what
     * the traditional module has to do by hand in WebConfig.
     */
    @GetMapping
    public Map<String, List<WorkItemEntity>> list(
            @RequestParam(required = false) Status status,
            @RequestParam(required = false) String tag) {
        List<WorkItemEntity> found = repository.findByArchivedAtIsNullOrderByPriorityDescTitleAsc()
                .stream()
                .filter(item -> status == null || item.getStatus() == status)
                .filter(item -> tag == null || tag.isBlank()
                        || java.util.Arrays.stream(item.getTags().split(";"))
                                .anyMatch(candidate -> candidate.toLowerCase()
                                        .contains(tag.toLowerCase())))
                .toList();
        return Map.of("items", found);
    }

    /**
     * Fetch by id. Archived items resolve: archive is a soft delete, so the list is the
     * active view and this addresses the record. Spring Data supplies findById, which is
     * the pair's contrast — the traditional side reaches its own JdbcTemplate query.
     */
    @GetMapping("/{id}")
    public ResponseEntity<Map<String, WorkItemEntity>> byId(@PathVariable String id) {
        return repository.findById(id)
                .map(item -> ResponseEntity.ok(Map.of("item", item)))
                .orElseGet(() -> ResponseEntity.status(404).build());
    }

    @PostMapping
    public ResponseEntity<?> create(@RequestBody Map<String, Object> body) {
        Instant now = Instant.now();
        @SuppressWarnings("unchecked")
        List<String> tags = (List<String>) body.getOrDefault("tags", List.of());
        // B5. String.valueOf turns an absent id into the literal "null", which is a row
        // nobody can address, written without a word. The key decides before anything else.
        Object rawId = body.get("id");
        String key = rawId == null ? "" : String.valueOf(rawId).trim();
        if (key.isEmpty() || key.equals("null")) {
            return ResponseEntity.badRequest().body(Map.of("error", "id is required"));
        }
        // save() is an upsert, so it cannot report a conflict. The existing row is the
        // answer, and returning it is what makes the repeat honest rather than survivable.
        var incumbent = repository.findById(key);
        if (incumbent.isPresent()) {
            return ResponseEntity.ok(Map.of("item", incumbent.get()));
        }
        WorkItemEntity created = new WorkItemEntity(
                key, String.valueOf(body.get("title")),
                Status.valueOf(String.valueOf(body.get("status"))),
                ((Number) body.get("priority")).intValue(),
                String.valueOf(body.get("assignee")), now, now, String.join(";", tags), null);
        repository.save(created);
        ChangeStreamController.emit("created", created.getId());
        return ResponseEntity.status(201).body(Map.of("item", created));
    }

    /**
     * @Valid on the parameter runs the constraints declared on the payload record before
     * the handler body executes. A null status never reaches this code: the framework
     * rejects the request and the advice below turns that into a 422.
     *
     * The validator was auto-configured by the validation starter. The traditional module
     * would have to declare one and wire it into the MVC config.
     */

    @PostMapping("/{id}/transition")
    public ResponseEntity<?> transition(@PathVariable String id,
                                        @Valid @RequestBody TransitionRequest request) {
        return repository.findById(id)
                .map(item -> {
                    // B5. Already there is not an illegal move, it is a move that has
                    // happened — what a retry of a dropped response is asking about. Only
                    // the self-edge changes; every genuine refusal still refuses.
                    if (item.getStatus() == request.status()) {
                        return ResponseEntity.ok(Map.of("item", item));
                    }
                    if (!item.getStatus().canTransitionTo(request.status())) {
                        return ResponseEntity.unprocessableEntity()
                                .body(Map.of("rejected",
                                        Map.of("id", id, "to", request.status().name())));
                    }
                    // Compare and set: the status this decision was made against is the
                    // precondition of the write, so a concurrent move is not overwritten.
                    int moved = repository.moveStatus(id, item.getStatus(),
                            request.status(), Instant.now());
                    if (moved == 0) {
                        return ResponseEntity.ok(Map.of("item",
                                repository.findById(id).orElse(item)));
                    }
                    ChangeStreamController.emit("transitioned", item.getId());
                    return ResponseEntity.ok(Map.of("item",
                            repository.findById(id).orElse(item)));
                })
                .orElseGet(() -> ResponseEntity.status(404).body(Map.of("error", "no such work item")));
    }

    @PostMapping("/{id}/archive")
    public Map<String, String> archive(@PathVariable String id) {
        return repository.findById(id).map(item -> {
            Instant now = Instant.now();
            item.setArchivedAt(now);
            item.setUpdatedAt(now);
            repository.save(item);
            return Map.of("archived", id);
        }).orElse(Map.of("error", "no such work item"));
    }
}
