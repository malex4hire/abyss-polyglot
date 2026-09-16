#!/usr/bin/env python3
"""Render the side-by-side page.

The pair contrast applied to the running software instead of to source. Two frames, two
frameworks, one stylesheet generated from one token file — so "they look the same" is a
property of how they are built rather than a claim, and a divergence shows up here the
moment it exists.

One selector drives both frames by re-pointing each at the same backend. A change made in
the left frame appears in the right one through the change stream, with nobody touching
the right frame. That is the thing this page exists to show, and it is the one claim in
this repository that a screenshot cannot fake.

Nothing here is enumerated. Which frontends exist, where they are served, and which
backends are selectable all come from stacks/manifest.yaml, so a stack activated there
appears on this page with no edit to this file — and no port literal lives outside the
manifest.
"""
from __future__ import annotations

import html
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "design"))

import tokens  # noqa: E402

SRC = ROOT / "side-by-side" / "src"
DIST = ROOT / "side-by-side" / "dist"

MANIFEST = tokens.load(ROOT / "stacks" / "manifest.yaml")
ACTIVE = {k: v for k, v in (MANIFEST.get("stacks") or {}).items() if v.get("active")}
MEMBERS = (tokens.TOKENS.get("stacks") or {}).get("members") or {}


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def label(stack_id: str) -> str:
    return str((MEMBERS.get(stack_id) or {}).get("label") or stack_id)


def glyph(stack_id: str) -> str:
    return str((MEMBERS.get(stack_id) or {}).get("glyph") or "")


def frontend_origins() -> dict:
    """Where each frontend is served, from the manifest. No port literal here."""
    return {
        sid: f"http://localhost:{stack['port']}"
        for sid, stack in ACTIVE.items()
        if stack.get("role") == "frontend" and stack.get("port")
    }


def render() -> str:
    origins = frontend_origins()
    if len(origins) < 2:
        raise SystemExit(
            "the manifest declares fewer than two active frontends; there is no pair to"
            " put side by side"
        )
    left, right = sorted(origins)[:2]

    options = "".join(
        f'<option value="{esc(sid)}">{esc(label(sid))}</option>'
        for sid, stack in sorted(ACTIVE.items())
        if stack.get("role") == "backend"
    )
    frames = "".join(
        f'<div class="split-side side" data-stack="{esc(name)}">'
        # The chip carries the declared label and glyph, not the bare id: a stack marked
        # by colour alone is a stack nobody who cannot see the colour can identify.
        f'<h2><span class="chip" data-stack="{esc(name)}">'
        f"{esc(glyph(name))} {esc(label(name))}</span></h2>"
        f'<iframe data-app-frame="{esc(name)}" title="{esc(label(name))} application" '
        f'src="{esc(origins[name])}/"></iframe>'
        "</div>"
        for name in (left, right)
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The same application, twice</title>
<link rel="stylesheet" href="tokens.generated.css">
<link rel="stylesheet" href="side-by-side.css">
<script type="module" src="side-by-side.js"></script>
</head>
<body>
<main>
<div class="page-head">
<h1>The same application, twice</h1>
<p class="lede">Two frameworks, one contract, one stylesheet generated from one token
file. Change something on either side and watch it arrive on the other: that is the
change stream, not a refresh.</p>
<section class="split-controls"><label>backend
<select data-testid="split-backend">{options}</select></label></section>
</div>
<section class="split" data-testid="split">{frames}</section>
</main>
</body>
</html>
"""


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "index.html").write_text(render(), encoding="utf-8")
    (DIST / "tokens.generated.css").write_text(tokens.token_css(), encoding="utf-8")
    for name in ("side-by-side.css", "side-by-side.js"):
        shutil.copy2(SRC / name, DIST / name)

    # Self-hosted, for the same reason the applications self-host: a page whose
    # typography arrives from someone else's CDN is a page that renders wrong with no
    # route to the outside, which is a state this demo is meant to survive.
    fonts = DIST / "fonts"
    fonts.mkdir(exist_ok=True)
    copied = 0
    for font in sorted((ROOT / "design" / "fonts").glob("*.woff2")):
        shutil.copy2(font, fonts / font.name)
        copied += 1

    print(f"side-by-side page rendered to {DIST.relative_to(ROOT)} ({copied} fonts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
