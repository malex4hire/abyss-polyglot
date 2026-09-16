"""Executable proof that a batch's teardown runs on both exits — applying the staged
writes on a clean exit and dropping them on an exception — from one function."""

from __future__ import annotations

import dataclasses

import pytest

from app.repository import Repository


@pytest.mark.context_managers
def test_teardown_runs_on_both_exits(sample):
    """A clean exit applies the staged writes; an exception drops them entirely."""
    repo = Repository()

    with repo.batch() as staged:
        staged.extend(sample)
    assert repo.size() == 3, "a clean exit applies the staged writes"

    with pytest.raises(RuntimeError):
        with repo.batch() as staged:
            staged.append(sample[0])
            raise RuntimeError("boom")
    assert repo.size() == 3, "an exception drops them rather than half-applying"


@pytest.mark.context_managers
def test_teardown_runs_when_the_block_raises(sample):
    """`with` receives contextlib's own manager, so setup and teardown are one function.

    The point is that one function reads as setup, the block, then teardown, with the
    two halves of the lifecycle in one place — not that a lifecycle exists. A class
    implementing __enter__ and __exit__ by hand is behaviourally identical on both exits,
    so nothing about what ends up in the repository can tell them apart.

    What can is the object `with` receives: the decorator wraps a generator function and
    hands back contextlib's own manager, and a hand-rolled class does not. That is the
    mark that distinguishes the two — one layer away from the behaviour, and readable.
    """
    import contextlib
    import inspect

    repo = Repository()
    manager = repo.batch()

    assert type(manager).__module__ == contextlib.__name__, (
        "the decorator supplies the manager, so setup and teardown are one function "
        f"read top to bottom: got {type(manager).__module__}.{type(manager).__name__}"
    )
    assert inspect.isgenerator(manager.gen), (
        "and it is driven by a generator — the yield is where the block runs"
    )
    manager.gen.close()
