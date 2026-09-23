#!/bin/bash
# Exercise 4: serve a routes.toml on :4000. Ctrl-C to stop.
#
#   bash scripts/serve_gateway.sh [routes.toml]
#
# There is no `switchyard-server` binary to install: the same Rust gateway is
# embedded in the pip wheel (docs/specs/switchyard-api-notes.md § Server install).
# The route reads your key via `api_key_env`, so it must be exported HERE.

set -euo pipefail

# Resolve both paths from THIS script's location, before any cd: secrets.env lives at
# the repo root, the config next to the lab. The remediation line below is then
# copy-pasteable from whatever directory the learner happens to be in.
LAB_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SECRETS="$(cd "$LAB_DIR/../.." && pwd)/secrets.env"
cd "$LAB_DIR"

CONFIG="${1:-routes.toml}"
[ -f "$CONFIG" ] || { echo "ERROR: no such config: $CONFIG (cp routes.toml.template routes.toml)" >&2; exit 1; }
[ -n "${NVIDIA_API_KEY:-}" ] || { echo "ERROR: NVIDIA_API_KEY is not set in THIS terminal." >&2
                                  echo "       Run:  set -a; source ${SECRETS}; set +a" >&2; exit 1; }

exec "$(bash scripts/install_switchyard.sh --print-python)" - "$CONFIG" "${PORT:-4000}" <<'PY'
import sys, time
from switchyard_rust.server import Server
server = Server(sys.argv[1], port=int(sys.argv[2]))       # loading it IS validating it
print(f"gateway up on {server.base_url} — routes: {server.base_url}/v1/models, "
      f"meter: {server.base_url}/v1/stats\nCtrl-C to stop.", flush=True)
try:
    while True:
        time.sleep(3600)
except KeyboardInterrupt:
    print("\nstopping…")
finally:
    server.close()
PY
