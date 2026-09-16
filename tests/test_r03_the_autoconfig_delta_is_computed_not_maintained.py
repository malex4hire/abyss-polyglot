"""R-3 — what Spring Boot's auto-configuration actually eliminates, computed from the
two running artifacts.

The traditional stack reports the capabilities it declares explicitly and the source line
each was declared on. The Boot stack reports the same capabilities and whether
auto-configuration supplied them. The delta is the join of those two live reports.

No maintained list exists anywhere, and that is the point. A hand-written "Boot saves you
these twelve beans" would be true on the day it was written and unfalsifiable afterwards
— the two frameworks would move underneath it and the page would keep making the same
claim. Computing it means the claim is re-derived every time the demo comes up, and a
Boot release that stops auto-configuring something turns this red.

Neither side is named here. The pair is resolved by `configuration_style` in the
manifest, so a fifth JVM stack does not require editing this file.
"""

from __future__ import annotations

import json
import subprocess

import pytest

import spine

DELTA = spine.REPO_ROOT / "build" / "autoconfig_delta.json"


def _pair_by_style(style: str) -> tuple[str, dict]:
    """Resolve a stack by its declared configuration_style, not by name."""
    matches = {
        sid: s for sid, s in spine.active_stacks().items()
        if s.get("configuration_style") == style
    }
    if len(matches) != 1:
        pytest.fail(
            f"expected exactly one active stack with configuration_style '{style}', "
            f"found {sorted(matches) or 'none'}"
        )
    sid = next(iter(matches))
    return sid, matches[sid]


def _report(sid: str, stack: dict, endpoint_field: str) -> dict:
    endpoint = spine.stack_field(sid, stack, endpoint_field)
    response = spine.http_get(spine.base_url(sid, stack) + endpoint)
    assert response.status_code == 200, (
        f"stack '{sid}' {endpoint_field} returned {response.status_code}"
    )
    try:
        return response.json()
    except ValueError:
        pytest.fail(f"stack '{sid}' {endpoint_field} did not return JSON")


def test_the_manifest_declares_the_pair_by_configuration_style():
    """Resolved by declared behaviour rather than by name, so this file names no stack."""
    explicit, auto = _pair_by_style("explicit"), _pair_by_style("auto")
    assert explicit[0] != auto[0]
    for sid, stack, field in (
        (*explicit, "beans_endpoint"),
        (*auto, "autoconfig_endpoint"),
    ):
        assert stack.get(field), (
            f"stack '{sid}' declares configuration_style but no {field}; the delta is "
            "computed from two live endpoints and has nothing to read without it"
        )


@pytest.mark.needs_stacks
def test_every_explicitly_declared_capability_is_autoconfigured_in_boot():
    trad_id, trad = _pair_by_style("explicit")
    boot_id, boot = _pair_by_style("auto")

    explicit = _report(trad_id, trad, "beans_endpoint")
    autoconf = _report(boot_id, boot, "autoconfig_endpoint")

    explicit_caps = explicit.get("capabilities")
    if not isinstance(explicit_caps, dict) or not explicit_caps:
        pytest.fail(
            f"stack '{trad_id}' reports no explicitly declared capabilities; the delta "
            "has nothing to compute against"
        )
    auto_caps = autoconf.get("capabilities")
    if not isinstance(auto_caps, dict):
        pytest.fail(f"stack '{boot_id}' auto-configuration report declares no capabilities")

    unmatched, hand_wired = [], []
    for capability, detail in sorted(explicit_caps.items()):
        provided = auto_caps.get(capability)
        if not provided:
            unmatched.append(
                f"'{capability}' is declared explicitly in {trad_id} "
                f"({detail.get('declared_at', 'unknown site')}) with no Boot equivalent"
            )
            continue
        if str(provided.get("source", "")).lower() != "auto-configuration":
            hand_wired.append(
                f"'{capability}' in {boot_id} comes from '{provided.get('source')}' at "
                f"{provided.get('declared_at', 'unknown site')}, not auto-configuration"
            )

    assert not unmatched, "capabilities with no Boot equivalent:\n  " + "\n  ".join(unmatched)
    assert not hand_wired, (
        "Boot capabilities hand-wired where auto-configuration would serve — which makes "
        "the comparison a comparison of two hand-wired applications:\n  "
        + "\n  ".join(hand_wired)
    )


@pytest.mark.needs_stacks
def test_the_computed_delta_is_non_empty_and_names_both_sides():
    subprocess.run(
        ["python3", str(spine.REPO_ROOT / "scripts" / "compute_delta.py")],
        capture_output=True, text=True, timeout=120, cwd=spine.REPO_ROOT, check=True,
    )
    spine.require_file(DELTA, "computed auto-configuration delta")
    delta = json.loads(DELTA.read_text(encoding="utf-8"))

    trad_id, _ = _pair_by_style("explicit")
    boot_id, _ = _pair_by_style("auto")
    assert delta.get("explicitStack") == trad_id
    assert delta.get("autoStack") == boot_id

    eliminated = delta.get("eliminated")
    assert isinstance(eliminated, list) and eliminated, (
        "the computed elimination delta is empty; Boot must eliminate explicit "
        "configuration the traditional stack carries, or the pair demonstrates nothing"
    )
    for entry in eliminated:
        assert entry.get("explicit_at"), (
            f"delta entry {entry.get('capability')!r} names no declaration site in the "
            "explicit stack, so a reader cannot go and look at what was eliminated"
        )


def test_the_delta_is_not_a_maintained_list():
    """It is build output, not a hand-authored file under version control.

    The precondition is asserted first: an absence check over a repository that has no
    delta at all passes vacuously and is not a gate.
    """
    if not DELTA.exists():
        pytest.skip(
            "no delta on disk yet; bring the demo up and run scripts/compute_delta.py. "
            "This check is about where the delta comes from, not whether it exists"
        )
    res = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(DELTA.relative_to(spine.REPO_ROOT))],
        capture_output=True, text=True, cwd=spine.REPO_ROOT,
    )
    assert res.returncode != 0, (
        "the auto-configuration delta is tracked in git, which makes it a maintained "
        "list; it must be computed from the two running artifacts"
    )
