#!/usr/bin/env bash
# Browser checks against every frontend the manifest declares.
#
# The targets were written out by hand once and drifted: the runtime and live-update
# checks ran against one frontend while the integrity checks ran against both, so a defect
# present only in React would have passed. The stack set comes from the manifest here, the
# same as everywhere else, and each driver refuses to run with its target unset rather than
# falling back to a guess.
#
#   bash scripts/visual.sh         every check
#   bash scripts/visual.sh live    the cross-frontend live-update check only
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="mcr.microsoft.com/playwright:v1.45.0-jammy"
ONLY="${1:-all}"

# name<TAB>origin, from the manifest. No port literal in this file.
read_stacks() {
  python3 - "$1" <<'PY'
import sys, pathlib, yaml
role = sys.argv[1]
manifest = yaml.safe_load(pathlib.Path("stacks/manifest.yaml").read_text()) or {}
for stack_id, stack in (manifest.get("stacks") or {}).items():
    if stack.get("active") and stack.get("role") == role and stack.get("port"):
        print(f"{stack_id} http://127.0.0.1:{stack['port']}")
PY
}

read_infra() {
  python3 - "$1" <<'PY'
import sys, pathlib, yaml
name = sys.argv[1]
manifest = yaml.safe_load(pathlib.Path("stacks/manifest.yaml").read_text()) or {}
spec = (manifest.get("infrastructure") or {}).get(name) or {}
if not spec.get("port"):
    raise SystemExit(f"manifest declares no port for infrastructure.{name}")
print(f"http://127.0.0.1:{spec['port']}")
PY
}

drive() {  # drive <script> [env assignments...]
  local script="$1"; shift
  local envs=()
  for pair in "$@"; do envs+=(-e "$pair"); done
  docker run --rm --network host "${envs[@]}" \
    -v "$PWD/visual:/w" -w /w "$IMAGE" node "$script"
}

frontends=$(read_stacks frontend)
backends=$(read_stacks backend)

# The two frontends, and a backend to point them both at. Taking the first of each rather
# than naming one keeps this file free of stack names too.
left=$(echo "$frontends" | sed -n '1p')
right=$(echo "$frontends" | sed -n '2p')
backend=$(echo "$backends" | sed -n '1p' | cut -d' ' -f1)

if [ -z "$right" ]; then
  echo "the manifest declares fewer than two active frontends; there is no pair to drive" >&2
  exit 2
fi

live() {
  drive live-drive.mjs \
    "LEFT=$(echo "$left" | tr ' ' '=')" \
    "RIGHT=$(echo "$right" | tr ' ' '=')" \
    "BACKEND=$backend"
}

if [ "$ONLY" = "live" ]; then
  live
  exit $?
fi

# Per-frontend checks, against every frontend rather than against one.
echo "$frontends" | while read -r name origin; do
  [ -n "$name" ] || continue
  echo "--- $name ($origin)"
  for check in integrity-drive.mjs runtime-drive.mjs tracker-drive.mjs; do
    drive "$check" "APP=$origin" "LABEL=$name" "SHOT=$check-$name"
  done
done

# The cross-frontend check, which needs two of them at once.
live

# The side-by-side page, and a screenshot of each frontend on its own.
drive check.mjs \
  "SIDE_BY_SIDE=$(read_infra side-by-side)" \
  "FRONTENDS=$(echo "$frontends" | tr ' ' '=' | tr '\n' ' ')"
