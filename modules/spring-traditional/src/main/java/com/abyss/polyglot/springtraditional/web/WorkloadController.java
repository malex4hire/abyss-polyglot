package com.abyss.polyglot.springtraditional.web;

import com.abyss.polyglot.springtraditional.WorkItemService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/** B3 aggregate. Same contract shape as every other backend serves. */
@RestController
public class WorkloadController {

    private final WorkItemService service;

    /**
     * Dependencies arrive through the constructor, so the object cannot exist in a
     * half-wired state and the field can be final. A single constructor needs no
     * @Autowired — the container infers it. Field injection would hide this dependency
     * from every caller and leave the class untestable without a container.
     *
     * Constructor injection is demonstrated here rather than on the service, whose
     * constructor three other tests must call to build their fixtures: breaking a
     * constructor every test needs could never produce a failure that names one thing.
     */
    public WorkloadController(WorkItemService service) {
        this.service = service;
    }

    @GetMapping("/workload")
    public Map<String, Map<String, Integer>> workload() {
        return Map.of("byAssignee", service.workload());
    }
}
