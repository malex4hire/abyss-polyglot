"""R-5 — the whole demo starts and operates with no route out of the containers.

This is what self-hosted fonts, digest-pinned images and a static server instead of a dev
server are all for. Each of those is a small inconvenience on a laptop with wifi and the
difference between a working demo and a blank screen on a locked-down network — which is
where a demo tends to be shown.

The first test in this file is the one that matters, and it is the one that is easy to
forget: prove egress is actually blocked. Everything below it observes a property of an
egress-blocked stack, so if the overlay silently stopped blocking, every one of them
would pass while testing nothing.
"""

from __future__ import annotations

import os
import re
import subprocess

import pytest

import spine

pytestmark = pytest.mark.slow

CDN_RE = re.compile(r"https?://(?!127\.0\.0\.1|localhost)[^\s\"'<>)]+", re.IGNORECASE)


def test_no_remote_asset_reference_survives_in_the_side_by_side_page():
    """A webfont CDN renders a fallback face on a machine with no route out."""
    spine.require_dir(spine.SIDE_BY_SIDE_SRC, "side-by-side source")
    offenders = []
    for path in spine.iter_repo_files((".html", ".css", ".js"), root=spine.SIDE_BY_SIDE_SRC):
        for n, line in enumerate(spine.text_of(path).splitlines(), start=1):
            for url in CDN_RE.findall(line):
                offenders.append(f"{spine._rel(path)}:{n}: {url}")
    assert not offenders, (
        "page assets must be self-hosted; remote references found:\n  " + "\n  ".join(offenders)
    )


def test_every_image_is_pinned_by_digest():
    """A tag is a moving target. `nginx:1.27-alpine` is a different image next month, and
    the run that pulls the new one is the run with no network to pull it with."""
    spine.require_file(spine.COMPOSE_FILE, "compose file")
    unpinned = []
    for path in spine.iter_repo_files((".yml", ".yaml")):
        for n, line in enumerate(spine.text_of(path).splitlines(), start=1):
            m = re.match(r"\s*image:\s*(\S+)", line)
            if m and "@sha256:" not in m.group(1):
                unpinned.append(f"{spine._rel(path)}:{n}: {m.group(1)}")
    for path in spine.iter_repo_files():
        if path.name.lower().startswith("dockerfile"):
            for n, line in enumerate(spine.text_of(path).splitlines(), start=1):
                m = re.match(r"\s*FROM\s+(\S+)", line, re.IGNORECASE)
                if m and "@sha256:" not in m.group(1):
                    unpinned.append(f"{spine._rel(path)}:{n}: {m.group(1)}")
    assert not unpinned, "images must be pinned by digest:\n  " + "\n  ".join(unpinned)


# Connect to a routable address by IP rather than resolving a hostname. A name that does
# not resolve is weaker evidence than a connection that does not open — it would report
# BLOCKED on a container that has no resolver but a perfectly good route out. Each image
# carries a different set of tools, so the probe uses whichever one it finds; a container
# with none of them is skipped rather than counted as blocked.
EGRESS_PROBE = r"""
if command -v wget >/dev/null 2>&1; then
  # -t 1: a timeout bounds one attempt, and wget retries twenty times by default,
  # so the probe outlived a three-minute test timeout while behaving correctly.
  wget -q -T 5 -t 1 -O /dev/null http://1.1.1.1/ && echo REACHED || echo BLOCKED
elif command -v curl >/dev/null 2>&1; then
  curl -s -m 5 -o /dev/null http://1.1.1.1/ && echo REACHED || echo BLOCKED
elif command -v python3 >/dev/null 2>&1; then
  python3 -c 'import socket
s = socket.socket(); s.settimeout(5)
try:
    s.connect(("1.1.1.1", 443)); print("REACHED")
except Exception:
    print("BLOCKED")'
elif command -v node >/dev/null 2>&1; then
  node -e 'const s=require("net").connect(443,"1.1.1.1");s.setTimeout(5000);
s.on("connect",()=>{console.log("REACHED");process.exit(0)});
s.on("error",()=>{console.log("BLOCKED");process.exit(0)});
s.on("timeout",()=>{console.log("BLOCKED");process.exit(0)});'
else
  echo NOPROBE
fi
"""


@pytest.fixture(scope="module")
def offline_up():
    """Bring the demo up with the overlay once, for every test below.

    Each of these observes a property of a running egress-blocked stack, so each needs
    one. Written first as a step inside a single test, which left the others asserting
    against whatever happened to be running — and passing or failing on that rather than
    on the overlay.
    """
    spine.require_file(spine.OFFLINE_COMPOSE, "offline compose overlay")
    return spine.compose_offline("up", "-d", "--wait", timeout=1800)


def _assert_came_up(up):
    assert up.returncode == 0, (
        f"the demo does not come up with egress blocked:\n{up.stderr[-2000:]}"
    )


@pytest.mark.needs_stacks
def test_egress_is_actually_blocked(offline_up):
    """The overlay has to block egress, or everything below it proves nothing."""
    _assert_came_up(offline_up)
    stacks = spine.active_stacks()
    assert stacks, "no active stacks"

    probed, reached = [], []
    for sid, stack in sorted(stacks.items()):
        service = spine.stack_field(sid, stack, "service")
        probe = spine.compose_offline(
            "exec", "-T", service, "sh", "-lc", EGRESS_PROBE, timeout=180
        )
        verdict = (probe.stdout.strip().splitlines() or ["NOPROBE"])[-1]
        if verdict == "NOPROBE":
            continue
        probed.append(sid)
        if verdict == "REACHED":
            reached.append(sid)

    assert probed, (
        "no container carried a tool able to attempt an outbound connection, so nothing "
        "here observed egress at all"
    )
    assert not reached, (
        "these containers opened a connection to the outside, so the overlay is not "
        f"blocking egress and the rest of this file would pass vacuously: {reached}"
    )


@pytest.mark.needs_stacks
def test_the_demo_is_reachable_from_the_host_with_egress_blocked(offline_up):
    """Blocking the way out must not block the way in.

    The overlay's first spelling used an internal network, which removes the external
    bridge and takes published ports with it. Every service reported healthy on its own
    healthcheck and not one of them answered on the laptop the demo runs on.
    """
    _assert_came_up(offline_up)
    unreachable = []
    for sid, stack in sorted(spine.active_stacks().items()):
        response = spine.await_health(sid, stack, timeout=60)
        if response is None or response.status_code != 200:
            unreachable.append(f"{sid} at {spine.health_url(sid, stack)}")
    assert not unreachable, (
        "the demo does not answer on the host with egress blocked:\n  "
        + "\n  ".join(unreachable)
    )


@pytest.mark.needs_stacks
def test_the_contract_is_served_by_every_backend_with_egress_blocked(offline_up):
    """Healthy is not serving. The contract suite is what says the demo still works."""
    _assert_came_up(offline_up)

    for sid, stack in sorted(spine.backends().items()):
        result = subprocess.run(
            ["python3", "-m", "pytest", str(spine.CONTRACT_SUITE), "-q",
             "-p", "no:cacheprovider"],
            capture_output=True, text=True, timeout=900, cwd=spine.REPO_ROOT,
            env={**os.environ, "CONTRACT_BASE_URL": spine.base_url(sid, stack)},
        )
        assert result.returncode == 0, (
            f"the contract suite fails against '{sid}' with egress blocked:\n"
            f"{result.stdout[-1500:]}"
        )
