"""Executable proof that parametrize expands one function into a case per row, each
with its own id, rather than running a loop inside a single test."""

from __future__ import annotations

import pytest

from app.workload import group_by_assignee
from app.status import Status
from test.conftest import make

@pytest.mark.pytest_parametrize
@pytest.mark.parametrize(
    ("assignees", "expected_groups"),
    [
        ("avery", 1),
        ("avery;avery", 1),
        ("avery;briar", 2),
        ("avery;briar;avery", 2),
        ("avery;briar;casey", 3),
    ],
    ids=["one", "repeat", "two", "repeat-of-two", "three"],
)
def test_grouping(assignees, expected_groups, request):
    """Each row runs as its own case, bound to the parameters by name.

    One function, one case per row. Each row is a separate test with its own id, so a
    failure names the case rather than the loop that contained it, and the ids make the
    report readable instead of a list of tuples. A for-loop over the same data reports one
    failure and stops at the first bad row.
    """
    names = assignees.split(";")
    items = [make(f"WI-{i}", Status.OPEN, 1, name) for i, name in enumerate(names)]

    assert len(group_by_assignee(items)) == expected_groups

    # A test cannot count its own invocations, which is why this was conceded — but it can
    # ask what it was invoked with. The collector attaches a callspec when it expands a
    # parametrised function into cases, and never when a test loops over rows itself.
    assert getattr(request.node, "callspec", None) is not None, (
        "this ran as one case of an expanded set, not as a loop inside one test"
    )
    assert set(request.node.callspec.params) == {"assignees", "expected_groups"}, (
        f"and the row is bound to the parameters by name: {request.node.callspec.params}"
    )
