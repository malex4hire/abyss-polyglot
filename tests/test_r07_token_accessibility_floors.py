"""R-7: every encoded distinction is complete, distinct, and legible.

A governed set declares whether it is colour-encoded. Hue separation applies to
colour-encoded sets only; a non-colour encoding (a label, a glyph, a border style, an
ink weight) is required of every set regardless.

That second half is the one that gets skipped, and it is the one that matters: a
distinction carried by colour alone disappears for a meaningful share of the people who
look at it, and it disappears entirely in a printout or a grayscale screenshot in a
slide deck.

An earlier version of this file forced a hue onto every member of every set, which is why
it failed the one set that is deliberately encoded by ink weight instead. A check that
conflicts with a deliberate choice is usually the thing that changed by mistake.

Floors are read from tokens.yaml, never written down here, so raising a floor is a
one-line edit to the declaration and the check follows.
"""

from __future__ import annotations

import pytest

import spine

NON_COLOUR_ENCODINGS = ("label", "glyph", "shape", "border_style", "position", "weight")

# Which sets carry tokens is read from the token file itself: a group declaring members
# is a governed set. Listing them here would make this file the declaration.
def _token_groups() -> dict[str, dict]:
    doc = spine.read_yaml(spine.TOKENS, "design tokens")
    groups = {
        name: block for name, block in doc.items()
        if isinstance(block, dict) and isinstance(block.get("members"), dict)
    }
    if not groups:
        pytest.fail(
            f"MALFORMED INPUT: {spine._rel(spine.TOKENS)} declares no token group with "
            "members; there is no encoded distinction to check"
        )
    return groups


def _floors() -> tuple[float, float]:
    doc = spine.read_yaml(spine.TOKENS, "design tokens")
    floors = doc.get("floors")
    if not isinstance(floors, dict):
        pytest.fail(f"MALFORMED INPUT: {spine._rel(spine.TOKENS)} declares no 'floors' section")
    for key in ("contrast", "hue_separation"):
        if key not in floors:
            pytest.fail(
                f"MALFORMED INPUT: floors in {spine._rel(spine.TOKENS)} declares no '{key}'"
            )
    return float(floors["contrast"]), float(floors["hue_separation"])


def _is_colour_encoded(name: str, block: dict) -> bool:
    if "color_encoded" not in block:
        pytest.fail(
            f"MALFORMED INPUT: token group '{name}' does not declare color_encoded; that "
            "declaration is what hue separation is scoped by, and a set that silently "
            "defaults is a set nobody decided about"
        )
    return bool(block["color_encoded"])


def test_every_active_stack_resolves_to_a_token():
    """The stack set comes from the manifest, so activating a stack with no token is a
    failure here rather than an unstyled chip nobody notices."""
    members = _token_groups()["stacks"]["members"]
    missing = sorted(s for s in spine.active_stacks() if not isinstance(members.get(s), dict))
    assert not missing, (
        "stacks activated in the manifest with no identity token: " + ", ".join(missing)
    )


def test_every_member_of_every_set_resolves_to_a_non_colour_encoding():
    """Required of every set, whether or not it is colour-encoded."""
    incomplete = []
    for name, block in sorted(_token_groups().items()):
        for member, entry in sorted(block["members"].items()):
            if not isinstance(entry, dict):
                incomplete.append(f"{name}: '{member}' resolves to no token")
                continue
            if not [k for k in NON_COLOUR_ENCODINGS if str(entry.get(k, "")).strip()]:
                incomplete.append(
                    f"{name}: '{member}' has no non-colour encoding (needs one of "
                    + ", ".join(NON_COLOUR_ENCODINGS) + ")"
                )
    assert not incomplete, (
        "no distinction may be carried by colour alone:\n  " + "\n  ".join(incomplete)
    )


def test_colour_encoded_sets_clear_the_hue_separation_floor():
    _, hue_floor = _floors()
    violations = []
    for name, block in sorted(_token_groups().items()):
        if not _is_colour_encoded(name, block):
            continue
        members = block["members"]
        colors = {
            m: entry["color"] for m, entry in sorted(members.items())
            if isinstance(entry, dict) and entry.get("color")
        }
        absent = sorted(set(members) - set(colors))
        if absent:
            violations.append(
                f"{name} is declared colour-encoded but these members carry no colour: "
                + ", ".join(absent)
            )
        items = sorted(colors.items())
        for i, (a, ca) in enumerate(items):
            for b, cb in items[i + 1:]:
                sep = spine.hue_separation(ca, cb)
                if sep < hue_floor:
                    violations.append(
                        f"{name}: '{a}' ({ca}) and '{b}' ({cb}) are {sep:.1f}deg apart, "
                        f"below the declared floor of {hue_floor}deg"
                    )
    assert not violations, "hue separation floor breached:\n  " + "\n  ".join(violations)


