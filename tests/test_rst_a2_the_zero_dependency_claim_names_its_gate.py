"""RST-A2: the one-command, no-dependency claim is bound to the gate that proves it.

A claim in a README is a control. It tells a reader what this repository does, it is the
copy they are most likely to trust, and unbound it has nothing that goes red when it stops
being true. That is the shape THE ROOT RULE refuses everywhere else here, and prose is not
exempt from it.

So the first screenful names a gate, and these checks close the loop three ways:

1. The claim is where a thirty-second pass reaches it, above the first section heading.
2. Every `R-n` it cites resolves to a real test file and to a row in the README's own
   verification table. A citation that resolves to neither is a decorative identifier.
3. The cited gate actually passes, with nothing skipped. A claim bound to a gate that is
   red, or to one that quietly skips itself on this machine, is worse than an unbound
   claim: it reads as verified and is not.

The third is the one that cannot be satisfied by editing this file.
"""

from __future__ import annotations

import re
import subprocess
import sys

import pytest

import spine

# The negations that make this claim the claim. Deliberately a short declared list rather
# than one sentence matched exactly: the wording is editorial and should be free to
# improve, while what it has to say is not. This is the only typed string here, and it is
# not load-bearing on its own — the citation below is what makes the claim checkable.
NO_DEPENDENCY_PHRASES = (
    "nothing installed",
    "no install",
    "no pip",
    "zero dependencies",
    "no dependencies",
)

GATE = re.compile(r"\bR-(\d+)\b")


def _readme() -> str:
    return spine.text_of(spine.require_file(spine.REPO_ROOT / "README.md", "the README"))


def _lines_outside_code_fences(text: str):
    fenced = False
    for index, line in enumerate(text.splitlines()):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield index, line


def _first_screenful(text: str) -> str:
    """Everything between the title and the first section heading.

    The title names the page; the first heading opens the first section. What sits between
    them is what a reader sees before deciding whether to keep going, and it is the region
    this constraint governs.
    """
    lines = text.splitlines()
    headings = [i for i, line in _lines_outside_code_fences(text) if re.match(r"#{1,6} ", line)]
    assert len(headings) > 1, (
        "the README has no section heading, so it has no first screenful to govern"
    )
    return "\n".join(lines[headings[0]:headings[1]])


def _gate_file(number: str):
    matches = sorted(spine.REPO_ROOT.glob(f"tests/test_r{int(number):02d}_*.py"))
    return matches


def test_the_first_screenful_states_the_one_command_no_dependency_claim():
    region = _first_screenful(_readme())

    command = f"python3 {spine.DEMO.name}"
    assert command in region, (
        f"the first screenful does not carry `{command}`. The one-command claim is the "
        "strongest thing this repository says and it belongs where a reader lands, not "
        "inside a setup section"
    )

    stated = [phrase for phrase in NO_DEPENDENCY_PHRASES if phrase in region.lower()]
    assert stated, (
        "the first screenful names the command and never says what it does not need. "
        "One command that still wants an install is an ordinary README; the claim is the "
        "absence. Expected one of: " + ", ".join(NO_DEPENDENCY_PHRASES)
    )


def test_every_gate_the_first_screenful_cites_resolves_to_a_real_check():
    """A citation is a promise that something will go red. Resolve it both ways.

    Both, because each catches a different rot. A gate with no test file is a claim
    pointing at nothing. A gate absent from the verification table is a claim pointing at
    something the README itself does not list, which is how a renumbering leaves the prose
    citing a check that has moved.
    """
    readme = _readme()
    region = _first_screenful(readme)

    cited = sorted({m.group(1) for m in GATE.finditer(region)}, key=int)
    assert cited, (
        "the first screenful cites no gate. RST-A2 asks the claim to name what proves it; "
        "an unbound claim in a README is the same defect as a guard that only exercises "
        "the happy path"
    )

    unresolved, untabled = [], []
    for number in cited:
        matches = _gate_file(number)
        if len(matches) != 1:
            unresolved.append(
                f"R-{number} -> {len(matches)} matching test files in tests/"
            )
        # The README's own verification table is the list a reader would check against.
        if not re.search(rf"^\|\s*R-{number}\s*\|", readme, re.M):
            untabled.append(f"R-{number}")

    assert not unresolved, (
        "the first screenful cites gates that do not resolve to exactly one check:\n  "
        + "\n  ".join(unresolved)
    )
    assert not untabled, (
        "the first screenful cites gates absent from the README's own verification table: "
        + ", ".join(untabled)
        + ". The prose and the table have to name the same set, or one of them is stale"
    )


def test_the_cited_gate_passes_and_skips_nothing():
    """Run it. A claim bound to a red gate reads as verified and is not.

    Skips count as a failure here on purpose. A gate that opts itself out on the machine
    doing the checking is exactly the shape that lets a claim look proven while nothing
    proves it, and the citation in the README makes no distinction.
    """
    region = _first_screenful(_readme())
    cited = sorted({m.group(1) for m in GATE.finditer(region)}, key=int)
    assert cited, "no gate cited; the check above explains why that fails"

    targets = []
    for number in cited:
        matches = _gate_file(number)
        assert len(matches) == 1, f"R-{number} does not resolve to one test file"
        targets.append(str(matches[0].relative_to(spine.REPO_ROOT)))

    run = subprocess.run(
        [sys.executable, "-m", "pytest", *targets, "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=spine.REPO_ROOT, capture_output=True, text=True, timeout=600,
    )
    tail = (run.stdout + run.stderr)[-3000:]

    assert run.returncode == 0, (
        "the first screenful cites " + ", ".join(f"R-{n}" for n in cited)
        + " and that gate does not pass. The claim is live on the page while the thing "
        f"proving it is red:\n\n{tail}"
    )
    assert not re.search(r"\b\d+ (?:skipped|xfailed|deselected)\b", run.stdout), (
        "the cited gate did not run in full; a check that opts out is not a check the "
        f"README gets to cite:\n\n{tail}"
    )
