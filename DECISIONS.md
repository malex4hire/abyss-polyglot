# Decisions

Dated, append-only. A decision that exists only in a commit message is a decision the next
reader has to reconstruct from a diff.

---

## 2026-09-17 - the README shows recorded demo output, above the first heading

**RST-A1.** A reviewer's first pass is over before any decision to clone is made, so the
repository's strongest claim - one command, nothing installed - had to be visible without
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
shows steps 4 to 6 - contiguous, bounded by the demo's own step rules, so nothing is
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

## 2026-09-17 - the zero-dependency claim names the gate that proves it

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

---

## 2026-09-17 - three holes the auto-review found in the checks above, and what closed them

Every one was reproduced by execution before it was believed, and every fix was driven red
the same way.

**The allowlist keyed on NAMES, so the reproduction check could be disarmed silently.**
`declared - ICG_ALLOWLIST` only notices a new key. Broaden an existing pattern to
`[^<>]+` under the name `generated-id` and `normalise()` collapses both the committed
artifact and the fresh recording to the same husk; the reproduction check then compares
two skeletons and passes over a fabricated transcript, with nothing owed here. Confirmed:
with that pattern and `status=IN_PROGRESS` hand-edited to `status=TOTALLY_FAKE`, all five
RST-A1 checks were green.

Closed by bounding what the patterns MATCH rather than what they are called: a declared
shape per field, plus a ceiling on the share of the transcript the four may account for
(12.7% when this landed, ceiling 25%). Both live in the test rather than in the recorder,
because a bound kept beside the thing it bounds is relaxed by the same edit that widens it.
The attack now reads 104.8% and goes red on both.

**The anti-squash check counted a union, which a banner subject defeats.**
`len(set().union(*naming.values())) >= len(owed)` is a cardinality test, not a per-
constraint assignment. Three commits each subject-lined `RST-A1 RST-A2 RST-A4: ...` gave
`owed = 3`, `distinct = 3`, green, with no constraint having a commit of its own.

Closed by reading the spec as it is written - "each naming the RST identifier it
satisfies", singular. A subject naming more than one constraint is evidence for none of
them, and every constraint must have a commit to itself. The three banner commits now go
red.

**`RST-A1` matched `RST-A10`**, because the match was a bare case-insensitive substring. A
single `RST-A10: one commit only` commit reported RST-A1 as satisfied. Latent at three
constraints and wrong at ten. Closed with a boundary that does not treat a digit as a
continuation.

**Known and deliberately not closed:** `normalise()` runs on the rendered SVG while `x`
coordinates are computed from unnormalised character columns, so a volatile value whose
length varies mid-line would break reproduction for a reason unrelated to content. Not
reachable today - the only volatile tokens inside the steps 4 to 6 window are the
fixed-width `DEMO-xxxxxxxx` and two line-final timestamps, and no port appears. It is also
the loud direction: it fails the gate and someone re-records, rather than passing quietly.

**Reported, not fixed:** the em dash convention is prose with no check anywhere, and four
em dashes reintroduced themselves inside this branch before a commit removed them by hand.
The fix is an audit line in `scripts/audit-names.py`, which is already wired into
`make verify-host` and CI. It is a new check in a repository frozen to presentation work,
so it is the operator's call rather than this branch's.

---

## 2026-09-17 - the em dash convention has a check, and D-2 is amended to allow it

**Operator ruling, this session.** D-2's freeze covers product surface: backends,
frontends, contract endpoints, modules, architectural depth. **It does not cover hygiene
gates that prevent a recurring manual correction.** A check that stops a convention being
hand-fixed on every branch is not depth; it is what keeps this repository from generating
chores after attention moves elsewhere. The previous entry filed this as `wont-fix` on a
scope reading that the operator has now corrected, so this supersedes it.

**The count was wrong and the record should carry the measured one.** This branch
reintroduced **six** em dashes across five lines in two files, not four.
`git show 3f1cdab -U0 | grep '^-' | grep -oP '\\x{2014}' | wc -l` returns 6; one line
carried two. The codepoint is written as an escape here because this file is inside the
population the check scans, which it demonstrated by failing on the first draft of this
very paragraph.

