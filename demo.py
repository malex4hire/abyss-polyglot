#!/usr/bin/env python3
"""Walk the contract, against a real server, with nothing installed.

    python3 demo.py

No pip, no virtualenv, no docker, no network. This script and the backend it starts are
both standard library only, which is why the first thing this repository asks of a reader
is a single command rather than a setup section.

What it does: starts the Python backend on a free port, waits for it to answer, then
walks stacks/../contract/openapi.yaml one operation at a time, printing the request it
is about to make and the response it got, so that the contract is legible from the
terminal rather than from a specification.

    create                     a work item, by a key the caller chose
    create again               the same key: 200 and one row, not 201 and two
    transition (legal)         OPEN -> IN_PROGRESS, applied
    transition (illegal)       IN_PROGRESS -> OPEN, refused with a typed rejection
    workload                   the per-assignee rollup
    archive                    a soft delete: leaves the list, stays retrievable
    events                     the change stream, carrying what just happened

Then it leaves the server running and prints curl lines, because the useful thing after
a walkthrough is a prompt in front of the same server.

The same contract is served by three other backends: two JVM frameworks and a
framework-free JDK one. Those need docker, and the README explains how. This one needs
nothing but an interpreter.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_SRC = ROOT / "modules" / "python-modern" / "src"
HOST = "127.0.0.1"
STARTUP_TIMEOUT = 20.0

# --- presentation ------------------------------------------------------------
#
# Colour through a capability check, not unconditionally. A terminal that is not a tty,
# such as a pipe into `less`, a CI log, or a file, gets escape codes rendered as garbage,
# and the transcript this script exists to produce becomes unreadable in exactly the
# places someone would paste it.

_COLOUR = sys.stdout.isatty() and os.environ.get("TERM", "") not in ("", "dumb")

# Line buffering when the output is a pipe. Python block-buffers a redirected stdout, and
# the last thing this script prints is followed by a wait that never returns. So the
# handover message, which is the whole point of the ending, sat in an 8KB buffer and was
# never written. Anything watching this through a pipe, `tee`, or a CI log saw a walkthrough
# that produced nothing and hung.
try:
    sys.stdout.reconfigure(line_buffering=True)
except AttributeError:  # pragma: no cover, only on an interpreter older than 3.7
    pass


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOUR else text


def dim(text: str) -> str:
    return _c("2", text)


def bold(text: str) -> str:
    return _c("1", text)


def good(text: str) -> str:
    return _c("32", text)


def warn(text: str) -> str:
    return _c("33", text)


def rule() -> None:
    print(dim("─" * 74))


def step(number: int, title: str, why: str) -> None:
    print()
    rule()
    print(f"{bold(f'{number}.')} {bold(title)}")
    print(f"   {dim(why)}")


# --- the client --------------------------------------------------------------
#
# urllib rather than requests, and it is the whole point: a demo whose first command
# needs a dependency is a demo with a setup section in front of it.


class Response:
    def __init__(self, status: int, body: bytes):
        self.status = status
        self.raw = body
        try:
            self.json = json.loads(body) if body else None
        except json.JSONDecodeError:
            self.json = None


def call(method: str, base: str, path: str, payload: dict | None = None,
         summarise=None) -> Response:
    """One request, printed before it is sent and after it answers.

    A 4xx is a response, not an exception: this contract refuses things on purpose, and a
    walkthrough that crashed on the refusal would be unable to show the most interesting
    operation in it.
    """
    url = base + path
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")

    print(f"   {bold(method)} {path}")
    if payload is not None:
        print(dim("   → " + json.dumps(payload)))

    try:
        with urllib.request.urlopen(request, timeout=10) as raw:
            response = Response(raw.status, raw.read())
    except urllib.error.HTTPError as exc:
        response = Response(exc.code, exc.read())

    marker = good(str(response.status)) if response.status < 400 else warn(str(response.status))
    print(f"   {marker}")

    # A response worth summarising is summarised. Dumping the whole seeded list here
    # buries the one line that mattered under sixty that did not, and a walkthrough
    # nobody reads to the end demonstrates nothing.
    if summarise is not None and response.json is not None:
        for line in summarise(response.json):
            print(dim("   " + line))
        return response

    body = json.dumps(response.json, indent=2) if response.json is not None else ""
    for line in body.splitlines():
        print(dim("   " + line))
    return response


def expect(response: Response, status: int, what: str) -> Response:
    """The walkthrough is also a test. A wrong answer stops it rather than scrolling by.

    Printing a response and moving on would let this script narrate a broken backend in
    a convincing tone, which is worse than failing.
    """
    if response.status != status:
        print()
        print(warn(f"   EXPECTED {status}: {what}"))
        print(warn(f"   GOT      {response.status}: {response.raw.decode(errors='replace')[:400]}"))
        raise SystemExit(1)
    return response


# --- the server --------------------------------------------------------------


def free_port() -> int:
    """Ask the kernel for one rather than picking a number.

    A hard-coded port is the difference between "it works" and "it works unless you
    already have something on that port", and the second is the one a stranger meets.
    """
    with socket.socket() as probe:
        probe.bind((HOST, 0))
        return probe.getsockname()[1]


def start_backend(port: int) -> subprocess.Popen:
    if not BACKEND_SRC.is_dir():
        raise SystemExit(f"backend source not found at {BACKEND_SRC}")

    env = {**os.environ, "PORT": str(port), "PYTHONPATH": str(BACKEND_SRC)}
    process = subprocess.Popen(
        [sys.executable, "-m", "app"],
        cwd=BACKEND_SRC, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    # Drain the child's output on a thread. A pipe nobody reads fills, and the server
    # then blocks on its next write. That is a backend which answers four requests and
    # hangs on the fifth, with nothing on screen to say why.
    captured: list[str] = []

    def drain() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            captured.append(line)
    threading.Thread(target=drain, daemon=True).start()
    process._captured = captured  # type: ignore[attr-defined]
    return process


def await_health(base: str, process: subprocess.Popen) -> dict:
    """Poll until it answers, and give up loudly rather than hanging.

    Checking the child is still alive on every pass matters more than the timeout: a
    backend that exits immediately, because of a syntax error or a port already taken,
    otherwise produces twenty seconds of silence and a timeout message that blames the
    wrong thing.
    """
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = "".join(getattr(process, "_captured", []))[-1500:]
            raise SystemExit(
                f"the backend exited with code {process.returncode} before answering:\n{output}"
            )
        try:
            with urllib.request.urlopen(base + "/health", timeout=1) as raw:
                if raw.status == 200:
                    return json.loads(raw.read())
        except Exception:  # noqa: BLE001, still coming up
            time.sleep(0.1)
    raise SystemExit(f"the backend did not answer {base}/health within {STARTUP_TIMEOUT:.0f}s")


def read_events(base: str, want: int, timeout: float = 5.0) -> list[str]:
    """Read a few frames off the change stream and stop.

    The stream never ends, because that is what a stream is, so this reads until it has
    what it came for or the clock runs out, rather than iterating to EOF and waiting
    forever.
    """
    lines: list[str] = []
    try:
        with urllib.request.urlopen(base + "/events", timeout=timeout) as stream:
            deadline = time.monotonic() + timeout
            while len(lines) < want and time.monotonic() < deadline:
                raw = stream.readline()
                if not raw:
                    break
                text = raw.decode(errors="replace").rstrip("\n")
                if text:
                    lines.append(text)
    except Exception as exc:  # noqa: BLE001, a stream that closes is a fact to report
        lines.append(f"(stream ended: {exc})")
    return lines


# --- the walkthrough ---------------------------------------------------------


def walk(base: str, health: dict) -> str:
    item_id = f"DEMO-{uuid.uuid4().hex[:8]}"

    print()
    print(bold("  Work Item API: one contract, walked end to end"))
    print(f"  {dim(base)}")
    seeded = health.get("items", 0)
    print(f"  {dim(f'seeded with {seeded} work items')}")

    step(1, "create", "the caller chooses the key, so the write is addressable and repeatable")
    created = expect(call("POST", base, "/work-items", {
        "id": item_id, "title": "Ship the polyglot demo", "status": "OPEN",
        "priority": 8, "assignee": "marc", "tags": ["demo", "contract"],
    }), 201, "a new key must create a row")
    assert created.json["item"]["id"] == item_id

    step(2, "create again, same key",
         "201 twice would mean two rows for one key; the second call wrote nothing")
    repeat = expect(call("POST", base, "/work-items", {
        "id": item_id, "title": "Ship the polyglot demo", "status": "OPEN",
        "priority": 8, "assignee": "marc", "tags": ["demo", "contract"],
    }), 200, "an existing key returns the row as it stands, and does not claim to create")
    assert repeat.json["item"]["createdAt"] == created.json["item"]["createdAt"], (
        "the second call returned a different row, so it wrote one"
    )

    step(3, "transition, legal",
         "the status control is a state machine, not a dropdown that writes whatever it is given")
    moved = expect(call("POST", base, f"/work-items/{item_id}/transition",
                        {"status": "IN_PROGRESS"}), 200, "OPEN -> IN_PROGRESS is legal")
    assert moved.json["item"]["status"] == "IN_PROGRESS"

    step(4, "transition, illegal",
         "refused with a typed rejection, and the refusal writes nothing")
    refused = expect(call("POST", base, f"/work-items/{item_id}/transition",
                          {"status": "OPEN"}), 422,
                     "IN_PROGRESS -> OPEN is not a move this machine makes")
    assert "rejected" in refused.json, "the refusal is typed, not a bare error string"
    after = expect(call(
        "GET", base, f"/work-items/{item_id}",
        summarise=lambda doc: [f"{doc['item']['id']}  status={doc['item']['status']}"],
    ), 200, "the item still resolves")
    assert after.json["item"]["status"] == "IN_PROGRESS", "a refused transition changed the row"
    print(f"   {good('unchanged')}{dim(': still IN_PROGRESS, so the refusal cost nothing')}")

    step(5, "workload", "the rollup each backend fans out however its runtime makes natural")
    rollup = expect(call("GET", base, "/workload"), 200, "the rollup is part of the contract")
    assert rollup.json["byAssignee"].get("marc", 0) >= 1

    step(6, "archive", "a soft delete: no row is ever removed, anywhere in this repository")
    expect(call("POST", base, f"/work-items/{item_id}/archive"), 200, "archive succeeds")

    listed = expect(call(
        "GET", base, "/work-items",
        summarise=lambda doc: [
            f"{len(doc['items'])} active: "
            + ", ".join(i["id"] for i in doc["items"]),
        ],
    ), 200, "the list is the active view")
    assert item_id not in [i["id"] for i in listed.json["items"]], (
        "an archived item must leave the list"
    )
    fetched = expect(call(
        "GET", base, f"/work-items/{item_id}",
        summarise=lambda doc: [
            f"{doc['item']['id']}  status={doc['item']['status']}  "
            f"archivedAt={doc['item']['archivedAt']}",
        ],
    ), 200, "and must stay retrievable by id")
    assert fetched.json["item"]["archivedAt"], "archivedAt says which"
    print(f"   {good('gone from the list, still addressable')}"
          f"{dim(', archivedAt = ' + str(fetched.json['item']['archivedAt']))}")

    step(7, "events", "the change stream: a notification, not a second source of truth")
    print(f"   {bold('GET')} /events  {dim('(reading a few frames, then moving on)')}")
    collector: list[list[str]] = []
    reader = threading.Thread(target=lambda: collector.append(read_events(base, want=3)))
    reader.start()
    time.sleep(0.4)
    trigger = f"DEMO-{uuid.uuid4().hex[:8]}"
    urllib.request.urlopen(urllib.request.Request(
        base + "/work-items", method="POST",
        data=json.dumps({"id": trigger, "title": "Something changed", "status": "OPEN",
                         "priority": 1, "assignee": "marc", "tags": []}).encode(),
        headers={"Content-Type": "application/json"},
    ), timeout=5).read()
    reader.join(timeout=8)
    frames = collector[0] if collector else []
    if frames:
        for line in frames:
            print(dim("   " + line))
        print(f"   {good('the stream announced the write.')} "
              f"{dim('This is how a change in one browser reaches the other.')}")
    else:
        print(warn("   the stream produced nothing in the time allowed"))

    return item_id


def main() -> int:
    port = free_port()
    base = f"http://{HOST}:{port}"
    process = start_backend(port)
    try:
        health = await_health(base, process)
        walk(base, health)

        print()
        rule()
        print(bold("  The server is still running. Try it:"))
        print()
        for line in (
            f"curl -s {base}/work-items | python3 -m json.tool",
            f"curl -s '{base}/work-items?status=OPEN&tag=demo' | python3 -m json.tool",
            f"curl -s {base}/workload | python3 -m json.tool",
            f"""curl -s -X POST {base}/work-items -H 'Content-Type: application/json' \\
     -d '{{"id":"MY-1","title":"yours","status":"OPEN","priority":5,"assignee":"you","tags":[]}}'""",
            f"curl -s -X POST {base}/work-items/MY-1/transition "
            f"-H 'Content-Type: application/json' -d '{{\"status\":\"DONE\"}}'"
            "   # refused: 422",
            f"curl -N {base}/events",
        ):
            print(f"    {line}")
        print()
        print(dim("  The other three backends serve this same contract; they need docker."))
        print(dim("  See the README, or run:  make up  &&  make verify"))
        print()
        print(dim("  Ctrl-C to stop."))
        print()

        while process.poll() is None:
            time.sleep(0.5)
        return 0
    except KeyboardInterrupt:
        print()
        return 0
    finally:
        # Terminate, then kill. A server left listening makes the next run pick a
        # different port and look like it worked, while the first one is still there.
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
