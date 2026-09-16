"""R-1 — the manifest and compose agree, and no port literal lives outside the manifest.

Every stack declares its service, its port and its health endpoint in one file.
scripts/render-env.py turns those into environment variables, compose reads them, and
every other consumer — the browser checks, the side-by-side page, demo.py — derives from
the same place.

The reason this is a check rather than a convention: a port written in two files is
correct until one of them changes, and the failure it produces is a connection refused
somewhere unrelated, hours later, with nothing pointing back at the edit.
"""

from __future__ import annotations

import filecmp
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

import spine

# A file a renderer owns may carry a port, because a rendered value is a derived value —
# that is the whole point of rendering it. The exemption is not taken on trust: the last
# test in this file re-runs every renderer and fails if what is committed differs from
# what they produce, so hand-editing a generated file to say something the manifest does
# not is caught rather than excused.
GENERATED_MARKER = "GENERATED"

# script -> the committed paths it owns. Both halves are needed: the first to re-run it,
# the second so a renderer that silently stops writing a file is a failure rather than a
# pass.
#
# render-env.py owns no committed path: .env is regenerated on every `make up` and is not
# in the repository, so it cannot go stale. It is still run, because a renderer that has
# stopped working is worth finding here rather than at the moment somebody starts the demo.
RENDERERS = {
    "scripts/render-env.py": (),
    "scripts/render-readme.py": ("README.md",),
    "scripts/render-app-tokens.py": (
        "modules/angular/src/tokens.generated.css",
        "modules/react/src/tokens.generated.css",
        "modules/angular/src/app.generated.css",
        "modules/react/src/app.generated.css",
    ),
}


def _is_generated(path) -> bool:
    return GENERATED_MARKER in spine.text_of(path)[:400]


def test_every_active_stack_declares_a_service_a_port_and_a_health_endpoint():
    active = spine.active_stacks()
    assert active, "the manifest declares no active stacks"
    incomplete = []
    for sid, stack in sorted(active.items()):
        for field in ("service", "port", "health_endpoint"):
            if not stack.get(field):
                incomplete.append(f"'{sid}' declares no '{field}'")
    assert not incomplete, (
        "active stacks must declare service, port and health endpoint:\n  "
        + "\n  ".join(incomplete)
    )


def test_every_declared_port_is_distinct():
    """Two services on one port is a demo that comes up and serves the wrong thing."""
    ports = spine.declared_ports()
    collisions = {}
    for owner, port in sorted(ports.items()):
        collisions.setdefault(port, []).append(owner)
    clashing = {p: owners for p, owners in collisions.items() if len(owners) > 1}
    assert not clashing, (
        "the manifest assigns one port to more than one service: "
        + ", ".join(f"{p} -> {', '.join(owners)}" for p, owners in sorted(clashing.items()))
    )


@pytest.mark.needs_docker
def test_compose_services_and_the_manifest_agree_in_both_directions():
    """Both directions, because each catches a different mistake.

    A manifest entry with no compose service is a stack that cannot start. A compose
    service absent from the manifest is a process nothing verifies — which is exactly
    what the two study-layer services that used to sit in this file were.
    """
    active = spine.active_stacks()
    declared = {stack["service"] for stack in active.values() if stack.get("service")}
    services = set(spine.compose_services())

    infra_services = {
        spec.get("service") for spec in spine.infrastructure().values()
        if isinstance(spec, dict) and spec.get("service")
    }

    missing = sorted(declared - services)
    extra = sorted(services - declared - infra_services)

    assert not missing, (
        "active manifest entries with no compose service: " + ", ".join(missing)
    )
    assert not extra, (
        "compose services absent from the manifest: " + ", ".join(extra)
    )


def test_no_port_literal_appears_outside_the_manifest():
    """Ports are manifest-declared and derived everywhere else, Postgres included.

    Markdown is scanned like everything else. A README that types a port is the same
    defect as a script that types one — it is a second place the number lives, and it is
    the copy a reader is most likely to trust. The README therefore carries
    `{{port:<stack>}}` placeholders and is rendered by scripts/render-readme.py.
    """
    ports = set(spine.declared_ports().values())
    assert ports, "no ports declared in the manifest"

    pattern = re.compile(
        r"(?<![\w.])(" + "|".join(str(p) for p in sorted(ports)) + r")(?![\w.])"
    )
    offenders = []
    for path in spine.iter_repo_files((
        ".yml", ".yaml", ".sh", ".py", ".ts", ".tsx", ".js", ".mjs", ".java",
        ".xml", ".properties", ".env", ".md", ".html", ".css", ".conf",
    )):
        if path == spine.MANIFEST or path.name in spine.JOURNALS or _is_generated(path):
            continue
        for n, line in enumerate(spine.text_of(path).splitlines(), start=1):
            if pattern.search(line):
                offenders.append(f"{spine._rel(path)}:{n}: {line.strip()}")
    assert not offenders, (
        "port literals must appear only in the manifest and be derived elsewhere:\n  "
        + "\n  ".join(offenders)
    )


