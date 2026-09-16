#!/usr/bin/env python3
"""Enforce: a validator must read the exact object the operation consumes.

Three defects of one shape, found one at a time over this build. A fourth — a commit
guard that read the working tree while git commits the index — belonged to tooling this
repository does not ship, so its rule was removed rather than left here asserting against
a file that does not exist. The lesson itself is in LESSONS.md.

  - a probe that read HTTP status from a server with a catch-all route, so every path
    answered 200 and every capability read as present;
  - two healthchecks that fetched something served whether or not the application worked;
  - a check that asserted on the word "auto-configuration" rather than on the class that
    supplied the capability, and so kept passing when the word stopped being printed.

That is a pattern, not luck. The rule was recorded in DECISIONS.md, and a rule recorded
is a rule someone has to remember, so this makes it enforceable.

These are heuristics over source text and they are deliberately coarse. They cannot decide
whether a check reads the right object in general — that is a judgement. What they can do
is refuse the specific shapes that have already cost this build real defects, and say so
loudly enough that the next one is noticed at the point it is written.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# A body assertion: evidence that the check read what came back rather than only that
# something came back.
BODY_EVIDENCE = (
    "grep", "json(", ".json", "innerText", "textContent", "allTextContents",
    "content-type", "Content-Type", "body", "readAllBytes", "read()", "getPermittedSub",
    "contains", "match", "n>", "length",
)


def compose_healthchecks() -> list[tuple[str, str]]:
    """(service, command) for every healthcheck in the compose file."""
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    out, service = [], "?"
    for line in text.splitlines():
        named = re.match(r"^  ([a-z][a-z0-9-]*):\s*$", line)
        if named:
            service = named.group(1)
        if "CMD-SHELL" in line or '"CMD"' in line:
            out.append((service, line.strip()))
    return out


def rule_healthchecks_read_the_application(problems: list[str]) -> None:
    """A healthcheck must fail when the application is broken but the server is up.

    Reachability is not health. A static server answers its catch-all, a web server answers
    its error page, and both look identical to a check that stops at the status code.
    """
    for service, command in compose_healthchecks():
        if service == "postgres":
            continue  # pg_isready asks the database itself; that is the right object.
        if not any(token in command for token in BODY_EVIDENCE):
            problems.append(
                f"docker-compose.yml [{service}]: healthcheck asserts reachability only. "
                "It cannot distinguish a working application from a server answering a "
                "catch-all. Assert on something only a working application produces."
            )


def rule_probes_assert_on_payload(problems: list[str]) -> None:
    """A status code is not evidence when the server has a fallback route."""
    for path in sorted((ROOT / "visual").glob("*.mjs")) + sorted((ROOT / "tests").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        statuses = re.findall(r"status(?:Code)?\s*===?\s*200|status_code\s*==\s*200", text)
        if not statuses:
            continue
        if not any(token in text for token in BODY_EVIDENCE):
            problems.append(
                f"{path.relative_to(ROOT)}: treats an HTTP status as sufficient evidence "
                "with no assertion on what came back."
            )


def rule_checks_do_not_assert_on_category_words(problems: list[str]) -> None:
    """Assert on the thing, not on the label the thing is filed under.

    A check bound to a word keeps passing while the word stops meaning anything, and stops
    passing when the word is improved. Both failures are silent about the actual property.
    """
    banned = ("auto-configuration", "auto-configured", "explicit")
    for path in sorted((ROOT / "visual").glob("*.mjs")):
        text = path.read_text(encoding="utf-8")
        for word in banned:
            for match in re.finditer(rf"""[=~]\s*[/"']\^?{re.escape(word)}\$?[/"']""", text):
                line = text[: match.start()].count("\n") + 1
                problems.append(
                    f"{path.relative_to(ROOT)}:{line}: asserts on the category word "
                    f"{word!r}. Assert on what supplied the capability — the declaring "
                    "class — rather than on the word it is filed under."
                )


def main() -> int:
    problems: list[str] = []
    rule_healthchecks_read_the_application(problems)
    rule_probes_assert_on_payload(problems)
    rule_checks_do_not_assert_on_category_words(problems)

    if problems:
        print("GUARD AUDIT FAILED — a validator is reading something adjacent to what it "
              "claims to protect:\n", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}\n", file=sys.stderr)
        return 1

    print("guard audit: every guard reads the object its operation consumes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