**Where it lives.** `scripts/audit-names.py`, which is already wired into `make
verify-host` and the CI audits step. A second audit script for one rule is wiring that buys
nothing.

**The population is read from git**, not from a list of extensions kept in the script. A
hand-kept set of "which files are ours" is a second copy of a fact and goes stale silently,
which is the defect that file already exists to refuse. Binaries drop out by failing to
decode rather than by being named. `licenses/` is excluded: it is third-party text this
repository carries and does not author, and rewriting a vendored licence to satisfy a house
style is not something a check gets to ask for. An exclusion widened until nothing is
scanned would otherwise pass green, so scanning zero files is itself a failure.

**The rule was widened in the same change, so the rule and its check say the same thing.**
The convention named the em dash, U+2014. The check reads the em-dash CLASS: U+2014, U+2015
HORIZONTAL BAR, and the two- and three-em dashes, which render identically at reading size.
Checking only U+2014 would assert a proxy for the property, and a look-alike would defeat
the rule with the check still green. The en dash U+2013 is deliberately not included: it is
visually distinct and a legitimate range separator, and a check with a false positive gets
disabled by whoever trusts it next.

### The reproduction, which is the condition of this landing

Green on a clean tree proves nothing, so the check was driven red three ways and the tree
restored after each.

| what was done | result |
|---|---|
| `git checkout 5cd2568 -- DECISIONS.md tests/test_rst_a2_...py`, restoring the two files exactly as `3f1cdab` found them | **exit 1**, all five lines named with file, line number and the offending text |
| the same six em dashes present, with `em_dashes(problems)` commented out of `main()` | **exit 0.** The check is what catches them, not something else in the audit |
| every U+2014 swapped for a visually identical U+2015 | **exit 1**, reported as `HORIZONTAL BAR`. The class widening is load-bearing, not decorative |

`make verify-host`: 48 passed, 19 deselected, audit green over 314 tracked text files.

---

## 2026-09-17 - a constraint's test file could escape the history check silently

Found by the auto-review in the sibling repository and present here in the same shape, so
it is fixed here too.

`_owed()` globs `tests/test_rst_*.py` and matches `^test_(rst_[a-z]\d+)_`, which requires an
underscore after the digits. A file the glob finds and the pattern rejects was dropped with
no warning: `test_rst_a6.py` never entered the set, so the check whose job is "a constraint
with no commit behind it fails" never asked about it. **A set built by discarding what it
cannot parse is a set that quietly shrinks to nothing** - the same proxy-for-the-property
shape LESSONS.md now leads with, one layer further in.

Now a named failure listing the files it cannot read. Reproduced with `test_rst_a6.py`
present: red, naming the file.

---

## 2026-09-17 - four more from the auto-review, including the proxy defect inside the proxy fix

**The previous entry and LESSONS.md both overstated what had landed, and the review said
so.** This corrects the claim rather than quietly restating it.

**`SHAPES["port"]` was looser than the pattern it bounded.** It accepted any 1-to-5-digit
run while the pattern was `(?<=:)\d{4,5}`. Widening to `\d{1,5}` satisfied the shape,
normalised every number in the transcript - status codes included - and let a committed
artifact whose `422` refusal had been hand-edited to `200` reproduce cleanly at 22.2%,
under the 25% ceiling. **Moving the bound into the test was necessary and was not
sufficient: a bound looser than the thing it bounds is not a bound.** The shape is now an
ephemeral port, 1024 to 65535.

**And the property is asserted directly, because a shape cannot express it.** A shape says
what a match looks like; it cannot say what a pattern LEAVES ALONE. So tokens the
transcript carries that are not volatile - `422`, `IN_PROGRESS`, `byAssignee`, `WI-002`,
`archived` - are altered and the comparison must notice. Measured, the checks divide
cleanly rather than overlapping:

| widening | what goes red |
|---|---|
| `\d{1,5}` under `port` | the shape, and the scaffolding check |
| `[^<>{}]+` under `generated-id` | all four, the canary included, because the match eats the mutation whole |

