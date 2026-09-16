#!/usr/bin/env python3
"""design/tokens.yaml, rendered into CSS custom properties.

Every visual value in this repository — colour, face, step on the type scale, spacing
step, rule width, transition duration — is declared once in tokens.yaml and emitted from
here. Both frontends and the side-by-side page import the same generated stylesheet, so
"the two applications look identical" is a property of how they are built rather than a
claim two teams keep true by care.

A stylesheet that names a hex value directly is the defect this exists to prevent: it
puts a second place colours live, and the first divergence is invisible until someone
puts two screenshots side by side.

The renderer knows mechanisms, not names. It contains no list of stacks and no list of
statuses; each governed set comes from its own declaring file.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "design" / "fonts"


def load(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if doc is None:
        return {}
    return doc


def flatten(section: dict) -> dict:
    """{(stack, key): entry} from a mapping nested stack -> key -> entry."""
    flat = {}
    for stack_id, entries in (section or {}).items():
        for entry_id, entry in (entries or {}).items():
            flat[(stack_id, entry_id)] = {**(entry or {}), "stack": stack_id}
    return flat


TOKENS = load(ROOT / "design" / "tokens.yaml")


def member_groups() -> dict:
    """Every governed set in the token file: any top-level group declaring members.

    Derived rather than listed. A list of group names here would mean adding a set to
    tokens.yaml and silently emitting nothing for it — which is how two sets stayed in
    this file for weeks after the thing they described was deleted.
    """
    return {
        name: block for name, block in TOKENS.items()
        if isinstance(block, dict) and isinstance(block.get("members"), dict)
    }


# Two groups are bound to elements elsewhere rather than by the generic badge rule below:
# stacks get the chip and edge treatment written just above it, and status is styled by
# the application stylesheet, which owns how a work item's state is drawn.
_BOUND_ELSEWHERE = ("stacks", "status")


def token_css() -> str:
    """Every visual value, emitted as custom properties from design/tokens.yaml."""
    lines = ["/* GENERATED from design/tokens.yaml. Do not edit; edit the tokens. */", ""]

    faces = (TOKENS.get("type") or {}).get("faces") or {}
    files = {"display": "Fraunces", "body": "PublicSans", "mono": "JetBrainsMono"}
    for role, spec in faces.items():
        stem = files.get(role)
        if not stem:
            continue
        for index in (0, 1):
            path = FONTS / f"{stem}-{index}.woff2"
            if path.exists():
                lines += [
                    "@font-face {",
                    f'  font-family: "{spec["family"]}";',
                    f'  src: url("fonts/{path.name}") format("woff2");',
                    "  font-display: swap;",
                    "  font-weight: 100 900;",
                    "}",
                ]
    lines.append("")
    trailing: list = []
    lines.append(":root {")

    for name, value in (TOKENS.get("surface") or {}).items():
        lines.append(f"  --surface-{name}: {value};")
    # Two aliases so a stylesheet can say what it means. Both resolve to a declared token;
    # neither introduces a value.
    for name, value in (TOKENS.get("decoration") or {}).items():
        lines.append(f"  --{name}: {value};")
    lines.append("  --arrival-wash: var(--arrival);")
    for name, value in (TOKENS.get("foreground") or {}).items():
        lines.append(f"  --fg-{name}: {value};")

    for group, block in member_groups().items():
        for member, spec in block["members"].items():
            slug = str(member).lower()
            for prop, value in (spec or {}).items():
                lines.append(f"  --{group}-{slug}-{prop.replace('_', '-')}: {value};")

    scale = (TOKENS.get("type") or {}).get("scale") or {}
    for step, size in scale.items():
        lines.append(f"  --type-{step}: {size}px;")
    code = (TOKENS.get("type") or {}).get("code") or {}
    lines.append(f"  --code-size: {code.get('size_px')}px;")
    lines.append(f"  --code-line: {code.get('line_height')};")
    for role, spec in faces.items():
        lines.append(f'  --face-{role}: "{spec["family"]}";')

    spacing = TOKENS.get("spacing") or {}
    for index, step in enumerate(spacing.get("scale") or []):
        lines.append(f"  --space-{index}: {step}px;")
    for name, width in (spacing.get("measures") or {}).items():
        lines.append(f"  --measure-{name}: {width}rem;")

    seam = TOKENS.get("seam") or {}
    lines.append(f"  --seam-rule: {seam.get('rule_width')}px;")
    lines.append(f"  --seam-reveal: {seam.get('reveal_ms')}ms;")
    lines.append(f"  --seam-wash: {seam.get('wash_alpha')};")
    lines.append(f"  --control-ease: {seam.get('control_ms')}ms;")
    lines.append(f"  --caret: {seam.get('caret_px')}px;")
    lines.append(f"  --split-breakpoint: {seam.get('split_breakpoint')}px;")
    # The wide default. The media query below flips it to a single column.
    lines.append("  --split-columns: 1fr 1fr;")

    # A19: the application surface. Dark under :root, light under an explicit theme, so the
    # default is dark and the choice is one attribute on the document.
    app = TOKENS.get("app") or {}
    density = app.get("density") or {}
    for name, value in density.items():
        suffix = "px" if name.endswith("_px") else (
            "rem" if name.endswith("_rem") else ("em" if name.endswith("_em") else "")
        )
        lines.append(f"  --app-{name.rsplit('_', 1)[0].replace('_', '-')}: {value}{suffix};")
    apptype = app.get("type") or {}
    lines.append(f"  --app-display-weight: {apptype.get('display_weight')};")
    lines.append(f"  --app-label-tracking: {apptype.get('label_tracking_em')}em;")

    for theme, scope in (("dark", ":root"), ("light", ':root[data-theme="light"]')):
        palette = (app.get("themes") or {}).get(theme) or {}
        accents = (app.get("accents") or {}).get(theme) or {}
        status = (app.get("status") or {}).get(theme) or {}
        block = [f"  --app-{name}: {value};" for name, value in palette.items()]
        block += [f"  --app-accent-{slug}: {value};" for slug, value in accents.items()]
        block += [f"  --app-status-{slug}: {value};" for slug, value in status.items()]
        if theme == "dark":
            lines.extend(block)
        else:
            trailing.extend(["", f"{scope} {{", *block, "}"])

    lines.append("}")

    # Bind each semantic token to the element that carries it. Emitting a token and
    # never applying it satisfies every structural check and renders a colourless page,
    # which is what happened until a browser looked at it.
    lines.append("")
    for stack_id in member_groups().get("stacks", {}).get("members", {}):
        slug = str(stack_id).lower()
        lines.append(
            f'.chip[data-stack="{stack_id}"] {{ background: var(--stacks-{slug}-color); }}'
        )
        lines.append(
            f'.side[data-stack="{stack_id}"] {{ '
            f"box-shadow: inset var(--seam-rule) 0 0 var(--stacks-{slug}-color); }}"
        )
    for group, block in member_groups().items():
        if group in _BOUND_ELSEWHERE:
            continue
        attribute = group[:-1] if group.endswith("s") else group
        for member, spec in block["members"].items():
            slug = str(member).lower()
            if (spec or {}).get("color"):
                lines.append(
                    f'.badge[data-{attribute}="{member}"] {{ '
                    f"color: var(--{group}-{slug}-color); "
                    f"border-color: var(--{group}-{slug}-color); }}"
                )
            if (spec or {}).get("weight"):
                lines.append(
                    f'.badge[data-{attribute}="{member}"] {{ '
                    f"font-weight: var(--{group}-{slug}-weight); }}"
                )
            if (spec or {}).get("border_style"):
                lines.append(
                    f'.badge[data-{attribute}="{member}"] {{ '
                    f"border-style: var(--{group}-{slug}-border-style); }}"
                )
    # The breakpoint, emitted as a custom PROPERTY rather than as a rule.
    #
    # It was a rule — `.split { grid-template-columns: 1fr }` inside a media query — and it
    # never fired. The page's own stylesheet loads after this one and sets the same
    # property at the same specificity, so the later sheet won at every width and the two
    # frames stayed side by side down to 400px, 168px each. A media query that loses on
    # source order is a media query that does nothing, and nothing said so.
    #
    # A custom property on :root cannot lose that way: the media query overrides the VALUE,
    # and whichever rule consumes it resolves the overridden one regardless of order.
    lines.append("")
    lines.append(f"@media (max-width: {seam.get('split_breakpoint')}px) {{")
    lines.append("  :root { --split-columns: 1fr; }")
    lines.append("}")
    lines.extend(trailing)
    return "\n".join(lines) + "\n"



if __name__ == "__main__":
    print(token_css(), end="")
