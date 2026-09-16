"""R-6 — the two frontends differ in framework and in nothing else that matters.

Two things are checked, and they are the two halves of "one contract, consumed unmodified
by every frontend" — the claim R-4 deliberately does not make.

First: both static servers are byte-identical. Every frontend has to proxy the contract
to whichever backend was selected, serve a single-page app's catch-all, and report its
own runtime. None of that is framework work, so if the two files ever diverge the
difference is not Angular-versus-React — it is one of them having been given an advantage.
Comparing bytes is the cheapest possible way to know, and it is exact.

Second: neither frontend's source contains a list of backends. Both read the selectable
set from their own server at runtime, which reads it from the generated environment,
which reads the manifest. A backend activated in the manifest therefore appears as an
option in both applications with no change to either — and a backend list hard-coded in a
component is the kind of thing that stays correct for exactly as long as nobody adds a
backend.
"""

from __future__ import annotations

import re

import pytest

import spine

SERVER_FILE = "serve.mjs"


def _frontend_module(sid: str, stack: dict):
    return spine.source_root(sid, stack).parent


def test_the_manifest_declares_a_pair_of_frontends():
    fes = spine.frontends()
    assert len(fes) >= 2, (
        "fewer than two active frontends; there is no pair to compare and the "
        "side-by-side page has nothing to put side by side"
    )
    for sid, stack in sorted(fes.items()):
        assert stack.get("pair") in fes, (
            f"frontend '{sid}' declares pair {stack.get('pair')!r}, which is not an "
            "active frontend"
        )


def test_every_frontend_static_server_is_byte_identical():
    fes = spine.frontends()
    assert fes, "no active frontends"

    contents = {}
    for sid, stack in sorted(fes.items()):
        path = _frontend_module(sid, stack) / SERVER_FILE
        spine.require_file(path, f"{sid} static server")
        contents[sid] = path.read_bytes()

    distinct = {v for v in contents.values()}
    if len(distinct) > 1:
        sizes = ", ".join(f"{sid}={len(v)}B" for sid, v in sorted(contents.items()))
        pytest.fail(
            f"the frontends' {SERVER_FILE} files differ ({sizes}). Everything in that "
            "file is framework-independent work — proxying, the single-page catch-all, "
            "the runtime report — so a difference here is one frontend being given an "
            "advantage the other does not have, which makes the pair comparison worthless"
        )


def test_no_frontend_source_carries_a_list_of_backends():
    """The selectable set is read at runtime, never written into a component."""
    stack_ids = sorted(spine.stacks())
    backend_ids = sorted(spine.backends())
    assert backend_ids, "the manifest declares no active backends"

    offenders = []
    for sid, stack in sorted(spine.frontends().items()):
        root = spine.source_root(sid, stack)
        spine.require_dir(root, f"{sid} source root")

        # The module's own test tree is excluded, and the exclusion is narrow: the claim
        # is about what the SHIPPED application carries. A unit test naming a backend is
        # using the id as an arbitrary base URL to assert a subscription against, which is
        # a fixture choice, not a stack list the application depends on.
        test_root = spine.REPO_ROOT / spine.stack_field(sid, stack, "test_root")

        for path in spine.iter_repo_files((".ts", ".tsx", ".js", ".jsx"), root=root):
            if test_root in path.parents:
                continue
            # Comments are blanked rather than skipped by line. A paragraph explaining why
            # two stacks share a base image spans several lines, and only its first one
            # starts with a comment marker.
            for n, line in enumerate(
                spine.strip_comments(spine.text_of(path)).splitlines(), start=1
            ):
                named = [b for b in backend_ids if b in line]
                if named:
                    offenders.append(
                        f"{spine._rel(path)}:{n}: names backend(s) {', '.join(named)}: "
                        f"{line.strip()}"
                    )
    assert not offenders, (
        "frontend source must carry no backend list; the set is read at runtime from the "
        "manifest, so activating a backend needs no frontend change:\n  "
        + "\n  ".join(offenders)
    )

    # And the server that supplies it must genuinely read it from the environment, or the
    # check above passes on a frontend that simply has no backend selector at all.
    for sid, stack in sorted(spine.frontends().items()):
        server = spine.text_of(_frontend_module(sid, stack) / SERVER_FILE)
        assert "BACKENDS_JSON" in server, (
            f"'{sid}' static server reads no backend set from its environment, so the "
            "absence of a list in its source proves nothing"
        )
        # Stripped, like the source scan above. The comment explaining why two JVM stacks
        # report an identical runtime version is exactly the kind of prose this file exists
        # to keep — flagging it would teach the next reader to delete the explanation
        # rather than the coupling.
        code = spine.strip_comments(server)
        named = sorted(b for b in stack_ids if b not in {sid} and b in code)
        assert not named, (
            f"'{sid}' static server names another stack in code: {', '.join(named)}"
        )


def test_both_frontends_render_from_the_same_generated_stylesheet():
    """"They look identical" is a property of how they are built, or it is a claim.

    The generated files are compared rather than the token file, because the token file
    being correct says nothing about what actually shipped into each module.
    """
    fes = spine.frontends()
    generated = {}
    for sid, stack in sorted(fes.items()):
        for name in ("tokens.generated.css", "app.generated.css"):
            path = spine.source_root(sid, stack) / name
            spine.require_file(path, f"{sid} {name}")
            generated.setdefault(name, {})[sid] = path.read_bytes()

    for name, by_stack in sorted(generated.items()):
        if len({v for v in by_stack.values()}) > 1:
            pytest.fail(
                f"{name} differs between frontends "
                + ", ".join(f"{sid}={len(v)}B" for sid, v in sorted(by_stack.items()))
                + ". Re-run scripts/render-app-tokens.py; a hand-edited copy is a second "
                "place the design system lives"
            )


def test_the_generated_stylesheets_are_generated_and_say_so():
    """A generated file that does not announce itself gets hand-edited, once, by someone
    in a hurry — and the next render silently reverts their fix."""
    unmarked = []
    for sid, stack in sorted(spine.frontends().items()):
        for path in spine.iter_repo_files((".css",), root=spine.source_root(sid, stack)):
            if not path.name.endswith(".generated.css"):
                continue
            head = spine.text_of(path)[:200]
            if not re.search(r"GENERATED", head):
                unmarked.append(spine._rel(path))
    assert not unmarked, (
        "generated stylesheets must carry a generated-from banner:\n  " + "\n  ".join(unmarked)
    )
