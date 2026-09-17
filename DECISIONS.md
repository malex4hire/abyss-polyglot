# Decisions

Dated, append-only. A decision that exists only in a commit message is a decision the next
reader has to reconstruct from a diff.

---

## 2026-09-17 — the README shows recorded demo output, above the first heading

**RST-A1.** A reviewer's first pass is over before any decision to clone is made, so the
repository's strongest claim — one command, nothing installed — had to be visible without
running the command. `docs/media/demo.svg` is a recording of `python3 demo.py`, rendered as
an SVG committed in-repo: no external host, no third-party embed, nothing fetched when the
page renders.

**Why a recording rather than a transcript typed into the page.** The README already
carried one of those, a work item id from a run nobody could reproduce
(`DEMO-4c11a615`). A typed transcript is a claim about output and it decays silently. This
one is re-recorded by `make record-demo`, and
`tests/test_rst_a1_the_demo_output_is_visible_without_execution.py` re-runs the recorder and
compares, so a stale artifact and a hand-edited one both go red.

**Why a window and not the whole run.** The walkthrough prints 147 lines. The artifact
shows steps 4 to 6 — contiguous, bounded by the demo's own step rules, so nothing is
elided inside it. Those three carry a typed refusal that writes nothing, the rollup, and
archive as a soft delete.

**Why it is recorded on a pseudo-terminal under `-S -I`.** `-S -I` is the condition R-8
asserts, and an artifact recorded under weaker conditions would be evidence for a
different claim. The pseudo-terminal is because `demo.py` colours through an `isatty()`
check: a plain pipe would record a transcript nobody would ever see. Every colour in the
SVG is read off the demo's own escape codes and resolved against `design/tokens.yaml`.

**The volatile-field allowlist** is `timestamp`, `duration`, `port`, `generated-id`,
declared in `scripts/record_demo.py:VOLATILE`. Each one is a field the reproduction check
stops looking at, so widening it is governed: any field beyond those four needs a line in
this log reading `volatile field: <name>`, and the RST-A1 test fails without it.

**Restructured, not removed.** The hand-authored excerpt in `## Run it` is gone from that
section and present at the top of the page as a recording of the same three steps. The
prose around it was kept and re-pointed.

---

## 2026-09-17 — the zero-dependency claim names the gate that proves it

**RST-A2.** The first screenful states `python3 demo.py`, with nothing installed, and names
**R-8** as the gate. `tests/test_rst_a2_the_zero_dependency_claim_names_its_gate.py` asserts
the claim is above the first section heading, that every `R-n` it cites resolves to a test
file in `tests/`, and that the cited gate passes with nothing skipped.

A claim in a README is a control like any other. Unbound, it has no test that goes red when
it stops being true, which is the shape `THE ROOT RULE` already refuses everywhere else in
this repository.

---

## 2026-09-17 - one commit per constraint, and the history is an input

**RST-A4.** Each constraint landed as its own commit naming it.
`tests/test_rst_a4_the_commit_history_is_legible.py` derives the set from this
repository's own `tests/test_rst_*.py` files and reads commit subjects, so a check that
arrives with no commit behind it fails, and so does a branch collapsed into one commit
claiming all of them.

It reads history rather than a branch range on purpose. A range against `origin/main` is
empty the moment the branch merges, which would leave the check green forever for the
wrong reason.

`actions/checkout@v4` fetches one commit by default, so `fetch-depth: 0` was added to the
host gate. A shallow clone fails this check with a named reason rather than skipping it:
the history is the input, and a check that passes quietly when its input is absent is
decoration.
