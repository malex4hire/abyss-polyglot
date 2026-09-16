#!/usr/bin/env python3
"""Restore the demo to seed state, without deleting anything.

Browser checks drive the real application against the real database, which is what makes
them worth having and also what makes them destructive: every run creates items and
archives others, so the demo degrades a little each time it is shown. The fix
belongs here rather than in the checks, because a cleanup step each check has to remember
is a cleanup step some check will forget.

Archive is soft delete and there are no hard deletes anywhere in this repository, so this
does not remove rows. It restores the seed rows to their seeded values and un-archives
them, and soft-deletes anything that was not seeded. A row created by a check stays in the
table with a timestamp on it, which is the same thing the application does when a person
archives an item.

The in-memory backends are not touched here: they build their state from the seed file at
startup, so restarting them is the reset, and this does that.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "modules" / "java-modern" / "src" / "main" / "resources" / "seed.csv"
MANIFEST = ROOT / "stacks" / "manifest.yaml"

# Schema per backend module. Which schemas exist is read from the database rather than
# listed here, so a backend that gains one is covered without editing this file.
SCHEMA_QUERY = (
    "select table_schema from information_schema.tables "
    "where table_name = 'work_item' and table_schema not in "
    "('pg_catalog','information_schema') order by 1;"
)


def psql(sql: str) -> str:
    done = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres",
         "psql", "-U", "polyglot", "-d", "polyglot", "-tA", "-c", sql],
        capture_output=True, text=True, cwd=ROOT, timeout=120,
    )
    if done.returncode != 0:
        raise SystemExit(f"demo-reset: psql failed:\n{done.stderr.strip()}")
    return done.stdout.strip()


def seed_rows() -> list[dict]:
    with SEED.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def restore_schema(schema: str, rows: list[dict]) -> tuple[int, int]:
    ids = ", ".join(quote(row["id"]) for row in rows)

    restored = 0
    for row in rows:
        # Upsert rather than insert-or-skip: a check may have transitioned a seed item, and
        # a reset that only un-archives would leave it in the wrong state.
        psql(
            f"insert into {schema}.work_item "
            "(id, title, status, priority, assignee, tags, created_at, updated_at, archived_at) "
            f"values ({quote(row['id'])}, {quote(row['title'])}, {quote(row['status'])}, "
            f"{int(row['priority'])}, {quote(row['assignee'])}, {quote(row['tags'])}, "
            "now(), now(), null) "
            "on conflict (id) do update set "
            "title = excluded.title, status = excluded.status, priority = excluded.priority, "
            "assignee = excluded.assignee, tags = excluded.tags, updated_at = now(), "
            "archived_at = null"
        )
        restored += 1

    # Everything else is soft-deleted, never removed. A check's leftovers stay auditable.
    archived = psql(
        f"with touched as (update {schema}.work_item set archived_at = now() "
        f"where id not in ({ids}) and archived_at is null returning 1) "
        "select count(*) from touched;"
    )
    return restored, int(archived or 0)


def main() -> int:
    if not SEED.is_file():
        raise SystemExit(f"demo-reset: no seed file at {SEED}")
    rows = seed_rows()

    schemas = [line for line in psql(SCHEMA_QUERY).splitlines() if line.strip()]
    for schema in schemas:
        restored, archived = restore_schema(schema, rows)
        print(f"  {schema}: {restored} seed rows restored, {archived} extra rows archived")

    # The in-memory backends rebuild from the seed file at startup.
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    in_memory = [
        stack["service"]
        for stack_id, stack in (manifest.get("stacks") or {}).items()
        if stack.get("active") and stack.get("role") == "backend" and stack.get("service")
        and stack_id not in {s.replace("_", "-") for s in schemas}
    ]
    if in_memory:
        subprocess.run(["docker", "compose", "restart", *in_memory],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
        print(f"  restarted (seed rebuilt at startup): {', '.join(in_memory)}")

    print("demo restored to seed state")
    return 0


if __name__ == "__main__":
    sys.exit(main())
