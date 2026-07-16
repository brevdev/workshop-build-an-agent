#!/usr/bin/env bash
# setup.sh — one-shot reproducer for the Build-an-Agent workshop inside an
# OpenShell/NemoClaw sandbox. RUN THIS FROM INSIDE THE SANDBOX (agent context).
#
# Idempotent: safe to re-run. Every step verifies before doing work.
#
# Prereqs (verify with scripts/preflight.sh; details in
# references/operator-contract.md — the operator does these OUTSIDE the sandbox):
#   - Sandbox policy allows GET pypi.org + files.pythonhosted.org and
#     POST /v1/ranking on integrate.api.nvidia.com (module-2 reranker).
#   - NVIDIA key staged at $REPO/secrets.env  (NVIDIA_API_KEY=...)
set -euo pipefail

# ---- config -----------------------------------------------------------------
REPO="${REPO:-/sandbox/workshop-build-an-agent}"
PORT="${PORT:-8888}"
VENV="$REPO/.venv"
SHIM_DIR="${SHIM_DIR:-/sandbox/netlink-stub}"
SHIM_SO="$SHIM_DIR/netlink-stub.so"
LAUNCHER_DIR="$REPO/.launcher-config"
RUNTIME_DIR="${JUPYTER_RUNTIME_DIR:-/tmp/jrt}"
REPO_SLUG="${REPO_SLUG:-brevdev/workshop-build-an-agent}"
BRANCH="${BRANCH:-edwli-dev}"
# CRITICAL: uv/TLS must use the OpenShell proxy CA bundle, NOT the system store.
export SSL_CERT_FILE="${SSL_CERT_FILE:-/etc/openshell-tls/ca-bundle.pem}"
export PIP_CERT="$SSL_CERT_FILE"

# SKILL_DIR = directory this script lives in (…/setup-workshop-nemoclaw)
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

say() { printf '\n=== %s ===\n' "$*"; }

# ---- 0. preflight -----------------------------------------------------------
say "0. preflight"
[ -d "$REPO" ] || { echo "FATAL: repo not found at $REPO. Clone it first (needs the github_git_clone policy block):"; \
  echo "  git clone --branch $BRANCH https://github.com/$REPO_SLUG $REPO"; exit 1; }
command -v uv >/dev/null || { echo "FATAL: uv not on PATH"; exit 1; }
[ -f "$SSL_CERT_FILE" ] || { echo "FATAL: CA bundle missing at $SSL_CERT_FILE"; exit 1; }
[ -f "$REPO/secrets.env" ] || echo "WARN: $REPO/secrets.env missing — notebooks will lack NVIDIA_API_KEY (operator must stage it; see references/operator-contract.md)."
mkdir -p "$RUNTIME_DIR"

# ---- 1. venv + deps ---------------------------------------------------------
say "1. venv + pinned deps"
if [ ! -x "$VENV/bin/python" ]; then
  uv venv "$VENV"
fi
# Install the exact pinned set proven to work (modules 1-3 + tiles + tooling).
# GPU-only deps (torch/unsloth/cudf) are intentionally OMITTED — modules 4 & 6
# need a GPU we don't have and installing them hangs voila.
uv pip install -p "$VENV/bin/python" -r "$SKILL_DIR/templates/requirements-sandbox.txt"

# ---- 2. netlink LD_PRELOAD shim (build with zig cc; no system gcc) ----------
say "2. netlink shim"
if [ ! -f "$SHIM_SO" ]; then
  mkdir -p "$SHIM_DIR"
  cp "$SKILL_DIR/templates/netlink-stub.c" "$SHIM_DIR/netlink-stub.c"
  # ziglang wheel ships a C compiler; use it since gcc/npm are unavailable.
  "$VENV/bin/python" -m ziglang cc -shared -fPIC -O2 \
      -o "$SHIM_SO" "$SHIM_DIR/netlink-stub.c"
fi
[ -f "$SHIM_SO" ] || { echo "FATAL: shim build failed"; exit 1; }

# ---- 3. bridge labextension (window.jupyterapp) -----------------------------
say "3. devx-jupyterapp-bridge labextension"
LABEXT_ROOT="$VENV/share/jupyter/labextensions"
if [ ! -f "$LABEXT_ROOT/devx-jupyterapp-bridge/static/remoteEntry.js" ]; then
  mkdir -p "$LABEXT_ROOT"
  tar -C "$LABEXT_ROOT" -xzf "$SKILL_DIR/assets/devx-jupyterapp-bridge.tar.gz"
fi
[ -f "$LABEXT_ROOT/devx-jupyterapp-bridge/static/remoteEntry.js" ] || { echo "FATAL: bridge extraction failed"; exit 1; }

# ---- 4. launcher config with rewritten paths + anti-duplication -------------
say "4. launcher config"
mkdir -p "$LAUNCHER_DIR"
# Install the working 11-tile config (paths already rewritten /project -> $REPO;
# Secrets Manager tile is type: jupyterlab-commands — see sandbox-internals.md).
sed "s#/sandbox/workshop-build-an-agent#$REPO#g" \
    "$SKILL_DIR/templates/jp_app_launcher.yaml" > "$LAUNCHER_DIR/jp_app_launcher.yaml"
# ANTI-DUPLICATION: the extension reads configs from BOTH cwd AND
# JUPYTER_APP_LAUNCHER_PATH. Move the repo-root copy aside + kill stale
# checkpoints, or you get 22 tiles (two of everything, one set letter-iconed).
if [ -f "$REPO/jp_app_launcher.yaml" ]; then
  mv "$REPO/jp_app_launcher.yaml" "/sandbox/original-root-jp_app_launcher.yaml.bak"
fi
rm -f "$REPO/.ipynb_checkpoints/jp_app_launcher-checkpoint.yaml" 2>/dev/null || true

# ---- 5. remove leftover IPC-transport experiment (superseded by the shim) ---
say "5. stale jupyter_server_config cleanup"
JCFG=/sandbox/.jupyter/jupyter_server_config.py
if [ -f "$JCFG" ] && grep -q 'transport *= *"ipc"' "$JCFG"; then
  mv "$JCFG" "$JCFG.bak"
  echo "moved aside $JCFG (forced IPC transport; necessary-but-insufficient — the shim is the fix)"
else
  echo "no stale IPC config"
fi

# ---- 6. neutralize blocking %pip cells in secrets notebooks -----------------
say "6. neutralize %pip cells"
"$VENV/bin/python" "$SKILL_DIR/scripts/neutralize_pip_cells.py" "$REPO"

say "SETUP COMPLETE — now run: bash $SKILL_DIR/scripts/start-jupyter.sh"
