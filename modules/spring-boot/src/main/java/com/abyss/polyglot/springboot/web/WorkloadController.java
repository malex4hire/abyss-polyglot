package com.abyss.polyglot.springboot.web;

import com.abyss.polyglot.springboot.domain.WorkItemEntity;
import com.abyss.polyglot.springboot.domain.WorkItemRepository;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/** B3 aggregate, in the same shape the shared contract gives every other backend. */
@RestController
public class WorkloadController {

    private final WorkItemRepository repository;

    public WorkloadController(WorkItemRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/workload")
    public Map<String, Map<String, Integer>> workload() {
        Map<String, Integer> byAssignee = new LinkedHashMap<>();
        for (WorkItemEntity item : repository.liveByPriority()) {
            byAssignee.merge(item.getAssignee(), item.getPriority(), Integer::sum);
        }
        return Map.of("byAssignee", byAssignee);
    }
}
