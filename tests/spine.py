"""Shared readers and derivations for the host-side verification suite.

Two rules govern everything in this module.

1. Nothing here enumerates a governed set. Stacks, roles, ports, tiers and token groups
   are read from their declaring files and joined. A list of stack names in this file
   would make the suite assert against itself instead of against the repository.

2. Absent input is a failed assertion, never a collection error. Every reader is a plain
   function called from inside a test body, so a missing input lands as a named failure
   and the suite still functions as a gate. Fixtures are deliberately not used for this:
   a raise inside a fixture is an error, not a failure, and an errored suite is not a
   gate.
"""

from __future__ import annotations

import colorsys
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Declared locations. Paths only — no content, no cardinalities.
# ---------------------------------------------------------------------------

MANIFEST = REPO_ROOT / "stacks" / "manifest.yaml"
TOKENS = REPO_ROOT / "design" / "tokens.yaml"
CONTRACT = REPO_ROOT / "contract" / "openapi.yaml"
CONTRACT_SUITE = REPO_ROOT / "contract" / "suite"
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
OFFLINE_COMPOSE = REPO_ROOT / "docker-compose.offline.yml"
DEMO = REPO_ROOT / "demo.py"
SIDE_BY_SIDE_SRC = REPO_ROOT / "side-by-side" / "src"
SIDE_BY_SIDE_DIST = REPO_ROOT / "side-by-side" / "dist"

# Directories that are build product, vendored asset, or VCS metadata. Excluded from
# every repository-wide scan.
SCAN_EXCLUDE_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".venv", "venv",
    "build", "dist", "node_modules", "target", "vendor", "fonts",
    # Review output written per commit by tooling outside this repository. It quotes
    # source, so scanning it reports this repository's own values back as violations.
    "code-review", "logs",
}



# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------

def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_yaml(path: Path, what: str) -> dict:
    """Load a declaring file, or fail the calling test with a named reason."""
    if not path.exists():
        pytest.fail(f"MISSING INPUT: {what} not found at {_rel(path)}")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        pytest.fail(f"UNREADABLE INPUT: {what} at {_rel(path)} is not valid YAML: {exc}")
    if doc is None:
        pytest.fail(f"EMPTY INPUT: {what} at {_rel(path)} parsed to nothing")
    if not isinstance(doc, dict):
        pytest.fail(
            f"MALFORMED INPUT: {what} at {_rel(path)} must be a mapping, "
            f"got {type(doc).__name__}"
        )
    return doc


def require_dir(path: Path, what: str) -> Path:
    if not path.is_dir():
        pytest.fail(f"MISSING INPUT: {what} directory not found at {_rel(path)}")
    return path


def require_file(path: Path, what: str) -> Path:
    if not path.is_file():
        pytest.fail(f"MISSING INPUT: {what} not found at {_rel(path)}")
    return path


def _section(doc: dict, key: str, what: str, path: Path) -> dict:
    if key not in doc:
        pytest.fail(f"MALFORMED INPUT: {what} at {_rel(path)} has no top-level '{key}' key")
    val = doc[key]
    if not isinstance(val, dict):
        pytest.fail(
            f"MALFORMED INPUT: '{key}' in {_rel(path)} must be a mapping keyed by id, "
            f"got {type(val).__name__}"
        )
    return val


# ---------------------------------------------------------------------------
# The manifest — the source of the stack set
# ---------------------------------------------------------------------------

def stacks() -> dict:
    """All declared stacks, keyed by stack id."""
    return _section(read_yaml(MANIFEST, "stack manifest"), "stacks", "stack manifest", MANIFEST)


def active_stacks() -> dict:
    """Stacks with active: true. The set every check is scoped to."""
    return {k: v for k, v in stacks().items() if v.get("active") is True}


def stack_field(stack_id: str, stack: dict, field: str):
    if field not in stack:
        pytest.fail(
            f"MALFORMED INPUT: stack '{stack_id}' in {_rel(MANIFEST)} declares no '{field}'"
        )
    return stack[field]


def backends() -> dict:
    return {k: v for k, v in active_stacks().items() if v.get("role") == "backend"}


def frontends() -> dict:
    return {k: v for k, v in active_stacks().items() if v.get("role") == "frontend"}


def source_root(stack_id: str, stack: dict) -> Path:
    return REPO_ROOT / stack_field(stack_id, stack, "source_root")


def infrastructure() -> dict:
    doc = read_yaml(MANIFEST, "stack manifest")
    infra = doc.get("infrastructure")
    if not isinstance(infra, dict) or not infra:
        pytest.fail(f"MALFORMED INPUT: {_rel(MANIFEST)} declares no infrastructure block")
    return infra


