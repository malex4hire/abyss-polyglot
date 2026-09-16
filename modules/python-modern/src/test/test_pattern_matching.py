"""Executable proof that match destructures the workflow result and that a guarded
case is tried before the general one it would otherwise be swallowed by."""

from __future__ import annotations

import pytest

from datetime import datetime, timezone

from app.status import Status
from app.workflow import Applied, Rejected, status_code_for
from app.work_item import archived


@pytest.mark.pattern_matching
def test_match_destructures_and_guards(sample):
    """One match statement destructures each outcome and guards the archived case."""
    live = sample[0]
    assert status_code_for(Applied(live)) == 200
    assert status_code_for(Applied(archived(live, datetime(2026, 3, 1, tzinfo=timezone.utc)))) == 409, \
        "the guarded case matches before the general one"
    assert status_code_for(Rejected(Status.DONE, Status.OPEN, "terminal")) == 422