def test_a_set_declared_not_colour_encoded_assigns_no_distinct_hues():
    """Otherwise the declaration is decorative and the set is colour-encoded anyway."""
    offenders = []
    for name, block in sorted(_token_groups().items()):
        if _is_colour_encoded(name, block):
            continue
        colors = {
            m: entry["color"] for m, entry in sorted(block["members"].items())
            if isinstance(entry, dict) and entry.get("color")
        }
        if len({c.upper() for c in colors.values()}) > 1:
            offenders.append(
                f"{name} declares color_encoded: false but assigns distinct hues: "
                + ", ".join(f"{m}={c}" for m, c in sorted(colors.items()))
            )
    assert not offenders, (
        "a set declared not colour-encoded must not carry distinct hues:\n  "
        + "\n  ".join(offenders)
    )


def test_every_foreground_background_pair_meets_the_contrast_floor():
    """Across groups, never within one.

    Checking ink as though it were a ground would fail every identity hue against every
    other identity hue and prove nothing, because they are never rendered on each other.
    """
    contrast_floor, _ = _floors()
    doc = spine.read_yaml(spine.TOKENS, "design tokens")

    backgrounds = doc.get("surface")
    foregrounds = doc.get("foreground")
    for name, group in (("surface", backgrounds), ("foreground", foregrounds)):
        if not isinstance(group, dict) or not group:
            pytest.fail(f"MALFORMED INPUT: {spine._rel(spine.TOKENS)} declares no '{name}' group")

    # Colour-encoded set members are foregrounds too: they render as text and marks.
    pairs: list[tuple[str, str]] = [
        (f"foreground.{n}", str(v)) for n, v in sorted(foregrounds.items())
        if str(v).startswith("#")
    ]
    for name, block in sorted(_token_groups().items()):
        if not _is_colour_encoded(name, block):
            continue
        for member, entry in sorted(block["members"].items()):
            if isinstance(entry, dict) and entry.get("color"):
                pairs.append((f"{name}.{member}", entry["color"]))

    failures = []
    for label, fg in pairs:
        for bg_name, bg in sorted(backgrounds.items()):
            if not isinstance(bg, str) or not bg.startswith("#"):
                continue
            ratio = spine.contrast_ratio(fg, bg)
            if ratio < contrast_floor:
                failures.append(
                    f"{label} ({fg}) on surface.{bg_name} ({bg}) is {ratio:.2f}:1, below "
                    f"the declared floor of {contrast_floor}:1"
                )
    assert not failures, "contrast floor breached:\n  " + "\n  ".join(failures)


def test_the_rendered_page_carries_the_non_colour_encoding_and_not_just_the_token():
    """A token emitted and never applied passes every structural check above and renders
    a page where the distinction is invisible. So read what was actually rendered."""
    spine.require_dir(spine.SIDE_BY_SIDE_DIST, "rendered side-by-side page")
    import re

    offenders = []
    for name, block in sorted(_token_groups().items()):
        members = block["members"]
        attr = name[:-1] if name.endswith("s") else name
        for path in spine.iter_repo_files((".html",), root=spine.SIDE_BY_SIDE_DIST):
            html = spine.text_of(path)
            for m in re.finditer(rf'data-{attr}="([^"]+)"', html):
                entry = members.get(m.group(1))
                if not isinstance(entry, dict):
                    continue
                mark = str(entry.get("glyph") or entry.get("label") or "").strip()
                if mark and mark not in html:
                    offenders.append(
                        f"{spine._rel(path)} marks {name}='{m.group(1)}' without rendering "
                        f"its non-colour encoding '{mark}'"
                    )
    assert not offenders, (
        "rendered output must carry the non-colour encoding, not just the token:\n  "
        + "\n  ".join(sorted(set(offenders)))
    )


def test_no_visual_literal_survives_in_a_hand_written_stylesheet():
    """Every colour, face and spacing value resolves through a custom property.

    A hex value typed into a stylesheet is a second place the palette lives, and it is
    invisible to every check above, which is the whole reason the tokens exist.
    """
    import re
    hex_literal = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b")
    color_func = re.compile(r"\b(?:rgba?|hsla?|oklch|lab)\s*\(")

    hand_written = [
        p for p in spine.iter_repo_files((".css",))
        if not p.name.endswith(".generated.css")
    ]
    assert hand_written, "no hand-written stylesheet found; this check has no subject"

    offenders = []
    for path in hand_written:
        for n, line in enumerate(spine.text_of(path).splitlines(), start=1):
            if spine.is_comment_line(line):
                continue
            if hex_literal.search(line) or color_func.search(line):
                offenders.append(f"{spine._rel(path)}:{n}: {line.strip()}")
    assert not offenders, (
        "colour literals must resolve through a token, not appear in a stylesheet:\n  "
        + "\n  ".join(offenders)
    )
