package com.abyss.polyglot.springtraditional.web;

import com.abyss.polyglot.springtraditional.Status;
import com.abyss.polyglot.springtraditional.WorkItem;
import com.abyss.polyglot.springtraditional.WorkItemService;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** The HTTP surface. Serves the same contract/openapi.yaml as every other backend. */
@RestController
@RequestMapping("/work-items")
public class WorkItemController {

    private final WorkItemService service;

    public WorkItemController(WorkItemService service) {
        this.service = service;
    }

    /**
     * A handler method, bound to a route by annotation. The dispatcher matches path and
     * verb, binds query parameters to arguments by name and type, and runs the return
     * value through a message converter. Everything between the socket and this method
     * body is the framework's; what is stated here is only which requests it wants.
     */
    @GetMapping
    public Map<String, List<WorkItem>> list(
            @RequestParam(required = false) Status status,
            @RequestParam(required = false) String tag) {
        return Map.of("items", service.query(status, tag));
    }

    /**
     * Fetch by id. Archived items resolve: archive is a soft delete, so the list is the
     * active view and this addresses the record.
     */
    @GetMapping("/{id}")
    public ResponseEntity<Map<String, WorkItem>> byId(@PathVariable String id) {
        return service.findById(id)
                .map(item -> ResponseEntity.ok(Map.of("item", item)))
                .orElseGet(() -> ResponseEntity.status(404).build());
    }

    @PostMapping
    public ResponseEntity<Map<String, WorkItem>> create(@RequestBody Map<String, Object> body) {
        WorkItemService.CreateResult result = service.create(body, Instant.now());
        if (!result.created()) {
            // B5. The key was taken, this call wrote nothing, so nothing is announced and
            // 201 would be a claim about a row that was already there.
            return ResponseEntity.ok(Map.of("item", result.item()));
        }
        ChangeStreamController.emit("created", result.item().id());
        return ResponseEntity.status(201).body(Map.of("item", result.item()));
    }

    @PostMapping("/{id}/transition")
    public ResponseEntity<?> transition(@PathVariable String id,
                                        @RequestBody Map<String, String> body) {
        Status next = Status.valueOf(body.get("status"));
        // Not found and refused are different answers. Collapsing them into one status
        // code makes a typo indistinguishable from an illegal move.
        if (service.findById(id).isEmpty()) {
            return ResponseEntity.status(404).body(Map.of("error", "no such work item", "id", id));
        }
        Optional<WorkItem> moved = service.transition(id, next, Instant.now());
        moved.ifPresent(item -> ChangeStreamController.emit("transitioned", item.id()));
        return moved.<ResponseEntity<?>>map(item -> ResponseEntity.ok(Map.of("item", item)))
                .orElseGet(() -> ResponseEntity.unprocessableEntity()
                        .body(Map.of("rejected", Map.of("id", id, "to", next.name()))));
    }

    @PostMapping("/{id}/archive")
    public Map<String, String> archive(@PathVariable String id) {
        service.archive(id, Instant.now());
        ChangeStreamController.emit("archived", id);
        return Map.of("archived", id);
    }
}
