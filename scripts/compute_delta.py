#!/usr/bin/env python3
"""Compute the auto-configuration elimination delta from the two running artifacts.

A maintained list would be true on the day it was written and unfalsifiable
afterwards. The traditional stack reports the capabilities it declares explicitly and
where each was declared; the Boot stack reports the same capabilities and whether
auto-configuration supplied them. The delta is the join of two live reports.

Neither side is enumerated here. The pair is resolved by configuration_style in the
manifest, so a fourth JVM stack does not require editing this file.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import urllib.request
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "autoconfig_delta.json"
HOST = os.environ.get("DEMO_HOST", "127.0.0.1")


def fail(message: str) -> None:
    print(f"DELTA FAILED: {message}", file=sys.stderr)
    raise SystemExit(1)


def stacks() -> dict:
    doc = yaml.safe_load((ROOT / "stacks" / "manifest.yaml").read_text())
    return {k: v for k, v in (doc.get("stacks") or {}).items() if v.get("active")}


def by_style(style: str) -> tuple[str, dict]:
    found = {k: v for k, v in stacks().items() if v.get("configuration_style") == style}
    if len(found) != 1:
        fail(f"expected exactly one active stack with configuration_style '{style}', "
             f"found {sorted(found) or 'none'}")
    name = next(iter(found))
    return name, found[name]


def get(stack: dict, endpoint_field: str) -> dict:
    endpoint = stack.get(endpoint_field)
    if not endpoint:
        fail(f"stack declares no {endpoint_field}")
    url = f"http://{HOST}:{stack['port']}{endpoint}"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 (any failure here is a failure to compute)
        fail(f"{url} did not answer: {exc}")


def main() -> int:
    trad_id, trad = by_style("explicit")
    boot_id, boot = by_style("auto")

    explicit = (get(trad, "beans_endpoint") or {}).get("capabilities") or {}
    auto = (get(boot, "autoconfig_endpoint") or {}).get("capabilities") or {}
    if not explicit:
        fail(f"{trad_id} reports no explicitly declared capabilities")

    eliminated, retained, unmatched = [], [], []
    for capability in sorted(explicit):
        declared_at = explicit[capability].get("declared_at", "unknown")
        provided = auto.get(capability)
        if not provided:
            unmatched.append({"capability": capability, "declared_at": declared_at})
        elif str(provided.get("source", "")).lower() == "auto-configuration":
            eliminated.append({
                "capability": capability,
                "explicit_at": declared_at,
                "auto_at": provided.get("declared_at", "unknown"),
            })
        else:
            retained.append({
                "capability": capability,
                "explicit_at": declared_at,
                "boot_source": provided.get("source"),
            })

    doc = {
        "explicitStack": trad_id,
        "autoStack": boot_id,
        "eliminated": eliminated,
        "retained": retained,
        "unmatched": unmatched,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"delta: {len(eliminated)} eliminated, {len(retained)} retained, "
          f"{len(unmatched)} unmatched -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
