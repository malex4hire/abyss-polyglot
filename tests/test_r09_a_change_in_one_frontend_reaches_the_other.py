"""R-9 — a change made in one frontend arrives in the other with nobody touching it.

This is the claim the whole repository is built to support, and it is the only one that
cannot be demonstrated by reading anything. Two different frameworks, two separate
browser contexts, one backend: create an item in Angular and it appears in React, archive
it in React and it leaves Angular. No refresh, no polling loop, no click on the far side.

The evidence is a real browser, because nothing short of one settles it. A unit test for
the stream proves a subscription calls its callback. It does not prove that a rendered
list re-renders, that the re-render reached the DOM, or that the other framework — with a
completely different change-detection model — noticed at all.

The declarative half runs on the host and is checked here. The behavioural half is driven
by visual/live-drive.mjs under Playwright, invoked by scripts/visual.sh, and this file
runs it. That split exists because a browser needs an image the host does not have: when
docker is unavailable this reports as a skip that names what was not run, rather than as
a pass.
"""

from __future__ import annotations

import subprocess

import pytest

import spine

STREAM_PATH = "/events"
LIVE_DRIVER = spine.REPO_ROOT / "visual" / "live-drive.mjs"


def test_the_change_stream_is_part_of_the_contract_not_instrumentation():
    """Every backend owes it and both frontends may depend on it.

    If it lived beside the identity endpoints it would be a demo surface, and a backend
    could serve the contract in full while a change in one browser reached nothing.
    """
    doc = spine.read_yaml(spine.CONTRACT, "API contract")
    paths = doc.get("paths") or {}
    assert STREAM_PATH in paths, (
        f"the contract declares no {STREAM_PATH}; live update is the claim this repository "
        "is built around and it must be something every backend owes"
    )
    assert STREAM_PATH not in spine.instrumentation_paths(), (
        f"{STREAM_PATH} is declared as instrumentation; it is contract"
    )

    body = str(paths[STREAM_PATH])
    assert "text/event-stream" in body, (
        f"{STREAM_PATH} does not declare an event-stream media type, so what a client may "
        "expect from it is unstated"
    )


def test_both_frontends_consume_the_stream():
    """Declared in the contract and consumed by neither would be a contract nobody uses."""
    silent = []
    for sid, stack in sorted(spine.frontends().items()):
        root = spine.source_root(sid, stack)
        joined = "\n".join(
            spine.text_of(p)
            for p in spine.iter_repo_files((".ts", ".tsx", ".js", ".jsx"), root=root)
        )
        if "EventSource" not in joined and STREAM_PATH not in joined:
            silent.append(sid)
    assert not silent, (
        "these frontends subscribe to no change stream, so a change made elsewhere "
        "reaches them only if somebody reloads: " + ", ".join(silent)
    )


# What a poll looks like inside a timer: something that goes and asks the server again.
FETCHING = ("fetch(", ".subscribe(", "refresh(", "reload(", "api.", "EventSource")


def test_no_frontend_refreshes_its_data_on_a_timer():
    """A poll looks identical on screen and is not the same claim.

    It would make "with no user action" true and "live" false, and it would keep working
    with the stream completely broken — which is the kind of green that teaches you to
    stop trusting the check.

    The subject is the interval's BODY, not the call. Banning setInterval outright was the
    first spelling and it was wrong: it flagged a progress bar and a tick counter, neither
    of which asks the server anything. A check that fires on correct code is a check
    somebody deletes.
    """
    offenders = []
    for sid, stack in sorted(spine.frontends().items()):
        for path in spine.iter_repo_files(
            (".ts", ".tsx", ".js", ".jsx"), root=spine.source_root(sid, stack)
        ):
            source = spine.strip_comments(spine.text_of(path))
            for body in spine.interval_callbacks(source):
                hit = [token for token in FETCHING if token in body]
                if hit:
                    offenders.append(
                        f"{spine._rel(path)}: an interval body calls {', '.join(hit)}: "
                        + " ".join(body.split())[:120]
                    )
    assert not offenders, (
        "a frontend re-reads its data on a timer; live update must come from the stream, "
        "or the demo shows the same thing while proving something weaker:\n  "
        + "\n  ".join(offenders)
    )


def test_the_browser_driver_exists_and_drives_both_directions():
    """Both directions, because one direction can pass on an accident.

    Angular creating and React noticing could be React re-fetching for its own reasons.
    The archive going the other way, through a different framework's change detection, is
    what makes it the stream rather than a coincidence.
    """
    spine.require_file(LIVE_DRIVER, "live-update browser driver")
    source = spine.text_of(LIVE_DRIVER)
    for needle, why in (
        ("waitForFunction", "the driver must wait for the far side to change by itself"),
        ("archive", "the driver must also drive the reverse direction"),
    ):
        assert needle in source, f"{spine._rel(LIVE_DRIVER)}: {why}"

    # It must not name a port, for the same reason nothing else may.
    ports = {str(p) for p in spine.declared_ports().values()}
    assert not [p for p in ports if p in source], (
        f"{spine._rel(LIVE_DRIVER)} names a port; its targets come from the manifest via "
        "scripts/visual.sh"
    )


@pytest.mark.needs_stacks
@pytest.mark.slow
def test_a_change_in_one_frontend_reaches_the_other_in_a_real_browser():
    if not spine.docker_available():
        pytest.skip(
            "docker is not available, so the browser image cannot run. The live-update "
            "claim is NOT verified by this run — `make visual` is what verifies it"
        )
    frontends = spine.frontends()
    assert len(frontends) >= 2, "fewer than two active frontends; there is no pair to drive"

    script = spine.REPO_ROOT / "scripts" / "visual.sh"
    spine.require_file(script, "browser check runner")
    result = subprocess.run(
        ["bash", str(script), "live"],
        capture_output=True, text=True, timeout=900, cwd=spine.REPO_ROOT,
    )
    assert result.returncode == 0, (
        "a change made in one frontend did not reach the other:\n"
        + (result.stdout or "")[-3000:] + (result.stderr or "")[-1500:]
    )
    assert "OK" in result.stdout, (
        "the browser driver produced no result lines, so it asserted nothing:\n"
        + result.stdout[-2000:]
    )
