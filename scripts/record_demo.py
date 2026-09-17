#!/usr/bin/env python3
"""Record `python3 demo.py` and render the recording as a committed SVG.

    make record-demo

This is the only supported way to produce docs/media/demo.svg. The README shows demo
output above its first heading, and there are two ways to put output in a README: type it,
or record it. Typing it is a claim about what the program prints, and it decays silently:
a work item id from a run nobody can reproduce sat in this README until this script
replaced it.

What it does, in order:

  1. Runs the walkthrough under `-S -I`, on a pseudo-terminal.

     `-S -I` because that is the claim R-8 makes about this demo, and an artifact recorded
     under weaker conditions than the claim would be evidence for a different claim. The
     pseudo-terminal because demo.py colours its output through an isatty() check, so a
     plain pipe records a transcript nobody would ever see. The emphasis in the artifact
     is the demo's own, read off its escape codes; none of it is decided here.

  2. Scrubs the machine it ran on. A transcript is captured output and captured output
     carries its environment: home directory, hostname, repository path.

  3. Takes a declared window of the walkthrough, by step number.

     The whole run is 147 lines, which is not a thing anybody reads above a fold. The
     window is contiguous and its boundaries are the demo's own step rules, so nothing is
     elided inside it: what the reader sees is an uninterrupted run of the walkthrough,
     not an assembly of favourable lines.

  4. Renders it, reading every colour and the monospace face from design/tokens.yaml,
     which is this repository's single token source and is not going to be second-guessed
     here.

Reproduction is what makes the artifact evidence rather than decoration, so the output is
deterministic apart from the fields listed in VOLATILE below, and
tests/test_rst_a1_... re-runs this and compares.
"""
from __future__ import annotations

import os
import re
import select
import socket
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo.py"
TOKENS = ROOT / "design" / "tokens.yaml"
ARTIFACT = ROOT / "docs" / "media" / "demo.svg"

# The steps to show. Contiguous, so the rendered transcript is an unbroken run of the
# walkthrough: a refusal that writes nothing, the rollup, and the soft delete. Those are
# the three the contract is interesting for, and between them they show a request, a
# response, a rejection and a read-back.
WINDOW_STEPS = (4, 5, 6)

# Terminal geometry. A fixed column count rather than one measured from the recording,
# because a measured width would change with the length of a volatile value and the
# artifact would stop reproducing for a reason that has nothing to do with its content.
# A line wider than this is a loud failure below, never a silent clip.
COLUMNS = 92
FONT_PX = 13.0
ADVANCE = 0.6            # monospace advance width, in ems
LINE_PX = 18.0
PAD_PX = 18.0
CHROME_PX = 34.0

# Fields that cannot reproduce, normalised away before the committed artifact and a fresh
# recording are compared. Each one is a field the comparison stops checking, so this set
# is the reproduction check's blast radius and widening it is governed: the RST-A1 test
# requires a decision log entry for anything here beyond the four the constraint allows.
VOLATILE = {
    "timestamp": re.compile(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
    ),
    "duration": re.compile(r"(?<![\w.])\d+(?:\.\d+)?\s?(?:ms|s)(?![\w.])"),
    "port": re.compile(r"(?<=:)\d{4,5}(?![\d\w.])"),
    "generated-id": re.compile(r"DEMO-[0-9a-f]{8}"),
}

HANDOVER = "Ctrl-C to stop"
DEADLINE_SECONDS = 180


class RecordingFailed(RuntimeError):
    """The walkthrough did not produce a transcript this script can render."""


# ---------------------------------------------------------------------------
# 1. record
# ---------------------------------------------------------------------------

def record() -> str:
    """Run the walkthrough on a pseudo-terminal and return what it printed.

    The walkthrough blocks once it hands the server over, so reading to EOF would hang.
    It is read until the handover line, with a wall clock behind it: a version of this
    that waited only for the marker would turn any early exit into a stuck run rather
    than a report.
    """
    import pty

    if not DEMO.is_file():
        raise RecordingFailed(f"{DEMO} is missing; it is what this records")

    parent, child = pty.openpty()
    process = subprocess.Popen(
        [sys.executable, "-S", "-I", str(DEMO)],
        cwd=ROOT, stdin=subprocess.DEVNULL, stdout=child, stderr=child,
        env={**os.environ, "TERM": "xterm-256color", "COLUMNS": str(COLUMNS)},
        close_fds=True,
    )
    os.close(child)

    chunks: list[bytes] = []
    deadline = time.monotonic() + DEADLINE_SECONDS
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([parent], [], [], 1.0)
            if not ready:
                continue
            try:
                data = os.read(parent, 65536)
            except OSError:  # the child closed its end
                break
            if not data:
                break
            chunks.append(data)
            if HANDOVER.encode() in b"".join(chunks[-4:]):
                break
    finally:
        os.close(parent)
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:  # pragma: no cover
            process.kill()

    text = b"".join(chunks).decode("utf-8", errors="replace").replace("\r\n", "\n")
    if HANDOVER not in text:
        raise RecordingFailed(
            "the walkthrough did not reach its handover line, so the run was incomplete:\n"
            + text[-2000:]
        )
    if "EXPECTED" in text:
        raise RecordingFailed(
            "the walkthrough printed an unmet expectation; recording a broken run and "
            "putting it at the top of the README is the one outcome worth refusing:\n"
            + text[-2000:]
        )
    return text


