"""Executable proof that annotations state what a function takes and gives back,
and survive to runtime where a type checker can read them."""

from __future__ import annotations

import pytest

from app.queries import matching
from app.status import Status


@pytest.mark.type_hints
def test_absent_criteria_are_part_of_the_signature(sample):
    """Optional criteria are part of the signature, so absent means no filtering."""
    assert len(matching(sample, None, None)) == 3, "both absent means no filtering"
    assert [i.id for i in matching(sample, Status.OPEN, None)] == ["WI-1", "WI-3"]
    assert [i.id for i in matching(sample, None, "docs")] == ["WI-3"]
    assert matching(sample, Status.DONE, None) == []


@pytest.mark.type_hints
def test_the_signature_states_its_intent_where_a_checker_can_read_it():
    """The annotations are kept at runtime, so a checker can read the same claim.

    This one is not assertable at runtime, on the reasoning
    that Python does not enforce annotations, which is true and is not the same claim.
    Nothing enforces them, but they are kept: `__annotations__` holds them and
    `typing.get_type_hints` resolves them, which is exactly how a checker reads them.

    So it is observable after all, and the counter that proved it is the same
    function with its annotations stripped: identical behaviour, identical results, and a
    signature that has stopped saying anything.
    """
    import typing

    hints = typing.get_type_hints(matching)

    assert "return" in hints, "the function states what it gives back"
    assert {"items", "status", "tag"} <= set(hints), (
        f"every parameter states what it takes: {sorted(hints)}"
    )
    assert type(None) in typing.get_args(hints["status"]), (
        "and absence is in the type rather than left to a convention: "
        f"{hints['status']}"
    )
