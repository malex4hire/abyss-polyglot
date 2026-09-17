"""R-4: one unmodified contract suite, run against every active backend, passing
identically.

The scope of this file is the BACKENDS, and saying so is the point.

An earlier version of this docstring claimed the contract was "consumed unmodified by
every frontend" as well. Every test under it exercised backends only. Nobody had lied on
purpose: the sentence was written when the suite was planned and never narrowed when the
tests were written, so a claim about six things stood over evidence about four for the
life of the build. The frontends' side of that claim is checked in R-6 and R-9, by
comparing their server source and by driving a real browser, because it is a different
claim needing different evidence, not a bigger version of this one.

What is checked here: the suite names no stack and branches on nothing, so it cannot be
quietly special-cased; it passes against every active backend; and it executes the same
number of tests against each, so a backend cannot pass by skipping.
"""

from __future__ import annotations

import os
import re
import subprocess

import pytest

import spine

BEHAVIOURS = ("B1", "B2", "B3", "B4", "B5")


def test_the_contract_declares_the_named_domain_behaviours():
    doc = spine.read_yaml(spine.CONTRACT, "API contract")
    paths = doc.get("paths")
    if not isinstance(paths, dict) or not paths:
        pytest.fail(f"MALFORMED INPUT: {spine._rel(spine.CONTRACT)} declares no paths")

    blob = " ".join(str(v) for v in (list(paths.keys()) + [str(paths)])).lower()
    missing = [b for b in BEHAVIOURS if b.lower() not in blob]
    assert not missing, (
        "the contract must cover the named domain behaviours; unreferenced: "
        + ", ".join(missing)
        + " (tag each operation with its behaviour id so coverage is checkable)"
    )


def test_instrumentation_endpoints_are_excluded_from_the_contract():
    """Identity, beans and autoconfig are instrumentation, not contract.

    A demo surface inside the contract would make every backend owe it, and would make
    the frontends entitled to depend on it. They report resolved runtime data for one
    panel; that is not a promise to a client.
    """
    doc = spine.read_yaml(spine.CONTRACT, "API contract")
    paths = set((doc.get("paths") or {}))
    leaked = sorted(spine.instrumentation_paths() & paths)
    assert not leaked, (
        "instrumentation endpoints appear in the contract; they are declared in the "
        "manifest and excluded from it: " + ", ".join(leaked)
    )

    contract_text = spine.text_of(spine.CONTRACT)
    by_text = [
        line.strip() for line in contract_text.splitlines()
        if "__instrumentation" in line or "/__metrics" in line
    ]
    assert not by_text, (
        "instrumentation appears in the contract text:\n  " + "\n  ".join(by_text)
    )


def test_the_suite_contains_no_per_stack_branch_name_or_skip():
    """A backend that needs a special case in this suite is a backend that does not
    serve the contract."""
    spine.require_dir(spine.CONTRACT_SUITE, "contract suite")
    stack_ids = set(spine.stacks())
    services = {s.get("service") for s in spine.stacks().values() if s.get("service")}
    names = {n for n in (stack_ids | services) if n}

    skip_re = re.compile(r"\b(skip|xfail|skipif)\b")
    offenders = []
    for path in spine.iter_repo_files((".py",), root=spine.CONTRACT_SUITE):
        for n, line in enumerate(spine.text_of(path).splitlines(), start=1):
            if spine.is_comment_line(line):
                continue
            if any(name in line for name in names):
                offenders.append(f"{spine._rel(path)}:{n}: names a stack: {line.strip()}")
            elif skip_re.search(line):
                offenders.append(f"{spine._rel(path)}:{n}: branches on skip/xfail: {line.strip()}")
    assert not offenders, (
        "the contract suite must be identical across backends: no per-stack branch, "
        "name or skip:\n  " + "\n  ".join(offenders)
    )


def test_the_suite_reads_its_target_from_the_environment_and_nothing_else():
    """It knows a base URL. No name, no port, no capability flag, no branch.

    That is what makes running it four times a comparison of implementations rather than
    a comparison of APIs.
    """
    spine.require_dir(spine.CONTRACT_SUITE, "contract suite")
    joined = "\n".join(
        spine.text_of(p) for p in spine.iter_repo_files((".py",), root=spine.CONTRACT_SUITE)
    )
    assert "CONTRACT_BASE_URL" in joined, (
        "the contract suite reads no base URL from the environment; it must be told "
        "where to point and nothing else"
    )


@pytest.mark.needs_stacks
@pytest.mark.slow
def test_the_suite_passes_identically_against_every_active_backend():
    backends = spine.backends()
    assert backends, "the manifest declares no active backend stacks"

    results = {}
    for sid, stack in sorted(backends.items()):
        results[sid] = subprocess.run(
            ["python3", "-m", "pytest", str(spine.CONTRACT_SUITE), "-q", "--tb=short",
             "-p", "no:cacheprovider"],
            capture_output=True, text=True, timeout=900, cwd=spine.REPO_ROOT,
            env={**os.environ, "CONTRACT_BASE_URL": spine.base_url(sid, stack)},
        )

    failed = {sid: res.stdout[-2000:] for sid, res in results.items() if res.returncode != 0}
    assert not failed, (
        "the contract suite failed against: " + ", ".join(sorted(failed)) + "\n"
        + "\n".join(f"--- {sid} ---\n{out}" for sid, out in sorted(failed.items()))
    )

    # Identical, not merely green. A backend whose suite collected fewer tests passes on
    # a smaller promise than the others and nothing above would say so.
    counts = {sid: re.findall(r"(\d+) passed", res.stdout) for sid, res in results.items()}
    distinct = {tuple(v) for v in counts.values()}
    assert len(distinct) == 1, (
        "the suite did not execute identically across backends; passed counts differ: "
        + ", ".join(f"{sid}={v}" for sid, v in sorted(counts.items()))
    )