# ---------------------------------------------------------------------------
# 2. scrub
# ---------------------------------------------------------------------------

def scrub(text: str) -> str:
    """Remove the machine from the transcript.

    Longest first, so the repository path is replaced before the home directory it sits
    under and does not leave half of itself behind.
    """
    replacements = [(str(ROOT), "."), (str(Path.home()), "~")]
    hostname = socket.gethostname()
    if hostname and len(hostname) > 3:
        replacements.append((hostname, "localhost"))
    for needle, replacement in sorted(replacements, key=lambda pair: -len(pair[0])):
        text = text.replace(needle, replacement)
    # Anything left that looks like somebody's home directory, whoever they are.
    return re.sub(r"/(?:home|Users)/[A-Za-z0-9._-]+", "~", text)


# ---------------------------------------------------------------------------
# 3. window
# ---------------------------------------------------------------------------

# One SGR escape: the colour the demo chose for what follows it.
SGR = re.compile(r"\x1b\[([0-9;]*)m")

STEP_HEADER = re.compile(r"^\d+\.\s")
RULE_LINE = re.compile(r"^─+$")


def window(text: str, steps: tuple[int, ...] = WINDOW_STEPS) -> list[str]:
    """The declared steps, from the rule above the first to the line before the next.

    Boundaries are the demo's own step rules rather than line numbers, so adding a step
    to the walkthrough moves the window instead of silently shifting its contents.
    """
    lines = text.split("\n")
    # Matched against the line with its escape codes removed. The demo emphasises a step
    # header, so the digit it starts with is not the first character on the line.
    bare = [SGR.sub("", line).rstrip() for line in lines]
    headers = [i for i, line in enumerate(bare) if STEP_HEADER.match(line)]
    if len(headers) < max(steps):
        raise RecordingFailed(
            f"the walkthrough printed {len(headers)} steps; the window asks for step "
            f"{max(steps)}"
        )
    if tuple(range(steps[0], steps[-1] + 1)) != steps:
        raise RecordingFailed(f"the window {steps} is not contiguous")

    def rule_above(header_index: int) -> int:
        for i in range(header_index - 1, -1, -1):
            if RULE_LINE.match(bare[i]):
                return i
        raise RecordingFailed("a step header with no rule above it; the transcript is malformed")

    start = rule_above(headers[steps[0] - 1])
    end = rule_above(headers[steps[-1]]) if len(headers) > steps[-1] else len(lines)
    selected = lines[start:end]
    while selected and not selected[-1].strip():
        selected.pop()
    if not selected:
        raise RecordingFailed("the declared window selected nothing")
    return selected


# ---------------------------------------------------------------------------
# 4. render
# ---------------------------------------------------------------------------

def palette() -> dict:
    """Colours and the monospace face, from the repository's single token source."""
    if not TOKENS.is_file():
        raise RecordingFailed(f"{TOKENS} is missing; it is where every colour here lives")
    doc = yaml.safe_load(TOKENS.read_text(encoding="utf-8")) or {}
    try:
        theme = doc["app"]["themes"]["dark"]
        status = doc["app"]["status"]["dark"]
        mono = doc["type"]["faces"]["mono"]["family"]
    except (KeyError, TypeError) as exc:
        raise RecordingFailed(
            f"{TOKENS} does not declare the application dark theme, its status colours "
            f"and a monospace face: {exc}"
        ) from None
    return {
        "bg": theme["bg"],
        "chrome": theme["raised"],
        "hairline": theme["hairline"],
        "ink": theme["ink"],
        "muted": theme["muted"],
        # The demo prints a 2xx in green and a refusal in amber. Those two meanings are
        # already declared on the application surface, so they are read from there rather
        # than invented: a terminal green and a DONE pill are the same statement.
        "good": status["DONE"],
        "warn": status["IN_PROGRESS"],
        "mono": mono,
    }


