"""Executable proof that rendering goes through the language's own protocol methods —
len() dispatching to __len__ — rather than through a loop that reaches the same number."""

from __future__ import annotations

import pytest

from app.work_item import describe


@pytest.mark.classes_dunder
def test_the_type_speaks_the_language_s_own_vocabulary(sample):
    """The rendered form is assembled from the item's own fields and its tag count."""
    rendered = describe(sample[1])
    assert rendered.startswith("WI-2: title-WI-2")
    assert "[IN_PROGRESS]" in rendered
    assert "p9" in rendered
    assert "(2 tags)" in rendered, "len() reached the tuple's __len__"


@pytest.mark.classes_dunder
def test_the_protocol_methods_are_what_get_called(sample):
    """The count comes from len() dispatching to __len__, not from a counting loop.

    The assertions above are about the rendered string, and a version that reaches into
    the object and counts with a loop produces it exactly — which is how a counter passed
    them. The existing comment already named the mechanism, "len() reached the tuple's
    __len__", and nothing was checking it.

    So the tags are handed over as an object that records the protocol call. Dispatch
    through __len__ is what is being shown; iterating to count is the alternative that
    looks the same from outside.
    """
    import dataclasses

    calls: list[str] = []

    class RecordingTags(tuple):
        def __len__(self):
            calls.append("__len__")
            return super().__len__()

    item = dataclasses.replace(sample[1], tags=RecordingTags(sample[1].tags))
    rendered = describe(item)

    assert "(2 tags)" in rendered, "the count still renders correctly"
    assert "__len__" in calls, (
        "the count came from len() dispatching to the type, not from a loop that "
        "arrived at the same number"
    )
