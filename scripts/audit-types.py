#!/usr/bin/env python3
"""Type-check every TypeScript stack, derived from the manifest.

Both frontends carried three type errors apiece for the entire build, through every green
gate, in a repository whose stated premise is that the Angular and the React were written by
hand. Nothing was looking: Vite strips types with esbuild rather than checking them, vitest
checks none, and no target ever invoked the compiler. The version-floor gap had the same
shape: a check covers what someone thought to name, and everything outside it is trusted
because nothing ever reports it.

The stack set is read from stacks/manifest.yaml, so activating a seventh TypeScript stack
puts it under this check with no edit here. An enumerated list would be the same defect
one level up: a list is a thing someone remembers to extend.

The check runs the compiler inside each stack's own container, which is the object the
claim is about. Type-checking on the host would read whatever node_modules the host
happens to have, and the artifact does not run on the host.

A container that is not running is a failure, not a skip. A check that quietly does nothing
when its subject is absent is the bypass this file exists to close: it would report success
for a stack it never looked at.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

def typescript_stacks() -> list[tuple[str, str, str | None]]:
    """(stack_id, service, command) for every active TypeScript stack in the manifest.

    The command is declared per stack rather than fixed here, because "type-check" is not
    one command across TypeScript. This file first ran `tsc` everywhere, which checks
    Angular's classes and none of its templates: a template naming a member its component
    does not have compiled clean, which was found by injecting exactly that. Angular
    declares `ngc`, React declares `tsc`, and the difference is the manifest's to state.
    """
    manifest = yaml.safe_load((ROOT / "stacks" / "manifest.yaml").read_text()) or {}
    return [
        (stack_id, stack.get("service") or stack_id, stack.get("type_check_command"))
        for stack_id, stack in (manifest.get("stacks") or {}).items()
        if stack.get("active") and stack.get("language") == "typescript"
    ]


def running(service: str) -> bool:
    result = subprocess.run(
        ["docker", "compose", "ps", "-q", service],
        cwd=ROOT, capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def main() -> int:
    stacks = typescript_stacks()
    if not stacks:
        print("type audit: the manifest declares no active TypeScript stack")
        return 0

    problems: list[str] = []
    for stack_id, service, command in stacks:
        if not command:
            # Same rule as the framework floor: an absent declaration is the failure,
            # because absence is what lets a stack go unchecked while the gate stays green.
            problems.append(
                f"{stack_id} is a TypeScript stack and declares no type_check_command.\n"
                f"      Declare one in stacks/manifest.yaml. There is no default: `tsc` is\n"
                f"      wrong for Angular, whose templates it does not read."
            )
            continue
        if not running(service):
            problems.append(
                f"{stack_id}: the '{service}' container is not running, so its sources were\n"
                f"      never type-checked. Bring it up with `docker compose up -d {service}`.\n"
                f"      Reported rather than skipped: a check that passes because it did not\n"
                f"      look is worse than no check."
            )
            continue
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", service, "sh", "-lc", command],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            # tsc writes diagnostics to stdout; a non-zero exit with neither stream is a
            # broken invocation rather than a clean tree, and says so instead of passing.
            detail = (result.stdout + result.stderr).strip() or (
                f"the compiler exited {result.returncode} and printed nothing")
            lines = detail.splitlines()
            shown = "\n".join("      " + line for line in lines[:8])
            more = f"\n      ... and {len(lines) - 8} more" if len(lines) > 8 else ""
            problems.append(f"{stack_id}: does not type-check\n{shown}{more}")

    if problems:
        print("TYPE AUDIT FAILED. A hand-written frontend does not compile:\n", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}\n", file=sys.stderr)
        return 1

    print(f"type audit: {', '.join(s for s, _, _ in stacks)} type-check clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