def test_no_fixed_address_appears_outside_the_manifest():
    """The same rule as ports, for the one address the demo pins.

    This is the check that did not exist. The address was written into compose three
    times — once as the pinned endpoint, twice as an /etc/hosts entry on a client. When
    the pinned endpoint silently failed to apply, its two copies went on naming an address
    nothing was listening on, and the demo failed offline with a Hibernate dialect error
    three layers from the cause.
    """
    addresses = {
        str(spec["ip"]) for spec in spine.infrastructure().values()
        if isinstance(spec, dict) and spec.get("ip")
    }
    if not addresses:
        pytest.skip("the manifest pins no fixed address, so there is nothing to duplicate")

    pattern = re.compile(r"(?<![\w.])(" + "|".join(re.escape(a) for a in sorted(addresses)) + r")(?![\w.])")
    offenders = []
    for path in spine.iter_repo_files((
        ".yml", ".yaml", ".sh", ".py", ".ts", ".tsx", ".js", ".mjs", ".java",
        ".xml", ".properties", ".env", ".md", ".conf",
    )):
        if path == spine.MANIFEST or path.name in spine.JOURNALS or _is_generated(path):
            continue
        for n, line in enumerate(spine.text_of(path).splitlines(), start=1):
            if spine.is_comment_line(line):
                continue
            if pattern.search(line):
                offenders.append(f"{spine._rel(path)}:{n}: {line.strip()}")
    assert not offenders, (
        "a pinned address must be declared in the manifest and derived everywhere else:\n  "
        + "\n  ".join(offenders)
    )


def test_prose_states_no_count_of_a_set_the_manifest_owns():
    """A typed count and a manifest drift apart silently, and the prose wins the reader.

    The nouns that name the set are declared by the manifest, so this is contextual
    rather than a hunt for integers: "four backends" is a violation and a port number
    mentioned in passing is not. A count that must appear in prose comes from a
    `{{count:stacks}}` placeholder rendered against the manifest.
    """
    nouns = spine.prose_nouns()
    pattern = spine.count_qualifier_pattern(nouns)

    offenders = []
    for path in spine.iter_repo_files((".md",)):
        if path.name.endswith(".in.md"):
            continue

        # Where a file has a template, the template is what is read — with its
        # placeholders still in place. Reading the rendered output instead would flag
        # every derived count as a typed one, and the only way to pass would be to stop
        # stating counts at all, which is not what this is asking for.
        template = path.with_suffix("").with_suffix(".in.md")
        text = spine.text_of(template if template.is_file() else path)

        for n, line in enumerate(text.splitlines(), start=1):
            for match in pattern.finditer(line):
                offenders.append(
                    f"{spine._rel(path)}:{n}: '{match.group(0)}' states a count of a set "
                    "the manifest owns"
                )
    assert not offenders, (
        "prose must derive counts of the stack set rather than state them:\n  "
        + "\n  ".join(offenders)
        + "\n\nUse a {{count:stacks}} placeholder and render with scripts/render-readme.py."
    )


def test_every_generated_file_is_reproducible_from_the_manifest():
    """Re-run each renderer and require what it produces to match what is committed.

    This is what makes the exemption above safe. Without it, "carries a GENERATED banner"
    is a comment anybody can type at the top of a hand-written file, and the one rule this
    repository enforces most loudly would have a hole in it shaped like a comment.

    Run against a copy of the tree, so a check cannot repair the thing it is checking.
    """
    missing = [
        rel for paths in RENDERERS.values() for rel in paths
        if not (spine.REPO_ROOT / rel).is_file()
    ]
    assert not missing, (
        "generated files absent from the tree; run `make render`: " + ", ".join(missing)
    )

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(
            spine.REPO_ROOT, work,
            ignore=shutil.ignore_patterns(
                ".git", "node_modules", "target", "__pycache__", ".pytest_cache", ".venv",
            ),
        )
        stale = []
        for script, paths in sorted(RENDERERS.items()):
            result = subprocess.run(
                ["python3", script], capture_output=True, text=True, cwd=work, timeout=120,
            )
            assert result.returncode == 0, (
                f"{script} failed:\n{result.stdout}\n{result.stderr}"
            )
            for rel in paths:
                produced, committed = work / rel, spine.REPO_ROOT / rel
                if not produced.is_file():
                    stale.append(f"{rel}: {script} did not write it")
                elif not filecmp.cmp(produced, committed, shallow=False):
                    stale.append(f"{rel}: differs from what {script} produces")

        assert not stale, (
            "generated files are out of date or were edited by hand. Re-run `make render` "
            "and commit the result; do not edit a generated file:\n  " + "\n  ".join(stale)
        )
