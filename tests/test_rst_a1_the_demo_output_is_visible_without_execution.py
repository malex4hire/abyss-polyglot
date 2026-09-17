"""RST-A1: the demo's own output is visible in the README without running anything.

A reviewer's first pass is over before any decision to clone is made. The repository's
strongest claim is that one command produces a working walkthrough, and until now the
evidence for it lived behind that command. This puts a recording of the walkthrough in
front of the reader.

The artifact is a recording, not a picture of one somebody drew. That distinction is the
whole point and it is what these checks are for: a hand-authored transcript in a README
is a claim about output, and it decays the moment the output changes. One already had:
the README quoted a work item id from a run nobody could reproduce.

Four things are checked.

1. The artifact exists where the README says it does.
2. It is referenced above the first section heading, which is the part of the page a
   thirty-second pass actually reaches.
3. A fresh recording matches the committed one, modulo the volatile allowlist. This is
   the one that settles it: a hand-edited SVG fails here, and so does a committed
   artifact that has gone stale against the demo it claims to show.
4. The allowlist itself cannot be widened silently. Every field normalised away is a
   field the comparison stops checking, so widening it is how check 3 would be defeated
   without touching check 3.
"""

from __future__ import annotations

import re
import socket
import sys
from pathlib import Path

import pytest

import spine

DECISIONS = spine.REPO_ROOT / "DECISIONS.md"
RECORDER = spine.REPO_ROOT / "scripts" / "record_demo.py"


def recorder():
    """The regeneration entry point, imported from inside a test body.

    Deliberately not a module-level import: a raise at collection time is an error, and
    an errored suite is not a gate. A missing recorder has to land as a named failure,
    the same as any other missing input in this suite.
    """
    import importlib

    spine.require_file(RECORDER, "the demo recorder")
    if str(RECORDER.parent) not in sys.path:
        sys.path.insert(0, str(RECORDER.parent))
    try:
        return importlib.import_module("record_demo")
    except ImportError as exc:  # pragma: no cover, a broken recorder, not a missing one
        pytest.fail(f"MISSING INPUT: {spine._rel(RECORDER)} could not be imported: {exc}")

# The four fields the ICG's allowlist names. Anything the recorder normalises beyond
# these is a widening, and a widening owes a decision log entry.
ICG_ALLOWLIST = frozenset({"timestamp", "duration", "port", "generated-id"})

# What each allowed field is allowed to BE.
#
# The key set alone is not a bound. A review demonstrated it: broaden an existing pattern
# to `[^<>]+` under the name `generated-id`, and normalise() collapses every text node in
# both the committed artifact and the fresh recording to the same skeleton. The
# reproduction check then compares two identical husks and passes over a fabricated
# transcript, with no new key and so nothing owed in the decision log.
#
# So the bound is on what the patterns MATCH, and it lives here rather than in the
# recorder on purpose: a bound kept beside the thing it bounds is relaxed by the same edit
# that widens it.
SHAPES = {
    "timestamp": lambda s: bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T[\d:.+\-Z]+", s)),
    "duration": lambda s: bool(re.fullmatch(r"\d+(?:\.\d+)?\s?(?:ms|s)", s)),
    "port": lambda s: s.isdigit() and 1 <= len(s) <= 5,
    "generated-id": lambda s: s.startswith("DEMO-"),
}

# How much of the artifact's own text the four fields may account for. Measured at 12.7%
# when this landed, so a doubling is allowed before it goes red; the demonstrated attack
# takes it to substantially all of it. A backstop under the shapes above, not a substitute
# for them.
VOLATILE_CEILING = 0.25


def _readme() -> str:
    return spine.text_of(spine.require_file(spine.REPO_ROOT / "README.md", "the README"))


def _lines_outside_code_fences(text: str):
    """Yield (index, line) for lines that are not inside a fenced code block.

    A fenced block here contains `# comment` lines that would otherwise read as headings,
    which would put "the first section heading" inside the run instructions.
    """
    fenced = False
    for index, line in enumerate(text.splitlines()):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield index, line


def _first_section_heading(text: str) -> int:
    """The line index of the first heading after the document title.

    The title is the page's name, not a section. The region this constraint governs is
    everything between the title and the heading that opens the first section, because
    that is what a reader sees before deciding whether to keep going.
    """
    headings = [i for i, line in _lines_outside_code_fences(text) if re.match(r"#{1,6} ", line)]
    assert headings, "the README has no headings at all, so there is no fold to be above"
    assert len(headings) > 1, (
        "the README has only a title and no section heading; RST-A1 governs the region "
        "above the first section, and there is no first section"
    )
    return headings[1]


def test_the_recorded_artifact_exists():
    rec = recorder()
    spine.require_file(rec.ARTIFACT, "the recorded demo artifact")
    body = spine.text_of(rec.ARTIFACT)
    assert body.lstrip().startswith("<svg") or "<svg" in body[:400], (
        f"{spine._rel(rec.ARTIFACT)} is not an SVG document; the artifact has to "
        "render in GitHub's markdown viewer from the repository, with nothing fetched"
    )


def test_the_artifact_is_referenced_above_the_first_section_heading():
    rec = recorder()
    text = _readme()
    fold = _first_section_heading(text)
    reference = rec.ARTIFACT.relative_to(spine.REPO_ROOT).as_posix()

    hits = [i for i, line in _lines_outside_code_fences(text) if reference in line]
    assert hits, (
        f"the README never references {reference}. The artifact exists and the page does "
        "not show it, which is the defect this constraint is about"
    )
    assert min(hits) < fold, (
        f"{reference} is referenced at line {min(hits) + 1}, below the first section "
        f"heading at line {fold + 1}. Demo output that needs a scroll is demo output a "
        "thirty-second pass does not reach"
    )