**The ceiling was measuring a different string from the one it protected.** It reads the
1,324 characters of text-node content; `normalise()` rewrites the whole 8,096-character
SVG. So a widening confined to attributes was invisible to it. Rather than pick a second
denominator, normalisation must now leave everything outside the transcript byte-identical,
which is the property the ceiling was a proxy for.

**`normalise()` turned valid XML into invalid XML**, substituting `<generated-id>` inside a
text node. Nothing depended on it parsing until a check did. Placeholders are braces now.

**The em dash check dropped any tracked file it could not open, and reported green over
it.** `chmod 000 LESSONS.md` took the population from 314 to 313 and passed over a file
carrying an em dash. `UnicodeDecodeError` is the legitimate binary filter; an `OSError` is
not, and neither is a failed `is_file()`. **This is the identical shape fixed in `_owed()`
two commits later** - a set built by discarding what it cannot parse - and the fix named the
pattern without applying it to the helper introduced alongside. An unreadable tracked file
now refuses the whole run.

**The anti-squash assertion grades all of history, and the docstring claimed more than
that.** A constraint is satisfied permanently by one past sole-naming commit, so squashing
a later branch stays green; only a constraint new to the set can turn it red. The limit is
accepted and now stated in the docstring: the alternative is a range against `origin/main`,
which is empty the moment the branch merges and would be green forever for the wrong
reason. Squashing landed commits means rewriting history, which a separate standing order
already forbids, and this is not the instrument for it.

---

## 2026-09-17 - five more, including a regression the previous entry introduced

**Correction to the entry above, which said the `_owed()` fix landed "two commits later".
It was one.** `tracked_text_files()` arrived in `f8ca188` and `_owed()` was fixed in
`90b3c57`, the commit immediately after. The commit message had it right and the decision
log, which is the copy that survives, was off by one. Appended rather than edited, because
a record that gets rewritten is not a record.

**The two pattern-bounding checks read a string `normalise()` never sees.** They evaluated
`VOLATILE` against text extracted from the SVG; `normalise()` runs on the raw file. So a
pattern anchored on markup matched nothing in the extracted string, the shape loop never
ran, and the ceiling computed 0.0%. Measured with
`(?<=preserve">)[^<]+` under `generated-id`, which collapses every transcript line: **8 of
9 checks green** over a fully disarmed reproduction check, with only the canary red.

**That is the same defect the previous entry claimed to have closed**, one half over. The
scaffolding check closed the attribute half; this was the markup half, and the entry
declared the proxy closed while it stood. Both now read the raw artifact. The ceiling's
denominator stays the transcript, because bounding against the whole file would let a
widening eat every recorded line and still read small against eight kilobytes of
scaffolding; a ratio above 1 is possible and is exactly the alarm it looks like. The same
attack now reddens three of the four.

**A regression this branch introduced: one unreadable file cancelled the whole scan and
named the wrong cause.** The `OSError` refusal returned an empty population, which
discarded the 313 files already read, hid every em dash in them, and printed *"the
exclusions have swallowed it"*. It also dropped the `is_file()` guard with no mention, so a
tracked file merely absent from the worktree - an ordinary mid-edit state - failed the
audit and CI with that same wrong message.

Now separated, because they are different facts: **present and unreadable** is its own
named problem and the scan continues; **tracked and absent** is counted, reported in the
success line, and not fatal, because `git status` already says so and failing there is a
false positive that gets a check disabled. Measured:

| state | exit |
|---|---|
| unreadable file, plus a real em dash elsewhere | 1, and both are reported |
| unreadable file only | 1 |
| absent file only | 0, with the count named |
| absent file, plus a real em dash | 1, the em dash found |

**`ET.fromstring` was unguarded**, so most widenings died with a ParseError before the
check's own message printed, and it silently doubled as a well-formedness test on
`normalise()` output. Parsing now fails with a named reason.

**The scaffolding check claimed "outside the transcript" and asserted "outside all text
content".** `render()` emits a chrome label that is a `<text>` node and is not transcript,
so a normalisation confined to it was invisible to every check here. Only the text runs
inside the group are blanked now, tails included. Low impact today and a claim wider than
its assertion, in the commit whose subject was that exact defect.
