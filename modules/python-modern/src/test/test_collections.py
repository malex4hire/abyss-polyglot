"""Executable proof that the repository preserves insertion order, filters archived
items out of a live read, and hands back a copy rather than its own list."""

from __future__ import annotations

import pytest

from app.repository import Repository
from app.work_item import archived
from datetime import datetime, timezone


@pytest.mark.collections
def test_insertion_order_is_part_of_the_contract(sample):
    """Insertion order survives, archived items are excluded, and the result is a copy."""
    repo = Repository()
    for item in reversed(sample):
        repo.put(item)
    repo.put(archived(sample[0], datetime(2026, 2, 1, tzinfo=timezone.utc)))

    live = repo.live()

    assert [i.id for i in live] == ["WI-3", "WI-2"], "order preserved, archived excluded"
    live.append(sample[0])
    assert len(repo.live()) == 2, "the returned list is a copy"
