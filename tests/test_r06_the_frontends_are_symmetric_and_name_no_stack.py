"""R-6: the two frontends differ in framework and in nothing else that matters.

Two things are checked, and they are the two halves of "one contract, consumed unmodified
by every frontend", which is the claim R-4 deliberately does not make.

First: both static servers are byte-identical. Every frontend has to proxy the contract
to whichever backend was selected, serve a single-page app's catch-all, and report its
own runtime. None of that is framework work, so if the two files ever diverge the
difference is not Angular-versus-React: it is one of them having been given an advantage.
Comparing bytes is the cheapest possible way to know, and it is exact.

Second: neither frontend's source contains a list of backends. Both read the selectable
set from their own server at runtime, which reads it from the generated environment,
which reads the manifest. A backend activated in the manifest therefore appears as an
option in both applications with no change to either, and a backend list hard-coded in a
component is the kind of thing that stays correct for exactly as long as nobody adds a
backend.
"""

from __future__ import annotations

import re

import pytest

import spine

# Files that must be byte-identical in both frontends, relative to the module root.
# None of this is framework work (serving the bundle, proxying the contract, reporting a
# height to an embedding page), so a difference in any of them is one application being
# given an advantage the other does not have.
SHARED_FILES = ("serve.mjs", "src/lib/embed.ts")
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


@pytest.mark.parametrize("shared", SHARED_FILES)
def test_every_shared_frontend_file_is_byte_identical(shared):
    fes = spine.frontends()
    assert fes, "no active frontends"

    contents = {}
    for sid, stack in sorted(fes.items()):
        path = _frontend_module(sid, stack) / shared
        spine.require_file(path, f"{sid} {shared}")
        contents[sid] = path.read_bytes()

    if len({v for v in contents.values()}) > 1:
        sizes = ", ".join(f"{sid}={len(v)}B" for sid, v in sorted(contents.items()))
        pytest.fail(
            f"the frontends' {shared} files differ ({sizes}). Nothing in that file is "
            "framework work, so a difference here is one frontend being given an advantage "
            "the other does not have, which makes the pair comparison worthless"
        )


def test_both_frontends_report_their_height_to_an_embedder():
    """Declared and imported, or the page falls back to a fixed height and stretches them.

    Shipping the helper and never calling it is the shape this repository keeps finding:
    the file exists, the byte-identical check above passes, and nothing runs.
    """
    silent = []
    for sid, stack in sorted(spine.frontends().items()):
        entry = [
            p for p in spine.iter_repo_files((".ts", ".tsx"), root=spine.source_root(sid, stack))
            if p.stem == "main"
        ]
        assert entry, f"'{sid}' has no main entry point"
        # A CALL, not a mention. The first spelling of this searched for the name and
        # was satisfied by the import line, so deleting the call left it green, and that
        # is a check that could not fail for the reason it claimed, caught by deleting
        # the call and watching it pass.
        called = False
        for path in entry:
            for line in spine.strip_comments(spine.text_of(path)).splitlines():
                if line.strip().startswith(("import ", "export ")):
                    continue
                if re.search(r"\breportHeightToEmbedder\s*\(", line):
                    called = True
        if not called:
            silent.append(sid)
    assert not silent, (
        "these frontends never call reportHeightToEmbedder, so the side-by-side page "
        "cannot size their frames and falls back to a fixed height: " + ", ".join(silent)
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
        # to keep, because flagging it would teach the next reader to delete the explanation
        # rather than the coupling.
        code = spine.strip_comments(server)
        named = sorted(b for b in stack_ids if b not in {sid} and b in code)
        assert not named, (
            f"'{sid}' static server names another stack in code: {', '.join(named)}"
        )


def test_every_test_id_the_browser_drivers_query_exists_in_a_frontend():
    """A driver querying a test id that no frontend renders cannot ever pass.

    This is the check that was missing. A driver asserted on
    `[data-testid=workload-loading]`, neither frontend carried that attribute, and the
    count was therefore zero on every run for the life of the build, while the failure
    message blamed the machine for answering too fast. It read as flakiness, so it was
    tolerated rather than investigated.

    Deterministic and host-side: the drivers name the ids, the frontends render them, and
    the two sets are compared by reading. No browser, no timing, no judgement.
    """
    frontends = spine.frontends()
    assert frontends, "no active frontends"

    def ids_in(root) -> set:
        found = set()
        for path in spine.iter_repo_files((".ts", ".tsx", ".js", ".jsx", ".html", ".py"), root=root):
            text = spine.text_of(path)
            found |= set(re.findall(r'data-testid=[\"\']([^\"\']+)[\"\']', text))
            # Angular binds some of them, and a bound attribute is still an attribute.
            found |= set(re.findall(r'\[attr\.data-testid\]=[\"\']([^\"\']+)[\"\']', text))
        return found

    # Per frontend, not pooled. A union would let one frontend drop an id while the other
    # kept it, which is the pair silently diverging, and the drivers run against both.
    per_frontend = {
        sid: ids_in(spine.source_root(sid, stack)) for sid, stack in sorted(frontends.items())
    }
    for sid, found in per_frontend.items():
        assert found, f"'{sid}' renders no test id; there is nothing for a driver to find"

    # The side-by-side page is a separate surface with its own ids, rendered by its own
    # script rather than by either frontend.
    page_ids = ids_in(spine.REPO_ROOT / "side-by-side") | ids_in(spine.REPO_ROOT / "scripts")

    in_every_frontend = set.intersection(*per_frontend.values())
    rendered = in_every_frontend | page_ids

    drivers = spine.REPO_ROOT / "visual"
    spine.require_dir(drivers, "browser drivers")

    queried: dict[str, str] = {}
    for path in spine.iter_repo_files((".mjs",), root=drivers):
        source = spine.strip_comments(spine.text_of(path))
        for match in re.finditer(r'data-testid=([A-Za-z0-9_-]+)', source):
            queried.setdefault(match.group(1), spine._rel(path))
        # at("x") / locator("[data-testid=x]") both reduce to the same name.
        for match in re.finditer(r'\bat\(\s*[\"\']([A-Za-z0-9_-]+)[\"\']', source):
            queried.setdefault(match.group(1), spine._rel(path))

    missing = []
    for name, where in sorted(queried.items()):
        if name in rendered:
            continue
        carriers = sorted(sid for sid, found in per_frontend.items() if name in found)
        detail = (
            f"rendered only by {', '.join(carriers)}" if carriers
            else "rendered by nothing in this repository"
        )
        missing.append(f"{name}  (queried by {where}; {detail})")
    assert not missing, (
        "browser drivers query test ids that not every frontend renders, so those "
        "assertions cannot pass, or can pass against only one half of the pair:\n  "
        + "\n  ".join(missing)
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
    in a hurry, and the next render silently reverts their fix."""
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
