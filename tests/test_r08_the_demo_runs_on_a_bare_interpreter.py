"""R-8: `python3 demo.py` works with nothing installed.

This is the repository's first line and its strongest claim, so it is the one most worth
checking mechanically. "Runs with nothing installed" decays the moment somebody adds an
import for convenience, and it decays silently: it keeps working on the machine of
everybody who already has the package.

Three things are checked, and the third is the one that actually settles it.

1. Neither demo.py nor the backend it starts imports anything outside the standard
   library. Read from the source, so it fails at the moment the import is added.
2. requirements.txt does not pin a runtime dependency. A pin nothing imports is worse
   than a missing one: it is a declaration that the module needs something it does not,
   and it stood in this repository for the life of the build.
3. The script is run with site-packages disabled, so nothing installed on this machine
   can satisfy an import. That is the only version of this claim that cannot be true by
   accident.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import time

import pytest

import spine

PYTHON_BACKEND = "python-modern"


def _stdlib_names() -> set[str]:
    names = set(getattr(sys, "stdlib_module_names", ()))
    if not names:
        pytest.fail(
            "this interpreter does not expose sys.stdlib_module_names, so the "
            "standard-library-only claim cannot be checked by reading"
        )
    return names


def _top_level_imports(path) -> set[str]:
    tree = ast.parse(spine.text_of(path), filename=str(path))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # a relative import stays inside the package
                continue
            if node.module:
                found.add(node.module.split(".")[0])
    return found


def _backend_stack() -> tuple[str, dict]:
    stacks = {
        sid: s for sid, s in spine.active_stacks().items()
        if s.get("language") == "python" and s.get("role") == "backend"
    }
    if len(stacks) != 1:
        pytest.fail(
            f"expected exactly one active python backend, found {sorted(stacks) or 'none'}"
        )
    sid = next(iter(stacks))
    return sid, stacks[sid]


def test_the_walkthrough_imports_only_the_standard_library():
    spine.require_file(spine.DEMO, "demo.py")
    outside = sorted(_top_level_imports(spine.DEMO) - _stdlib_names())
    assert not outside, (
        "demo.py imports outside the standard library: " + ", ".join(outside)
        + ". The first command in the README promises no install; an import here breaks it"
    )


def test_the_backend_the_walkthrough_starts_imports_only_the_standard_library():
    """Its own package is not a third-party import; anything else is."""
    sid, stack = _backend_stack()
    root = spine.source_root(sid, stack)
    spine.require_dir(root, f"{sid} source root")

    # The package's own name, read from the tree rather than typed.
    own = {p.name for p in root.iterdir() if p.is_dir() and (p / "__init__.py").exists()}
    assert own, f"no importable package under {spine._rel(root)}"

    allowed = _stdlib_names() | own
    offenders = []
    for path in spine.iter_repo_files((".py",), root=root):
        # The module's own test suite may use pytest; the server may not.
        if "test" in path.relative_to(root).parts:
            continue
        for name in sorted(_top_level_imports(path) - allowed):
            offenders.append(f"{spine._rel(path)}: {name}")
    assert not offenders, (
        "the python backend imports outside the standard library:\n  " + "\n  ".join(offenders)
        + "\n\nThis module is in-memory and standard-library-only on purpose; that is what "
        "lets demo.py run with no install."
    )


def test_no_runtime_dependency_is_pinned_that_nothing_imports():
    """A pin nothing imports is a declaration the module needs something it does not.

    A database driver sat in this file, and in the manifest's required_artifacts, for the
    life of the build. Nothing imported it. It cost an image layer, a wheel build and a
    false statement about what the module is.
    """
    sid, stack = _backend_stack()
    requirements = spine.source_root(sid, stack).parent / "requirements.txt"
    spine.require_file(requirements, f"{sid} requirements.txt")

    pinned = set()
    for line in spine.text_of(requirements).splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        name = re.split(r"[\[<>=!~;]", line)[0].strip().lower()
        if name:
            pinned.add(name)

    # pytest is the module's own test runner, declared and used by its test suite. Read
    # from the tree rather than exempted by name.
    test_root = spine.REPO_ROOT / spine.stack_field(sid, stack, "test_root")
    test_imports = set()
    for path in spine.iter_repo_files((".py",), root=test_root):
        test_imports |= {n.lower() for n in _top_level_imports(path)}

    src_imports = set()
    for path in spine.iter_repo_files((".py",), root=spine.source_root(sid, stack)):
        src_imports |= {n.lower() for n in _top_level_imports(path)}

    unused = sorted(pinned - src_imports - test_imports)
    assert not unused, (
        f"{spine._rel(requirements)} pins dependencies nothing imports: "
        + ", ".join(unused)
        + ". Remove them, or the module is carrying a claim about itself that is false"
    )

    declared = stack.get("required_artifacts") or []
    assert not [a for a in declared if str(a).lower() in unused], (
        "the manifest declares a required artifact the module does not import"
    )


@pytest.mark.slow
def test_the_walkthrough_completes_with_site_packages_disabled():
    """-S, so nothing installed on this machine can satisfy an import.

    The check above reads the source and is the fast one. This one is the evidence: a
    conditional import, an import inside a function, a package vendored into the tree.
    None of those are caught by reading, and all of them break the promise on a stranger's
    laptop. It is also the only test here that exercises the walkthrough at all.
    """
    spine.require_file(spine.DEMO, "demo.py")

    process = subprocess.Popen(
        [sys.executable, "-S", "-I", str(spine.DEMO)],
        cwd=spine.REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env={**os.environ, "TERM": "dumb"},
    )
    lines: list[str] = []
    # A wall clock as well as a marker. The walkthrough blocks on purpose once it hands the
    # server over, so reading to EOF would hang, and a version of this that waited only
    # for the marker DID hang, for a reason worth keeping: a redirected stdout is
    # block-buffered, so the final line never left the child's buffer. The deadline turns
    # that class of failure into a report instead of a stuck run.
    deadline = time.monotonic() + 120
    try:
        assert process.stdout is not None
        for line in process.stdout:
            lines.append(line)
            if "Ctrl-C to stop" in line:
                break
            if len(lines) > 600 or time.monotonic() > deadline:
                break
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    output = "".join(lines)
    assert "Ctrl-C to stop" in output, (
        "the walkthrough did not run to completion with site-packages disabled:\n"
        + output[-3000:]
    )
    # Each numbered step in the walkthrough must have been reached. The steps are counted
    # from what printed rather than declared here, so adding one needs no edit.
    reached = re.findall(r"^\d+\. ", output, re.M)
    assert len(reached) >= 7, (
        f"only {len(reached)} walkthrough steps printed; the walk stopped early:\n"
        + output[-3000:]
    )
    assert "EXPECTED" not in output, (
        "the walkthrough printed an unmet expectation, which means the backend answered "
        "something the contract does not allow:\n" + output[-3000:]
    )
