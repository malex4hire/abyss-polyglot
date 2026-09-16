package com.abyss.polyglot.springtraditional;

import org.springframework.jdbc.core.JdbcTemplate;

/**
 * Schema and seed, per-module schema (Additional Constraints). Archive is a soft delete:
 * archived_at is set, the row stays. No hard deletes anywhere in this repo.
 */
public class SchemaInitializer {

    private final JdbcTemplate jdbc;

    public SchemaInitializer(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public void initialize() {
        jdbc.execute("CREATE SCHEMA IF NOT EXISTS spring_traditional");
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS spring_traditional.work_item (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INT NOT NULL,
                    assignee TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    tags TEXT NOT NULL,
                    archived_at TIMESTAMPTZ
                )""");
        Integer rows = jdbc.queryForObject(
                "SELECT count(*) FROM spring_traditional.work_item", Integer.class);
        if (rows != null && rows == 0) {
            seed();
        }
    }

    private void seed() {
        Object[][] rows = {
            {"WI-001", "Migrate batch scheduler", "OPEN", 5, "avery", "backend;legacy"},
            {"WI-002", "Rewrite claims parser", "IN_PROGRESS", 8, "briar", "backend;parser"},
            {"WI-003", "Retire SOAP endpoint", "OPEN", 3, "avery", "legacy"},
            {"WI-004", "Add audit trail export", "BLOCKED", 6, "casey", "audit"},
            {"WI-005", "Tune connection pool", "IN_PROGRESS", 7, "briar", "backend;performance"},
            {"WI-006", "Document transition rules", "OPEN", 2, "casey", "docs"},
        };
        for (Object[] row : rows) {
            jdbc.update("""
                    INSERT INTO spring_traditional.work_item
                      (id, title, status, priority, assignee, created_at, updated_at, tags, archived_at)
                    VALUES (?, ?, ?, ?, ?, now(), now(), ?, NULL)""",
                    row[0], row[1], row[2], row[3], row[4], row[5]);
        }
    }
}
