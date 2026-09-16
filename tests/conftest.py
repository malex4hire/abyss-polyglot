"""Pytest configuration for the host-side verification suite.

Intentionally thin. Readers live in tests/spine.py and are called from inside test
bodies so that a missing input is a failed assertion with a named reason rather than a
collection error. An errored suite is not a gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def pytest_report_header(config):
    return "abyss-polyglot — host-side verification"