def declared_ports() -> dict[str, int]:
    """Every port the manifest declares, stacks and infrastructure alike, keyed by owner.

    Infrastructure is included deliberately. Postgres's port was once the one number
    written directly into compose, on the reasoning that it is not a stack — which is how
    a rule with an exception in it stops being a rule.
    """
    ports = {
        sid: int(stack["port"])
        for sid, stack in active_stacks().items()
        if stack.get("port")
    }
    for name, spec in infrastructure().items():
        if isinstance(spec, dict) and spec.get("port"):
            ports[name] = int(spec["port"])
    return ports


# ---------------------------------------------------------------------------
# Instrumentation endpoints
#
# Identity, beans and autoconfig are instrumentation, not contract. They report resolved
# runtime *data* and never a claimed identity string, because a module asserting its own
# identity proves nothing.
# ---------------------------------------------------------------------------

INSTRUMENTATION_FIELDS = ("identity_endpoint", "beans_endpoint", "autoconfig_endpoint")

# Keys an instrumentation report must never carry. Each is a self-assertion rather than
# resolved runtime data.
CLAIMED_IDENTITY_KEYS = (
    "framework", "identity", "stack", "stack_id", "stack_name",
    "declares", "claimed_framework", "framework_name",
)


def instrumentation_paths() -> set[str]:
    paths = set()
    for stack in stacks().values():
        for field in INSTRUMENTATION_FIELDS:
            if stack.get(field):
                paths.add(str(stack[field]))
    return paths


# ---------------------------------------------------------------------------
# The nouns that name the stack set in prose
#
# Detection is contextual, not value-based. An integer is a violation only where it is
# used as a stated count of a set the manifest owns — so the nouns that name that set
# have to be declared by the manifest itself.
# ---------------------------------------------------------------------------

COUNT_PLACEHOLDER_RE = re.compile(r"\{\{\s*count:([A-Za-z0-9_\[\]/.-]+)\s*\}\}")

# "one" is deliberately absent. As a quantifier it is pervasive and never states a set
# size — "exactly one contract", "the one stack with no framework" — and only use as a
# stated count is a violation.
NUMERAL_WORDS = (
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety", "hundred", "dozen",
)


def prose_nouns() -> list[str]:
    """The nouns that name the stack set in prose, declared by the manifest."""
    doc = read_yaml(MANIFEST, "stack manifest")
    nouns = doc.get("nouns")
    if not isinstance(nouns, dict) or not nouns.get("stacks"):
        pytest.fail(
            f"MISSING DECLARATION: {_rel(MANIFEST)} declares no nouns.stacks; the "
            "derived-count check needs the words that name this set in prose"
        )
    return [str(w).lower() for w in nouns["stacks"]]


def count_qualifier_pattern(nouns: list[str]) -> re.Pattern:
    """A numeral — digits or words — qualifying one of these nouns.

    At most one intervening word, so "four backends" is caught while a sentence that
    merely mentions a port number near the word "stack" is not. A wider window matched any
    numeral that happened to share a sentence with the noun, which is not what this asks:
    only use as a stated count is a violation.
    """
    numeral = r"(?:\d+|" + "|".join(NUMERAL_WORDS) + r")"
    noun = "|".join(re.escape(n) for n in sorted(nouns, key=len, reverse=True))
    return re.compile(
        rf"(?<![\w-])({numeral})\s+(?:[\w-]+\s+)?({noun})(?![\w-])",
        re.IGNORECASE,
    )


# ---------------------------------------------------------------------------
# Repository scanning
# ---------------------------------------------------------------------------

def iter_repo_files(suffixes: tuple[str, ...] | None = None, root: Path = REPO_ROOT):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SCAN_EXCLUDE_DIRS for part in path.relative_to(root).parts):
            continue
        if suffixes and path.suffix not in suffixes:
            continue
        yield path


COMMENT_PREFIXES = ("#", "//", "--", "/*", "*", "<!--")


def is_comment_line(line: str) -> bool:
    return line.strip().startswith(COMMENT_PREFIXES)


