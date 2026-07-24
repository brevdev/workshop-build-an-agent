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

# ---- 4b. terminal rcfile (Terminal tile PATH) --------------------------------
say "4b. terminal rcfile"
# The Terminal tile spawns a LOGIN bash by default: /etc/profile resets PATH
# and the image's read-only /sandbox/.bashrc re-prepends only the hermes dirs,
# so the workshop venv (langgraph/uvicorn/streamlit) drops off PATH and every
# lesson terminal command fails with "command not found". The rc files can't
# be replaced — the supervisor denies creating/overwriting .bashrc*/.profile*
# in /sandbox even though the dir is rw. Fix: generate a custom rcfile here
# (writable) and have start-jupyter.sh spawn terminals as NON-login bash with
# --rcfile pointing at it (ServerApp.terminado_settings there).
cat > "$LAUNCHER_DIR/terminal-bashrc" <<EOF
# Generated by setup-workshop-nemoclaw setup.sh — sourced by Terminal tile bash.
[ -f /sandbox/.bashrc ] && . /sandbox/.bashrc
export PATH="$VENV/bin:\$PATH"
# TLS via the OpenShell L7 proxy CA for python tools run from terminals.
export SSL_CERT_FILE="\${SSL_CERT_FILE:-/etc/openshell-tls/ca-bundle.pem}"
export PIP_CERT="\$SSL_CERT_FILE"
# AI-Workbench parity: the platform injects the project env + configured
# secrets into terminals; here the lesson flows need them too (e.g. module-2
# \`uvicorn mcp_server:app\` hard-requires TAVILY_API_KEY at import).
set -a
[ -f "$REPO/variables.env" ] && . "$REPO/variables.env"
[ -f "$REPO/secrets.env" ] && . "$REPO/secrets.env"
set +a
# npm registry is egress-blocked; without this a stray npx (module-2 PART 2A
# remote MCP) burns ~70s/call in retry backoff before failing. Fail fast.
export NPM_CONFIG_FETCH_RETRIES=1
export NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=8000
# AI-Workbench parity: platform terminals open at the project root. Here the
# server is deliberately launched from /sandbox (launcher-config
# anti-duplication) and terminado inherits that cwd, so every repo-relative
# lesson command (\`cd code/2-agentic-rag && langgraph dev\`, …) would fail on
# first paste. Only rehome terminals that actually spawned at /sandbox.
[ "\$PWD" = /sandbox ] && cd "$REPO"
EOF

# ---- 4c. aiohttp proxy trust (async ChatNVIDIA / langgraph dev) --------------
say "4c. aiohttp trust_env patch (.pth)"
# The sandbox has no direct DNS/egress — all HTTP rides the L7 proxy via
# HTTP(S)_PROXY env vars. httpx/requests honor them by default; aiohttp does
# NOT (needs trust_env=True). langchain-nvidia-ai-endpoints' ASYNC path uses
# aiohttp, so any served agent run (langgraph dev → ainvoke → ChatNVIDIA)
# dies with "Cannot connect to host integrate.api.nvidia.com:443 [Temporary
# failure in name resolution]" while sync paths (boot-time embeddings) work.
# Venv-scoped fix: a .pth-imported module that defaults trust_env=True when
# proxy env vars are present. (site-packages sitecustomize.py is unusable —
# /usr/local/lib/nemoclaw-patches/sitecustomize.py shadows it via PYTHONPATH.)
SITE_PKGS="$("$VENV/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
cat > "$SITE_PKGS/_workshop_aiohttp_trust_env.py" <<'EOF'
"""Make aiohttp honor HTTP(S)_PROXY inside the OpenShell sandbox (loaded via
zz-workshop-aiohttp-trust-env.pth). Without this, async ChatNVIDIA calls from
langgraph dev bypass the proxy and fail DNS. No-op outside proxied envs."""
import os

if os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"):
    try:
        import aiohttp

        _orig_init = aiohttp.ClientSession.__init__

        def _patched_init(self, *args, **kwargs):
            kwargs.setdefault("trust_env", True)
            _orig_init(self, *args, **kwargs)

        aiohttp.ClientSession.__init__ = _patched_init
    except Exception:
        pass
