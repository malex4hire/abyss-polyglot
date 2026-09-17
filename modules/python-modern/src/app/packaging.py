"""How this program finds its own parts."""

from __future__ import annotations

import importlib
import pkgutil


def own_modules() -> list[str]:
    """The modules this package contains, discovered rather than listed.

    A package is a directory the import system understands, and pkgutil walks it, so the
    inventory comes from the filesystem instead of a list someone maintains. import_module
    resolves a name to a loaded module through the same machinery an import statement
    uses, which is what makes the reported set the one actually importable, not the one
    someone believed was there.
    """
    package = importlib.import_module(__package__)
    return sorted(
        info.name for info in pkgutil.iter_modules(package.__path__)
    )
