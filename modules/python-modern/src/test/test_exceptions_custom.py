"""Executable proof that a custom exception carries the data that caused it, so a
handler can read the refusal off the object instead of parsing its message."""

from __future__ import annotations

import pytest

from app.errors import TransitionRefused
from app.status import Status


@pytest.mark.exceptions_custom
def test_the_failure_is_programmable_not_only_printable():
    """The refused transition is readable as attributes, not only as text."""
    error = TransitionRefused(Status.DONE, Status.OPEN)
    assert isinstance(error, Exception)
    assert error.frm is Status.DONE, "the cause is readable off the object"
    assert error.to is Status.OPEN
    assert "DONE cannot move to OPEN" in str(error)
