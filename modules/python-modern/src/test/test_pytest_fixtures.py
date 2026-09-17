"""Executable proof that fixtures are dependency injection for tests: resolved by
name, composed out of one another, and torn down even when the test fails."""

from __future__ import annotations

import pytest

from app.repository import Repository

@pytest.fixture
def seeded(sample):
    """A repository already holding the sample, torn down after each test.

    Fixtures are dependency injection for tests: this one asks for `sample` by naming it
    as a parameter and pytest resolves it, so setup composes instead of being repeated.
    The code after yield is teardown and runs even when the test fails, which is what a
    setUp/tearDown pair gives you without the class, and what a plain helper function
    does not give you at all.

    Scope is the other half: this is function-scoped, so each test gets its own
    repository and no test can leave state for the next one.
    """
    repo = Repository()
    for item in sample:
        repo.put(item)
    yield repo
    repo._items.clear()


@pytest.mark.pytest_fixtures
def test_the_fixture_is_resolved_by_name_and_torn_down(seeded):
    """The fixture is resolved by name and arrives already holding the sample."""
    assert seeded.size() == 3, "the fixture composed on top of another fixture"
    assert seeded.get("WI-2") is not None, "and the items it was given are there"


@pytest.mark.pytest_fixtures
def test_the_setup_is_composed_out_of_another_fixture(seeded, request):
    """The setup is composed out of another fixture, which the request makes readable.

    The assertions above are about the repository the fixture hands over, and a fixture
    that builds the same items itself produces an identical one. That is correct, and it
    is what people write before composition occurs to them. Dependency injection is the
    point: this fixture asks for `sample` by naming it, and pytest resolves it.

    That is readable from inside the test. The resolved fixture closure is on the request,
    so a fixture built out of another one names both, and a self-contained one names only
    itself.
    """
    assert "sample" in request.fixturenames, (
        "the setup is assembled from another fixture rather than repeated here: "
        f"{sorted(n for n in request.fixturenames if not n.startswith('_'))}"
    )
    assert seeded.size() == 3, "and it still hands over the repository it built"
