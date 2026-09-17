# Lessons

---

## A transcript typed into a README is an unbound claim

`README.in.md` quoted a walkthrough step with a work item id, `DEMO-4c11a615`, from a run
nobody could reproduce. It was correct when it was typed and there was nothing that would
have gone red if it stopped being. That is the same defect as a guard that only exercises
the happy path, in prose, and the README is the copy a reader trusts most.

The fix is not a better transcript. It is that the artifact is recorded by
`make record-demo` and a check re-records and compares.

## Normalising a field is narrowing a check, so the allowlist is the blast radius

A reproduction check that compares "modulo volatile fields" can be defeated without anybody
touching the check: widen what counts as volatile until nothing is compared. So the four
allowed fields are declared in one place, and anything beyond them fails the test until it
is written down in `DECISIONS.md` with a reason.

## Recording a demo on a pipe records a demo nobody sees

`demo.py` colours its output behind an `isatty()` check, which is right: escape codes in a
CI log are garbage. It also means a recorder using a pipe captures a transcript that is not
what a reader would get. Recording on a pseudo-terminal costs about fifteen lines and the
emphasis in the artifact is then the demo's own, not the recorder's opinion of it.