def _spans(line: str, colours: dict):
    """Split one recorded line into (text, fill, bold) runs, from its own escape codes."""
    fill, bold, out, cursor = colours["ink"], False, [], 0
    for match in SGR.finditer(line):
        if match.start() > cursor:
            out.append((line[cursor:match.start()], fill, bold))
        for code in (match.group(1) or "0").split(";"):
            code = code or "0"
            if code == "0":
                fill, bold = colours["ink"], False
            elif code == "1":
                bold = True
            elif code == "2":
                fill = colours["muted"]
            elif code == "32":
                fill = colours["good"]
            elif code == "33":
                fill = colours["warn"]
        cursor = match.end()
    if cursor < len(line):
        out.append((line[cursor:], fill, bold))
    return [(text, fill, bold) for text, fill, bold in out if text]


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(text: str) -> str:
    """The committed artifact: one recorded run, as an SVG that fetches nothing."""
    colours = palette()
    lines = window(scrub(text))

    overlong = [line for line in lines if len(SGR.sub("", line)) > COLUMNS]
    if overlong:
        raise RecordingFailed(
            f"{len(overlong)} recorded line(s) exceed the {COLUMNS}-column canvas, and "
            "clipping a transcript silently is how it stops being one. Widen COLUMNS:\n  "
            + SGR.sub("", overlong[0])[:160]
        )

    char = FONT_PX * ADVANCE
    width = round(COLUMNS * char + 2 * PAD_PX)
    height = round(CHROME_PX + len(lines) * LINE_PX + 2 * PAD_PX)
    baseline = CHROME_PX + PAD_PX + FONT_PX

    body = []
    for n, line in enumerate(lines):
        y = round(baseline + n * LINE_PX, 1)
        column = 0
        for run, fill, bold in _spans(line, colours):
            x = round(PAD_PX + column * char, 1)
            weight = ' font-weight="600"' if bold else ""
            body.append(
                f'<text x="{x}" y="{y}" fill="{fill}"{weight} '
                f'xml:space="preserve">{_escape(run)}</text>'
            )
            column += len(run)

    dots = "".join(
        f'<circle cx="{x}" cy="{round(CHROME_PX / 2, 1)}" r="4" fill="{colours["hairline"]}"/>'
        for x in (PAD_PX, PAD_PX + 15, PAD_PX + 30)
    )
    title = f"recorded: python3 demo.py (steps {WINDOW_STEPS[0]} to {WINDOW_STEPS[-1]} of the walkthrough)"

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">\n'
        "  <!-- GENERATED by scripts/record_demo.py from a recorded run of demo.py.\n"
        "       Do not edit; run `make record-demo`. Colours come from design/tokens.yaml. -->\n"
        f"  <title>{_escape(title)}</title>\n"
        f'  <rect width="{width}" height="{height}" rx="8" fill="{colours["bg"]}"/>\n'
        f'  <rect width="{width}" height="{CHROME_PX}" rx="8" fill="{colours["chrome"]}"/>\n'
        f'  <rect y="{CHROME_PX - 8}" width="{width}" height="8" fill="{colours["chrome"]}"/>\n'
        f"  {dots}\n"
        f'  <text x="{round(PAD_PX + 46, 1)}" y="{round(CHROME_PX / 2 + 4, 1)}" '
        f'fill="{colours["muted"]}" font-size="11" '
        f'font-family="{colours["mono"]}, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"'
        f">python3 demo.py</text>\n"
        f'  <g font-family="{colours["mono"]}, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT_PX}">\n    '
        + "\n    ".join(body)
        + "\n  </g>\n</svg>\n"
    )


# ---------------------------------------------------------------------------
# reproduction
# ---------------------------------------------------------------------------

def normalise(svg: str) -> str:
    """Replace every volatile field with its own name, so two runs can be compared.

    Braces rather than angle brackets: the placeholder lands inside an SVG text node, and
    `<generated-id>` turns a valid document into an unclosed tag. Nothing here depends on
    the normalised form parsing, but a normaliser that makes valid XML invalid is a trap
    for whatever reads its output next, and one check now does.
    """
    for name, pattern in sorted(VOLATILE.items()):
        svg = pattern.sub(f"{{{name}}}", svg)
    return svg


def main() -> int:
    try:
        svg = render(record())
    except RecordingFailed as exc:
        print(f"record-demo: {exc}", file=sys.stderr)
        return 1

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    before = ARTIFACT.read_text(encoding="utf-8") if ARTIFACT.is_file() else ""
    ARTIFACT.write_text(svg, encoding="utf-8")

    if not before:
        state = "recorded"
    elif normalise(before) == normalise(svg):
        state = "unchanged (volatile fields aside)"
    else:
        state = "re-recorded; the walkthrough's output changed"
    print(f"{ARTIFACT.relative_to(ROOT)} {state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
