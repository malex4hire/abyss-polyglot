package com.abyss.polyglot.springtraditional;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

/** Persistence, on JdbcTemplate. No JPA, no repository derivation: SQL is written out. */
@Repository
public class WorkItemRepository {

    private static final String COLUMNS =
            "id, title, status, priority, assignee, created_at, updated_at, tags, archived_at";

    private final JdbcTemplate jdbc;

    public WorkItemRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    private static final RowMapper<WorkItem> MAPPER = (ResultSet rs, int row) -> new WorkItem(
            rs.getString("id"),
            rs.getString("title"),
            Status.valueOf(rs.getString("status")),
            rs.getInt("priority"),
            rs.getString("assignee"),
            rs.getTimestamp("created_at").toInstant(),
            rs.getTimestamp("updated_at").toInstant(),
            rs.getString("tags").isBlank() ? List.of() : Arrays.asList(rs.getString("tags").split(";")),
            rs.getTimestamp("archived_at") == null ? null : rs.getTimestamp("archived_at").toInstant());

    /**
     * Query through JdbcTemplate. The SQL is visible, the RowMapper says exactly how a
     * row becomes an object, and the template handles the connection, the statement, the
     * result set and the close, which is the boilerplate, not the intent. Compare Boot's
     * spring-data-jpa-repository, where a method name generates the query and the SQL
     * is never written at all.
     */
    public List<WorkItem> findAll() {
        return jdbc.query(
                "SELECT " + COLUMNS + " FROM spring_traditional.work_item "
                        + "WHERE archived_at IS NULL ORDER BY priority DESC, title ASC",
                MAPPER);
    }

    public Optional<WorkItem> findById(String id) {
        List<WorkItem> found = jdbc.query(
                "SELECT " + COLUMNS + " FROM spring_traditional.work_item WHERE id = ?", MAPPER, id);
        return found.isEmpty() ? Optional.empty() : Optional.of(found.get(0));
    }

    /**
     * B5. Returns rows written: 1 for an insert, 0 when the key was already there.
     *
     * The ON CONFLICT clause was already here and the update count was thrown away, so the
     * database refused the duplicate and the API reported a creation anyway. A guard whose
     * result nobody reads is not a guard.
     */
    public int insert(WorkItem item) {
        return jdbc.update("""
                INSERT INTO spring_traditional.work_item
                  (id, title, status, priority, assignee, created_at, updated_at, tags, archived_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT (id) DO NOTHING""",
                item.id(), item.title(), item.status().name(), item.priority(), item.assignee(),
                java.sql.Timestamp.from(item.createdAt()), java.sql.Timestamp.from(item.updatedAt()),
                String.join(";", item.tags()));
    }

    /**
     * B5. Compare and set: the status the caller decided against is part of the WHERE
     * clause, so the check and the write are one statement rather than two. Zero rows
     * affected means the row was not in the expected state: already moved, by this
     * caller's own retry or by somebody else.
     */
    public int updateStatus(String id, Status expected, Status status, Instant at) {
        return jdbc.update("""
                UPDATE spring_traditional.work_item
                   SET status = ?, updated_at = ?
                 WHERE id = ? AND status = ?""",
                status.name(), java.sql.Timestamp.from(at), id, expected.name());
    }

    public void archive(String id, Instant at) {
        jdbc.update("UPDATE spring_traditional.work_item SET archived_at = ?, updated_at = ? WHERE id = ?",
                java.sql.Timestamp.from(at), java.sql.Timestamp.from(at), id);
    }
}