def test_the_artifact_carries_no_host_or_path_from_the_machine_that_recorded_it():
    """A transcript is captured output, and captured output carries its environment."""
    rec = recorder()
    body = spine.text_of(spine.require_file(rec.ARTIFACT, "the recorded artifact"))
    leaks = []
    if re.search(r"/(?:home|Users)/[A-Za-z0-9._-]+", body):
        leaks.append("a home directory path")
    if str(Path.home()) in body:
        leaks.append("this machine's home directory")
    hostname = socket.gethostname()
    if hostname and len(hostname) > 3 and hostname in body:
        leaks.append(f"this machine's hostname ({hostname})")
    assert not leaks, (
        f"{spine._rel(rec.ARTIFACT)} carries " + ", ".join(leaks)
        + ". The recorder scrubs these; a committed artifact holding one was not produced "
        "by it"
    )


def test_the_volatile_allowlist_is_not_widened_without_a_decision():
    """Every normalised field is a field the comparison below stops checking.

    So widening the allowlist is how the reproduction check gets defeated without anybody
    editing the reproduction check. It costs a line in the decision log, which is cheap
    and leaves the widening visible to whoever reads it next.
    """
    rec = recorder()
    declared = set(rec.VOLATILE)
    widened = sorted(declared - ICG_ALLOWLIST)
    if not widened:
        return

    spine.require_file(DECISIONS, "the decision log")
    log = spine.text_of(DECISIONS)
    undeclared = [name for name in widened if f"volatile field: {name}" not in log]
    assert not undeclared, (
        "the recorder normalises fields outside the allowlist with no decision log entry: "
        + ", ".join(undeclared)
        + f"\n\nEach one needs a line in {spine._rel(DECISIONS)} reading "
        "'volatile field: <name>' and saying why the artifact cannot reproduce it"
    )


def test_a_fresh_recording_matches_the_committed_artifact():
    """The check that settles it: re-record, and compare modulo the allowlist.

    This runs the walkthrough the same way the artifact was recorded, on a bare
    interpreter, so it is also a second reading of R-8: if `python3 demo.py` stops working
    with nothing installed, the artifact stops reproducing and this goes red.

    Deliberately not marked slow. The whole walkthrough runs in well under a second, and a
    marker would have kept the one check that settles this out of `make verify-host`.
    """
    rec = recorder()
    committed = spine.text_of(spine.require_file(rec.ARTIFACT, "the recorded artifact"))

    try:
        fresh = rec.render(rec.record())
    except rec.RecordingFailed as exc:
        pytest.fail(f"the walkthrough could not be recorded, so the artifact cannot be checked: {exc}")

    expected = rec.normalise(committed)
    actual = rec.normalise(fresh)

    if expected == actual:
        return

    import difflib

    diff = "\n".join(list(difflib.unified_diff(
        expected.splitlines(), actual.splitlines(),
        fromfile="committed (normalised)", tofile="fresh recording (normalised)",
        lineterm="", n=2,
    ))[:60])
    pytest.fail(
        f"{spine._rel(rec.ARTIFACT)} does not reproduce from a fresh run of the "
        "walkthrough. Either the demo's output changed and the artifact is stale, or the "
        f"artifact was edited by hand. Regenerate it with `make record-demo`.\n\n{diff}"
    )


def _artifact_text(rec) -> str:
    """The transcript the artifact renders, with the SVG scaffolding removed."""
    import xml.etree.ElementTree as ET

    svg = spine.text_of(spine.require_file(rec.ARTIFACT, "the recorded artifact"))
    namespace = "{http://www.w3.org/2000/svg}"
    return "".join((el.text or "") for el in ET.fromstring(svg).iter(namespace + "text"))


def test_each_volatile_pattern_matches_only_the_shape_its_name_claims():
    """The bound on breadth, which the key check does not provide.

    Every field normalised away is a field the reproduction check stops looking at, and
    the amount a field takes away is a property of its PATTERN, not of its name. A field
    called `generated-id` whose pattern eats whole lines is a disarmed check wearing an
    allowed name.
    """
    rec = recorder()
    content = _artifact_text(rec)
    assert content, "the artifact renders no text, so there is nothing to bound"

    wrong = []
    for name, pattern in sorted(rec.VOLATILE.items()):
        shape = SHAPES.get(name)
        if shape is None:
            wrong.append(f"{name}: no declared shape, so its pattern is unbounded")
            continue
        for match in pattern.finditer(content):
            if not shape(match.group(0)):
                wrong.append(f"{name}: matched {match.group(0)[:60]!r}, which is not a {name}")
                break

    assert not wrong, (
        "volatile patterns matching things they are not named for:\n  " + "\n  ".join(wrong)
        + "\n\nA pattern that matches more than its name says is how the reproduction "
        "check gets disarmed without anybody editing the reproduction check"
    )


def test_the_volatile_fields_do_not_account_for_most_of_the_artifact():
    """A backstop under the shapes, on volume rather than on form."""
    rec = recorder()
    content = _artifact_text(rec)
    taken = sum(
        len(match.group(0))
        for pattern in rec.VOLATILE.values()
        for match in pattern.finditer(content)
    )
    share = taken / len(content)
    assert share <= VOLATILE_CEILING, (
        f"the volatile patterns account for {share:.1%} of the transcript, over the "
        f"{VOLATILE_CEILING:.0%} ceiling. Past that the reproduction check is comparing "
        "more placeholder than recording"
    )
