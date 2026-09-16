"""Shared fixtures for the module's own tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.status import Status
from app.work_item import WorkItem

AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make(item_id: str, status: Status = Status.OPEN, priority: int = 5,
         assignee: str = "avery", tags: tuple[str, ...] = ()) -> WorkItem:
    """Build a fixture directly.

    Tests build their own inputs rather than borrowing from the code another test
    covers, so a failure names the thing that actually broke.
    """
    return WorkItem(id=item_id, title=f"title-{item_id}", status=status,
                    priority=priority, assignee=assignee,
                    created_at=AT, updated_at=AT, tags=tags, archived_at=None)


@pytest.fixture
def sample() -> list[WorkItem]:
    return [
        make("WI-1", Status.OPEN, 5, "avery", ("backend",)),
        make("WI-2", Status.IN_PROGRESS, 9, "briar", ("backend", "parser")),
        make("WI-3", Status.OPEN, 2, "casey", ("docs",)),
    ]
