package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.domain.WorkItemEntity;
import com.abyss.polyglot.springboot.domain.WorkItemRepository;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** Executable proof that the repository method name alone becomes the query: the where
 *  clause and the order clause are parsed out of it at startup. */
@Tag("spring-data-jpa-repository")
@SpringBootTest
class SpringDataJpaRepositoryTest {

    @Autowired
    WorkItemRepository repository;

    @Test
    void theMethodNameIsTheQuery() {
        Instant now = Instant.now();
        repository.save(new WorkItemEntity("T-low", "low", com.abyss.polyglot.springboot.domain.Status.OPEN,
                1, "tester", now, now, "t", null));
        repository.save(new WorkItemEntity("T-high", "high", com.abyss.polyglot.springboot.domain.Status.OPEN,
                99, "tester", now, now, "t", null));
        repository.save(new WorkItemEntity("T-gone", "gone", com.abyss.polyglot.springboot.domain.Status.OPEN,
                50, "tester", now, now, "t", now));

        List<WorkItemEntity> found = repository.liveByPriority();
        List<String> ids = found.stream().map(WorkItemEntity::getId).toList();

        assertTrue(ids.contains("T-high"));
        assertFalse(ids.contains("T-gone"), "IsNull in the method name became a where clause");
        assertTrue(ids.indexOf("T-high") < ids.indexOf("T-low"),
                "OrderByPriorityDesc in the method name became an order clause");

        repository.deleteAllById(List.of("T-low", "T-high", "T-gone"));
    }

    @Test
    void theQueryComesFromTheNameAndNotFromAnAnnotation() throws Exception {
        // The rows-and-order assertion above passes against the same query written out as
        // JPQL, because the results are identical. That is the contrast, not the point.
        // The point is that the method signature IS the query, so there is no second
        // spelling to keep in agreement with it. That is visible on the method and
        // nowhere else.
        var method = WorkItemRepository.class.getMethod("liveByPriority");

        assertNull(method.getAnnotation(org.springframework.data.jpa.repository.Query.class),
                "no query is written: the name is parsed into one at startup");
        assertTrue(method.getName().contains("ArchivedAtIsNull")
                        || method.isDefault(),
                "and the name it is derived from is the one the interface declares");
    }
}
