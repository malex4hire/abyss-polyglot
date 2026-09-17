#!/usr/bin/env python3
"""Enforce: a name means one thing (five defects, one family).

Recorded as a lesson after four instances, and hit a fifth two commits later, which is
the whole point of this file. A rule written down is a rule someone has to remember at the
moment it matters; a rule that runs is a rule.

The five: an attribute read as two shapes, an SSE event spelled two ways across stacks,
a check bound to a label rather than the thing it named, a CSS class naming both the top
chrome and the workload meter, and a data attribute naming both an identifier and a
rolled-up state. Two shapes are checkable and both would have caught real defects here:

  1. An attribute whose values are sometimes an identifier and sometimes a state word is
     two attributes wearing one name. One attribute held a compound key on one panel and
     a single state word on another, so querySelector returned the wrong element.

  2. A class that carries descendant rules and is applied to different kinds of element is
     the CSS version. `.bar` was a <header> and a <span>, and `.bar > span` painted the
     header.

Deliberately narrow. It does not try to decide what a name means in general. It refuses
the two shapes that have already gone wrong, and says so where it cannot tell.

It also carries one punctuation convention, for the same reason the rest of this file
exists: the rule was written down, nothing ran it, and it was broken inside the branch that
wrote it down. It lives here rather than in a new script because this one is already wired
into `make verify-host` and into the CI audits step, and a second audit script for one rule
is wiring that buys nothing.
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SURFACES = {
    "apps": [ROOT / "modules" / "angular" / "src", ROOT / "modules" / "react" / "src",
             ROOT / "design" / "app.css"],
    "page": [ROOT / "side-by-side" / "src", ROOT / "scripts" / "render-side-by-side.py"],
}

TEMPLATE_SUFFIXES = (".ts", ".tsx", ".py", ".html", ".js")

# A value that looks like an identifier rather than a state: a compound key, a stack id
# with a slash, anything carrying a path separator.
KEY_SHAPED = re.compile(r"[a-z0-9-]+/[a-z0-9-]+")

ATTR_USE = re.compile(r'data-([a-z][a-z0-9-]*)\s*=\s*["\']([^"\']*)["\']')
ATTR_BIND = re.compile(r'\[attr\.data-([a-z][a-z0-9-]*)\]\s*=\s*"([^"]*)"')

# .foo > bar, .foo bar: a rule reaching into whatever the class contains.
DESCENDANT = re.compile(r"\.([a-z][a-z0-9-]*)\s*(?:>\s*)?([a-z][a-z0-9-]*)\s*(?:,|\{)")

# <tag ... class="a b"> in any of the template dialects here.
TAG_CLASS = re.compile(r"<([a-z][a-z0-9-]*)\b[^>]*?\bclass(?:Name)?=[\"']([^\"']+)[\"']", re.I)


# ---------------------------------------------------------------------------
# One punctuation convention: no em dash.
#
# Commit fb2c5dc removed every em dash from this repository. That was the rule, nothing
# enforced it, and the branch that recorded the rule put SIX of them back across two files
# before somebody noticed and removed them by hand. A convention maintained by whoever
# notices is a chore this repository generates forever.
#
# The CLASS, not the character. U+2014 is the one the convention named, but U+2015 and the
# two- and three-em dashes render identically at reading size. Checking only U+2014 would
# be checking a proxy for the property: the rule is "no em-dash-looking punctuation", and a
# look-alike would satisfy the narrow check while defeating the rule. This widening is the
# prompt half of the fix and is recorded in DECISIONS.md, so the rule and its check say the
# same thing.
#
# The en dash (U+2013) is deliberately absent: it is visually distinct and a legitimate
# range separator. A check with a false positive is worse than no check, because it gets
# disabled by whoever trusts it next.
# ---------------------------------------------------------------------------

EM_DASH_CLASS = {
    "\u2014": "EM DASH",
    "\u2015": "HORIZONTAL BAR",
    "\u2e3a": "TWO-EM DASH",
    "\u2e3b": "THREE-EM DASH",
}

# Third-party text this repository carries and does not author. Rewriting a vendored
# licence to satisfy a house style is not a thing this check is allowed to ask for.
NOT_OURS = ("licenses/",)


def tracked_text_files() -> list[Path]:
    """Every tracked file that decodes as text, read from git rather than from a list here.

    From git, because a hand-kept set of extensions is the same defect this file is about:
    it is a second copy of "which files are ours" and it goes stale silently. Undecodable
    files are the binaries (fonts, images, the recorded gif) and are skipped by decoding,
    not by name.
    """
    listing = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    if listing.returncode != 0:
        print(f"could not list tracked files: {listing.stderr.strip()}", file=sys.stderr)
        return []

    out, unreadable = [], []
    for name in listing.stdout.split("\0"):
        if not name or name.startswith(NOT_OURS):
            continue
        path = ROOT / name
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # The binaries: fonts, images, the recorded gif. The only legitimate filter
            # here, because it is the one that means "this is not text".
            continue
        except OSError as exc:
            # A tracked file this cannot open is NOT a binary and NOT a pass. Dropping it
            # shrinks the population silently and the audit reports green over a file it
            # never read: `chmod 000 LESSONS.md` took the count from 314 to 313 and passed
            # over an em dash. The same defect as a set built by discarding what it cannot
            # parse, which this repository fixed elsewhere and reintroduced here.
            unreadable.append(f"{name}: {exc.strerror or exc}")
            continue
        out.append(path)

    if unreadable:
        print(
            "these tracked files could not be read, so nothing checked them:\n  "
            + "\n  ".join(unreadable),
            file=sys.stderr,
        )
        return []
    return out


def em_dashes(problems: list[str]) -> int:
    """Returns how many files were scanned, so the caller can report the population."""
    files = tracked_text_files()
    if not files:
        # An exclusion widened until nothing is scanned would otherwise pass green, which
        # is the shape this whole file exists to refuse.
        problems.append(
            "the em dash check scanned no files at all, so it proved nothing. Either the "
            "tree is not a git checkout or the exclusions have swallowed it"
        )
        return 0

    for path in files:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for char, name in EM_DASH_CLASS.items():
                if char in line:
                    problems.append(
                        f"{path.relative_to(ROOT)}:{n} carries {name} ({char!r}). "
                        f"This repository writes ordinary punctuation:\n"
                        f"      {line.strip()[:110]}"
                    )
                    break
    return len(files)


def _files(paths) -> list[Path]:
    out = []
    for path in paths:
        if path.is_file():
            out.append(path)
        elif path.is_dir():
            out.extend(p for p in path.rglob("*")
                       if p.is_file() and p.suffix in TEMPLATE_SUFFIXES + (".css",)
                       and "node_modules" not in p.parts and not p.name.endswith(".generated.css"))
    return out


def attribute_collisions(files: list[Path], problems: list[str]) -> None:
    """An attribute the code selects on must be written in exactly one place.

    Shape-matching the values does not work: in a renderer both sides are interpolated, so
    a compound key and a state word look identical at rest, which is exactly how
    the original offender passed a first version of this check while being the defect it was
    written for. What is visible is where an attribute is *written*. If JavaScript looks up
    `[data-x]` to find one element, and more than one place in the surface emits
    `data-x=`, then querySelector is choosing between them by document order, which is not
    a decision anybody made.
    """
    selected: set[str] = set()
    for path in files:
        if path.suffix != ".js":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        selected.update(re.findall(r"querySelector(?:All)?\(\s*[\"'][^\"']*\[data-([a-z][a-z0-9-]*)\]",
                                   text))

    sites: dict[str, set[str]] = defaultdict(set)
    for path in files:
        if path.suffix == ".css":
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for name in set(re.findall(r"data-([a-z][a-z0-9-]*)\s*=", line)):
                sites[name].add(f"{path.relative_to(ROOT)}:{n}")

    for name in sorted(selected):
        where = sites.get(name, set())
        if len(where) > 1:
            problems.append(
                f"data-{name} is selected in JavaScript and written in more than one place:\n"
                f"      {chr(10).join('      ' + w for w in sorted(where)[:4]).strip()}\n"
                f"      querySelector picks whichever comes first, which is not a decision.\n"
                f"      Prefix by component so each name belongs to one of them."
            )


def class_collisions(files: list[Path], problems: list[str]) -> None:
    """One class with descendant rules, applied to different kinds of element."""
    reaching: set[str] = set()
    for path in files:
        if path.suffix != ".css":
            continue
        for owner, _child in DESCENDANT.findall(path.read_text(encoding="utf-8", errors="replace")):
            reaching.add(owner)

    applied: dict[str, set[str]] = defaultdict(set)
    for path in files:
        if path.suffix == ".css":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for tag, classes in TAG_CLASS.findall(text):
            for token in classes.split():
                if token in reaching:
                    applied[token].add(tag.lower())

    for name, tags in sorted(applied.items()):
        if len(tags) > 1:
            problems.append(
                f".{name} carries descendant rules and is applied to {', '.join(sorted(tags))}.\n"
                f"      A rule written for one of those paints the other. Prefix by component."
            )


def main() -> int:
    problems: list[str] = []
    scanned = em_dashes(problems)
    for surface, paths in SURFACES.items():
        found: list[str] = []
        files = _files(paths)
        attribute_collisions(files, found)
        class_collisions(files, found)
        problems.extend(f"[{surface}] {p}" for p in found)

    if problems:
        print("NAME AUDIT FAILED:\n", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}\n", file=sys.stderr)
        return 1

    print(
        "name audit: every checked name carries one meaning, and "
        f"{scanned} tracked text files carry no em-dash-class character "
        f"({', '.join(sorted(EM_DASH_CLASS.values()))})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
