#!/usr/bin/env python3
"""Emit design/tokens.yaml into both frontends, so the applications wear the same system.

The token CSS is generated rather than copied by hand because a hand-copied palette is a
second place colours live. Both frontends get the same file, so "they look identical" is
a claim the tokens make true rather than something kept in agreement by care.

Fonts are copied in rather than linked from a shared service: an application whose
typography depends on another process running is an application that looks broken when
it is opened on its own.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "design"))

# One generator, so the frontends and the side-by-side page cannot drift apart.
import tokens  # noqa: E402

TARGETS = {
    "angular": ROOT / "modules" / "angular",
    "react": ROOT / "modules" / "react",
}


def main() -> int:
    css = tokens.token_css()
    fonts = ROOT / "design" / "fonts"

    for name, module in TARGETS.items():
        if not module.is_dir():
            print(f"  {name}: no module directory, skipped")
            continue

        (module / "src" / "tokens.generated.css").write_text(css, encoding="utf-8")

        # One stylesheet, copied into both. Written once in design/ rather than authored
        # per frontend, because "the two look identical" should be true by construction
        # rather than kept true by care — and the first divergence would otherwise be
        # invisible until someone put the two screenshots side by side.
        #
        # The banner is prepended rather than kept in the source file, so design/app.css
        # reads as the thing you edit and both copies read as things you do not. A
        # generated file that does not announce itself gets hand-edited once, by someone
        # in a hurry, and the next render silently reverts their fix.
        (module / "src" / "app.generated.css").write_text(
            "/* GENERATED from design/app.css by scripts/render-app-tokens.py.\n"
            " * Do not edit; edit design/app.css and re-render. */\n"
            + (ROOT / "design" / "app.css").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        # The application wears its own identity hue as its accent. Emitted per module
        # rather than written into the shared stylesheet, because the stylesheet is the
        # thing that must be identical — the accent is the one value that should not be,
        # and it still resolves to a declared token rather than a literal.
        (module / "src" / "accent.generated.css").write_text(
            "/* GENERATED from design/tokens.yaml. Do not edit; edit the tokens. */\n"
            f".app {{ --app-accent: var(--app-accent-{name}); }}\n",
            encoding="utf-8",
        )

        # Vite serves public/ at the root, which is where the generated @font-face rules
        # already point.
        public_fonts = module / "public" / "fonts"
        public_fonts.mkdir(parents=True, exist_ok=True)
        copied = 0
        for font in sorted(fonts.glob("*.woff2")):
            shutil.copy2(font, public_fonts / font.name)
            copied += 1
        print(f"  {name}: tokens written, {copied} fonts copied")

    print("frontend tokens rendered from design/tokens.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
