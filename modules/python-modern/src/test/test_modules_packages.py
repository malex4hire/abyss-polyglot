"""Executable proof that the package inventory is discovered from the filesystem,
so it cannot drift from what is actually on disk."""

from __future__ import annotations

import pytest

from app.packaging import own_modules


@pytest.mark.modules_packages
def test_the_inventory_comes_from_the_filesystem():
    """The reported module list matches an independent walk of the package."""
    modules = own_modules()

    # Compared against an independent walk of the package rather than against two names
    # this test also knows. Naming a few modules is satisfied by any list containing them,
    # including a hand-written one that has quietly stopped matching the directory, which
    # is the failure discovering the list from disk makes impossible.
    import pkgutil

    import app

    discovered = sorted(
        module.name for module in pkgutil.iter_modules(app.__path__)
    )

    assert modules == discovered, (
        "the inventory is the directory, so anything present is found without being "
        f"remembered: reported {modules}, on disk {discovered}"
    )
