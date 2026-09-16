#!/usr/bin/env python3
"""Enforce: a name means one thing (five defects, one family).

Recorded as a lesson after four instances, and hit a fifth two commits later — which is
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

Deliberately narrow. It does not try to decide what a name means in general — it refuses
the two shapes that have already gone wrong, and says so where it cannot tell.
"""
from __future__ import annotations

import re
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

# .foo > bar, .foo bar — a rule reaching into whatever the class contains.
DESCENDANT = re.compile(r"\.([a-z][a-z0-9-]*)\s*(?:>\s*)?([a-z][a-z0-9-]*)\s*(?:,|\{)")

# <tag ... class="a b"> in any of the template dialects here.
TAG_CLASS = re.compile(r"<([a-z][a-z0-9-]*)\b[^>]*?\bclass(?:Name)?=[\"']([^\"']+)[\"']", re.I)


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
    a compound key and a state word look identical at rest — which is exactly how
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
    for surface, paths in SURFACES.items():
        found: list[str] = []
        files = _files(paths)
        attribute_collisions(files, found)
        class_collisions(files, found)
        problems.extend(f"[{surface}] {p}" for p in found)

    if problems:
        print("NAME AUDIT FAILED — a name is carrying more than one meaning:\n", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}\n", file=sys.stderr)
        return 1

    print("name audit: every checked name carries one meaning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
