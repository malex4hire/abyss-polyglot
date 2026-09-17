#!/usr/bin/env python3
"""Generate .env from stacks/manifest.yaml.

Ports are declared once, in the manifest. Compose therefore reads every port from an
environment variable generated here, so a port moves in one file and every consumer
follows, and the host suite can assert that no port literal lives anywhere else.
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
manifest = yaml.safe_load((ROOT / "stacks" / "manifest.yaml").read_text())

lines = ["# GENERATED from stacks/manifest.yaml by scripts/render-env.py. Do not edit.",
         "# Ports are declared only in the manifest; this file is the bridge to compose.",
         ""]

infra = manifest.get("infrastructure") or {}
for name, spec in infra.items():
    if not isinstance(spec, dict):
        continue
    if spec.get("port"):
        lines.append(f"{name.replace('-', '_').upper()}_PORT={spec['port']}")
    # Some infrastructure needs a fixed address as well as a port. Same rule as the port:
    # declared once in the manifest, derived by everything that needs it.
    if spec.get("ip"):
        lines.append(f"{name.replace('-', '_').upper()}_IP={spec['ip']}")

for stack_id, stack in (manifest.get("stacks") or {}).items():
    if stack.get("active") and stack.get("port"):
        lines.append(f"{stack_id.replace('-', '_').upper()}_PORT={stack['port']}")

# The selectable backend set. Frontends carry no stack list: they read this at runtime
# from their own server, which reads it from here, which reads the manifest. A backend
# activated in the manifest becomes an option with no change to either frontend.
backends = {
    stack_id: {
        "label": stack.get("label") or stack_id,
        "origin": f"http://{stack['service']}:8080",
        # The declared pair, so the runtime panel can put the two side by side. The
        # frontends still name no stack: they read this, which reads the manifest.
        "pair": stack.get("pair") or "",
        # The artifact whose resolved version IS the framework version, read against
        # the runtime's own artifact list, never typed by hand. "none" means the stack has
        # no framework by design; the panel falls back to the runtime version for those
        # rather than showing a version that does not exist. Normalised to "" here,
        # matching the sentinel the runtime-identity check already reads.
        "framework_artifact": (
            "" if (stack.get("framework_artifact") or "none") == "none"
            else stack["framework_artifact"]
        ),
    }
    for stack_id, stack in (manifest.get("stacks") or {}).items()
    if stack.get("active") and stack.get("role") == "backend" and stack.get("service")
}
lines.append("BACKENDS_JSON=" + json.dumps(backends, separators=(",", ":")))

lines += ["", "POSTGRES_DB=polyglot", "POSTGRES_USER=polyglot", "POSTGRES_PASSWORD=polyglot", ""]
(ROOT / ".env").write_text("\n".join(lines))
print(f"wrote .env with {len([l for l in lines if '=' in l])} values")
