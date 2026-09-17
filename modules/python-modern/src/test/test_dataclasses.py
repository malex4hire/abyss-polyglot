"""Executable proof that a frozen dataclass is derived rather than mutated, that its
equality and field set are generated, and that replace() reads that set off the type."""

from __future__ import annotations

import pytest

from dataclasses import FrozenInstanceError, dataclass

from app.status import Status
from app.work_item import evolve


@pytest.mark.dataclasses
def test_frozen_means_derive_rather_than_mutate(sample):
    """Frozen refuses assignment; evolve() derives a new value and leaves the original."""
    item = sample[0]
    with pytest.raises(FrozenInstanceError):
        item.priority = 99

    derived = evolve(item, priority=99)

    assert derived.priority == 99, "the change lands on the new value"
    assert item.priority == 5, "and the original is untouched"
    assert derived.id == item.id, "every other field carried across"
    # Was `item == sample[0]`, which is `x == x`, true of every object in Python,
    # including one with no __eq__ at all. Componentwise equality is only visible against
    # a separately constructed instance carrying the same values.
    twin = evolve(item)
    assert twin is not item, "a distinct object"
    assert twin == item, "equality is componentwise and generated, not identity"
    assert not hasattr(item, "__dict__"), "slots dropped the per-instance dict"
    with pytest.raises(TypeError):
        evolve(item, nonexistent=1)

    # Everything above is also satisfied by field-by-field reconstruction through the
    # constructor, which is the spelling this replaces. What dataclasses.replace
    # supplies that a hand-rolled version cannot is that it reads the field set off the
    # type at call time, so it derives any dataclass without being told its fields, and
    # keeps working when a field is added to WorkItem, which a hand-rolled list does not.
    @dataclass(frozen=True)
    class Other:
        left: int
        right: str

    other = evolve(Other(1, "a"), right="b")
    assert (other.left, other.right) == (1, "b"), \
        "the field set comes from the type, not from a list written out by hand"
