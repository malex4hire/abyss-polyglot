"""Executable proof that the grouping is built by a comprehension rather than by an
accumulator loop, a difference only the compiled form makes visible."""

from __future__ import annotations

import pytest

from app.queries import titles_by_assignee


@pytest.mark.comprehensions
def test_the_shape_of_the_result_is_visible_in_the_expression(sample):
    """The result's shape is visible in the expression: sorted keys, list values."""
    grouped = titles_by_assignee(sample)
    assert list(grouped) == ["avery", "briar", "casey"], "keys arrive sorted"
    assert grouped["avery"] == ["title-WI-1"]
    assert all(isinstance(v, list) for v in grouped.values())


@pytest.mark.comprehensions
def test_the_value_is_built_by_a_comprehension_and_not_by_an_accumulator(sample):
    """The grouping is built by a comprehension, which only the bytecode can show.

    The assertions above are about the value, and an accumulator loop with setdefault
    produces exactly that value, which is how a counter passed them. A comprehension is
    not a different result, it is a different statement about what the loop is for, so the
    only place the difference is observable is the compiled form.

    An assertion that cannot distinguish the mechanism from its plainer alternative is
    worth relaxing only when the mechanism leaves no detectable mark at any layer the
    test can reach, compiled output included. This one does leave a mark: building a
    collection by comprehension emits MAP_ADD, LIST_APPEND or SET_ADD, and a loop calling
    .append() or .setdefault() emits ordinary attribute loads and calls instead.
    """
    import dis
    import io

    listing = io.StringIO()
    dis.dis(titles_by_assignee, file=listing)
    text = listing.getvalue()

    assert any(op in text for op in ("MAP_ADD", "LIST_APPEND", "SET_ADD")), (
        "the collection is built by a comprehension, which is the point; an "
        "accumulator loop produces the same dict and none of these opcodes"
    )
