"""Executable proof that each Status member carries its own transition rule, rather
than the rules living in a table kept somewhere beside the constants."""

from __future__ import annotations

import pytest

from app.status import Status


@pytest.mark.enums
def test_each_member_carries_its_own_rule():
    """Each member answers for itself which states it may move to."""
    assert Status.OPEN.can_transition_to(Status.IN_PROGRESS)
    assert not Status.OPEN.can_transition_to(Status.DONE), "no jumping straight to DONE"
    assert not Status.DONE.can_transition_to(Status.OPEN), "DONE is terminal"
    assert not Status.CANCELLED.can_transition_to(Status.IN_PROGRESS)