# Matches a line comment to end of line, and a block comment across lines. String literals
# are left alone deliberately: a URL containing "//" inside a string is not a comment, and
# a stripper that tried to be clever about quotes would be a small parser nobody reviews.
_LINE_COMMENT = re.compile(r"(?<![:\"'\\])//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
# Angular puts its template in a string literal, so a template comment is an HTML comment
# sitting inside TypeScript. Missing this shape is what let a paragraph about two stacks
# sharing a base image read as source naming two stacks.
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def strip_comments(text: str) -> str:
    """Blank out C-style comments, keeping line numbers intact.

    Checking `line.startswith("//")` finds the first line of a comment and misses every
    continuation line under it — so a paragraph explaining why two stacks share a base
    image read as frontend source naming two stacks. That is a false positive, and a check
    with a false positive gets disabled by whoever trusts it next.

    Newlines are preserved so a hit still reports the line it is on.
    """
    def blank(match: re.Match) -> str:
        return "".join("\n" if c == "\n" else " " for c in match.group(0))

    for pattern in (_BLOCK_COMMENT, _HTML_COMMENT, _LINE_COMMENT):
        text = pattern.sub(blank, text)
    return text


def interval_callbacks(text: str) -> list[str]:
    """The argument text of every setInterval(...) call, by balanced parentheses.

    The question is never "does this file call setInterval" — a progress bar and a tick
    counter both do, legitimately. It is whether an interval FETCHES, because a timer that
    re-lists the data is a poll wearing the same clothes as live update. So the body is
    what gets read, not the call site.
    """
    out, needle = [], "setInterval"
    start = text.find(needle)
    while start != -1:
        # Only a call. `ReturnType<typeof setInterval>` is a type position, and reading
        # forward to the next parenthesis from there returns an unrelated expression.
        after = start + len(needle)
        while after < len(text) and text[after].isspace():
            after += 1
        if after >= len(text) or text[after] != "(":
            start = text.find(needle, after)
            continue
        open_paren = after
        depth, i = 0, open_paren
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    out.append(text[open_paren + 1:i])
                    break
            i += 1
        start = text.find(needle, start + len(needle))
    return out


def text_of(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def visible_text(html: str) -> str:
    """Rendered text of an HTML document, tags and script/style content removed."""
    html = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    return re.sub(r"(?s)<[^>]+>", " ", html)


# ---------------------------------------------------------------------------
# Colour maths for the token checks. Floors are read from tokens.yaml, never
# written down here.
# ---------------------------------------------------------------------------

def hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def relative_luminance(value: str) -> float:
    def channel(c: float) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_to_rgb(value)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(a: str, b: str) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def hue_degrees(value: str) -> float:
    r, g, b = (c / 255 for c in hex_to_rgb(value))
    return colorsys.rgb_to_hls(r, g, b)[0] * 360


def hue_separation(a: str, b: str) -> float:
    d = abs(hue_degrees(a) - hue_degrees(b)) % 360
    return min(d, 360 - d)


# ---------------------------------------------------------------------------
# Container and process helpers for the checks that need a running stack
# ---------------------------------------------------------------------------

def docker_available() -> bool:
    return shutil.which("docker") is not None


def compose(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        capture_output=True, text=True, timeout=timeout, cwd=REPO_ROOT,
    )


def compose_offline(*args: str, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "-f", str(OFFLINE_COMPOSE), *args],
        capture_output=True, text=True, timeout=timeout, cwd=REPO_ROOT,
    )


def compose_services() -> list[str]:
    require_file(COMPOSE_FILE, "compose file")
    if not docker_available():
        pytest.fail("MISSING TOOL: docker is not on PATH, so compose cannot be read")
    res = compose("config", "--services")
    if res.returncode != 0:
        pytest.fail(
            f"COMPOSE ERROR: `docker compose config --services` failed: {res.stderr.strip()}"
        )
    return [s for s in res.stdout.split() if s]


def container_identity(service: str) -> tuple[str, str]:
    """(container id, started-at) for a compose service."""
    res = compose("ps", "-q", service)
    cid = res.stdout.strip().splitlines()
    if res.returncode != 0 or not cid:
        pytest.fail(
            f"NOT RUNNING: compose service '{service}' has no container; bring the demo up first"
        )
    cid = cid[0]
    insp = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.StartedAt}}", cid],
        capture_output=True, text=True, timeout=30,
    )
    if insp.returncode != 0:
        pytest.fail(f"INSPECT FAILED: container {cid} for '{service}': {insp.stderr.strip()}")
    return cid, insp.stdout.strip()


def http_get(url: str, timeout: int = 10):
    try:
        import requests
    except ImportError:
        pytest.fail("MISSING TOOL: `requests` is not installed; install the 'verify' extra")
    try:
        return requests.get(url, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 — any transport failure is a stack failure
        pytest.fail(f"UNREACHABLE: {url} did not respond: {exc}")


def base_url(stack_id: str, stack: dict) -> str:
    host = os.environ.get("DEMO_HOST", "127.0.0.1")
    port = stack_field(stack_id, stack, "port")
    return f"http://{host}:{port}"


def identity_url(stack_id: str, stack: dict) -> str:
    return base_url(stack_id, stack) + stack_field(stack_id, stack, "identity_endpoint")


def health_url(stack_id: str, stack: dict) -> str:
    return base_url(stack_id, stack) + stack_field(stack_id, stack, "health_endpoint")


def await_health(stack_id: str, stack: dict, timeout: int = 240):
    """Poll a stack's health endpoint until it answers, or give up.

    A restarted service is not immediately listening, and http_get fails the test on the
    first refused connection. Anything that restarts a container needs to wait for it
    rather than race it.
    """
    import time

    try:
        import requests
    except ImportError:
        pytest.fail("MISSING TOOL: `requests` is not installed; install the 'verify' extra")

    url = health_url(stack_id, stack)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response
        except Exception:  # noqa: BLE001 — still coming up
            pass
        time.sleep(2)
    return None
