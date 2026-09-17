# Lessons

---

## A CHECK THAT ASSERTS A PROXY FOR THE PROPERTY REPORTS GREEN WHILE THE PROPERTY IS FALSE

**The rule: put the bound in the test, beside the thing it bounds, so that widening it
requires the same edit that would relax it.**

This is one defect, not several, and it has now appeared three times across two
repositories inside a single branch. Each instance asserted something *adjacent to* the
property and read as though it asserted the property:

| the property | what was asserted instead | how it failed |
|---|---|---|
| the volatile patterns normalise only volatile fields | **the set of NAMES** those patterns are filed under | broaden `generated-id` to `[^<>]+`: the reproduction check compares two identical husks and passes a fabricated transcript. No new name, so nothing was owed |
| each constraint landed as its own commit | **the CARDINALITY of the union** of commits mentioning any constraint | three subjects each naming all three constraints: `owed = 3`, `distinct = 3`, green, no constraint with a commit of its own |
| each constraint landed as its own commit (*the second repository*) | **the same cardinality test, copied** | the check was duplicated before it was attacked, so the defect was duplicated with it. Two repositories, one edit's worth of thought |

**The third phrasing of this class, named because it is the one this branch got right, not
one it got wrong: asserting that a gate EXISTS in place of asserting that the gate is
CORRECT.** A gate can exist, be renamed, be skipped by a marker, or be red. The RST-A2
check refuses that shape deliberately: it resolves the cited `R-n` to a file, cross-checks
it against the README's own table, then *runs it* and fails on a skip. That is the property.
Had it stopped at the glob, it would be a fourth row above.


**Why this class is worse than having no check.** A missing check is visible as an absence
and somebody eventually writes it. A proxy check occupies the slot: it is named for the
property, it is cited in a commit message as covering the property, and it reports green.
Nobody writes the real one, because the slot looks filled.

**The three tells, all cheap to run before filing:**

1. **Name the property in a sentence, then read the assertion.** If the sentence and the
   assertion are not the same claim, the gap is the defect. "Only volatile fields are
   normalised" is not "the key set is unchanged."
2. **Ask what the assertion would still permit.** A cardinality test permits any
   assignment with the same count. A name test permits any pattern under that name.
3. **Attack the check, not the subject.** Mutating the subject proves the check reacts.
   Only mutating the check's own logic proves it is correct, and every instance above
   survived subject mutation.

**And the fix, which generalises past these three: the bound belongs in the test.** A bound
kept beside the thing it bounds is relaxed by the same edit that widens it, which is not a
bound at all. `SHAPES` and `VOLATILE_CEILING` live in the RST-A1 test rather than in
`scripts/record_demo.py` for exactly that reason: widening `VOLATILE` no longer relaxes
what `VOLATILE` is allowed to match.

**The corollary that caught the fourth finding.** The same reasoning applies to a check's
own scope. An em-dash check reading only U+2014 is a proxy for "no em-dash-looking
punctuation", and a visually identical U+2015 would defeat it while the check stayed green.
So the check reads the class, and the rule was widened to say so in the same change.

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