EOF
printf 'import _workshop_aiohttp_trust_env\n' > "$SITE_PKGS/zz-workshop-aiohttp-trust-env.pth"

# ---- 4d. module-3 judge rate limiter -----------------------------------------
say "4d. module-3 judge rate limiter"
# ragas.evaluate()'s default concurrency 429s the NVIDIA API key's RPM budget
# and the module-3 RAGAS cell "succeeds" with nan metrics (verified with the
# eval notebook running SOLO). Throttle the judge model itself (sandbox copy
# of evaluation_framework.py; marker-guarded, idempotent) — fixes both the
# LLM-as-judge loops and ragas without touching any exercise cell.
"$VENV/bin/python" "$SKILL_DIR/scripts/tune_judge_rate_limit.py" "$REPO"

# ---- 4e. module-5 model map repair -------------------------------------------
say "4e. module-5 model map"
# deepseek-r1-0528 is retired from the NIM catalog (404s everywhere) and
# meta/llama-3.3-70b-instruct currently answers slower than ChatNVIDIA's 60s
# client timeout, erroring every Deep Agent turn. Remap the sandbox copies
# (backend + lab files; marker-guarded) to served, fast siblings.
"$VENV/bin/python" "$SKILL_DIR/scripts/tune_model_map.py" "$REPO"

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

# ---- 6b. sandbox notes + /project path fixes in lesson content --------------
say "6b. lesson content sandbox notes"
# Lessons written for the AI Workbench mount (`cd /project/...`) or for
# egress/hardware this sandbox deliberately lacks (npm remote-MCP, Docker,
# GPU) get a marker-guarded SANDBOX NOTE + bash-fence path rewrites, pointing
# learners at the sandbox-supported alternative already in the lesson.
"$VENV/bin/python" "$SKILL_DIR/scripts/sandbox_content_notes.py" "$REPO"

# ---- 7. propagate workshop skills into the agent's skill library ------------
say "7. propagate workshop skills into the agent skill library"
# The NemoClaw/hermes harness only scans its own skill library — repo-local
# .claude/skills are invisible to it, so a resident agent session denies all
# knowledge of the workshop unless these are copied in. Real copies (matching
# how the sandbox image bakes agents/hermes/skills/); re-running refreshes
# them. Excluded on purpose: setup-workshop-nemoclaw-operator (host-side:
# needs docker + the openshell CLI) and setup-workshop (bare-metal GPU
# installer) — both would only mislead an in-sandbox agent.
AGENT_SKILLS="${AGENT_SKILLS:-/sandbox/.hermes-data/skills}"
if [ -d "$AGENT_SKILLS" ] && [ -w "$AGENT_SKILLS" ]; then
  installed=""
  for d in "$REPO/.claude/skills"/*/; do
    name="$(basename "$d")"
    case "$name" in setup-workshop-nemoclaw-operator|setup-workshop) continue ;; esac
    # THIS skill propagates from the RUNNING copy ($SKILL_DIR), never from the
    # repo checkout — an operator-staged update in the agent library would
    # otherwise be silently reverted to the repo's older version on re-run.
    if [ "$name" = "setup-workshop-nemoclaw" ]; then
      if [ "$(readlink -f "$SKILL_DIR")" = "$(readlink -f "$AGENT_SKILLS/$name")" ]; then
        installed="$installed $name(running-copy,kept)"
        continue
      fi
      d="$SKILL_DIR/"
    fi
    [ -f "${d}SKILL.md" ] || continue
    rm -rf "${AGENT_SKILLS:?}/${name:?}"
    cp -a "$d" "$AGENT_SKILLS/$name"
    installed="$installed $name"
  done
  echo "agent skills refreshed:${installed:- (none found)}"
else
  echo "WARN: $AGENT_SKILLS missing or unwritable — skipping skill propagation (not a NemoClaw agent sandbox?)"
fi

say "SETUP COMPLETE — now run: bash $SKILL_DIR/scripts/start-jupyter.sh"
