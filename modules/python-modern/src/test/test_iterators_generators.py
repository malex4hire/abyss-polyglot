"""Executable proof that pages are produced on demand by a generator, so stopping
early does no work for the pages nobody asked for."""

from __future__ import annotations

import pytest

from app.repository import Repository


@pytest.mark.iterators_generators
def test_pages_are_produced_on_demand(sample):
    """Paging suspends and resumes rather than building the whole result first."""
    repo = Repository()

    pages = repo.pages(2, sample)
    # hasattr(__next__) is true of any iterator, including one over a list that was
    # built in full first — which is what a counter returned. Laziness is the whole
    # point, so the assertion names it: the function suspends and resumes rather
    # than returning a finished collection.
    import inspect

    assert inspect.isgenerator(pages), (
        "a generator, not an iterator over a list somebody already built: "
        f"{type(pages).__name__}"
    )
    assert [len(p) for p in pages] == [2, 1], "the tail page is not padded"

    first = next(repo.pages(1, sample))
    assert len(first) == 1, "stopping early does no work for the rest"
