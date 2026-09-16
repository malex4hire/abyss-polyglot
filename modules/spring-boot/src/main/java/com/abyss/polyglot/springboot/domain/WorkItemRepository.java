package com.abyss.polyglot.springboot.domain;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * Persistence with no implementation.
 *
 * This is an interface. Nothing in this module implements it: Spring Data builds a proxy
 * at startup and derives the query from the method name.
 */
public interface WorkItemRepository extends JpaRepository<WorkItemEntity, String> {

    /**
     * B5. Compare and set, in one statement.
     *
     * Derived-name queries cannot express "update only if", so this is the point where the
     * framework stops writing the query for you and the pair contrast inverts: the
     * traditional module writes SQL for everything and this one writes SQL exactly where
     * the convention runs out. The precondition is in the WHERE clause, so the check and
     * the write cannot be separated by another caller, and the row count is the answer.
     */
    @org.springframework.transaction.annotation.Transactional
    @org.springframework.data.jpa.repository.Modifying(clearAutomatically = true, flushAutomatically = true)
    @org.springframework.data.jpa.repository.Query("""
            update WorkItemEntity w
               set w.status = :next, w.updatedAt = :at
             where w.id = :id and w.status = :expected""")
    int moveStatus(@org.springframework.data.repository.query.Param("id") String id,
                   @org.springframework.data.repository.query.Param("expected") Status expected,
                   @org.springframework.data.repository.query.Param("next") Status next,
                   @org.springframework.data.repository.query.Param("at") java.time.Instant at);

    /**
     * The query is the method name. It parses into a where clause and an order clause,
     * and the SQL is generated at startup. There is no body here because there is no
     * implementation here — that is the feature.
     */
    List<WorkItemEntity> findByArchivedAtIsNullOrderByPriorityDescTitleAsc();

    /**
     * The derived query, called by name.
     *
     * This default method exists to give the derived query a call site. The declaration
     * above it has no body to read at all, which is precisely the feature: the method
     * name IS the query, so the name is the only thing there is to get right. Get one
     * word of "ArchivedAtIsNull" or "OrderByPriorityDescTitleAsc" wrong and Spring Data
     * either derives a different query or refuses to start.
     *
     * The traditional module writes the same query as SQL with a RowMapper beside it.
     * That one is longer and says exactly what runs; this one is a name and says what is
     * wanted. The cost shows up when the derived query is wrong, because there is no SQL
     * to read — only a name to re-parse in your head.
     */
    default List<WorkItemEntity> liveByPriority() {
        return findByArchivedAtIsNullOrderByPriorityDescTitleAsc();
    }
}
