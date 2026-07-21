#!/usr/bin/env bash
# start-jupyter.sh — launch the ONE JupyterLab server for the workshop.
# RUN FROM INSIDE THE SANDBOX. Enforces single-server discipline: stale servers
# keep the port bound (Jupyter traps SIGTERM), the relaunched shim-carrying
# server never takes over, and tiles vanish / kernels break "mysteriously".
set -euo pipefail

REPO="${REPO:-/sandbox/workshop-build-an-agent}"
PORT="${PORT:-8888}"
VENV="$REPO/.venv"
SHIM_SO="${SHIM_SO:-/sandbox/netlink-stub/netlink-stub.so}"
LAUNCHER_DIR="$REPO/.launcher-config"
RUNTIME_DIR="${JUPYTER_RUNTIME_DIR:-/tmp/jrt}"
URL_OUT="${URL_OUT:-/sandbox/workshop-url.txt}"

export SSL_CERT_FILE="${SSL_CERT_FILE:-/etc/openshell-tls/ca-bundle.pem}"
export PIP_CERT="$SSL_CERT_FILE"

[ -x "$VENV/bin/jupyter" ] || { echo "FATAL: venv missing — run setup.sh first"; exit 1; }
[ -f "$SHIM_SO" ] || { echo "FATAL: netlink shim missing at $SHIM_SO — run setup.sh first"; exit 1; }

# SINGLE-SERVER DISCIPLINE: kill everything jupyter-ish. SIGTERM is trapped by
# Jupyter, so use KILL. Also reap orphaned voila/ipykernel/streamlit children
# from previous servers.
for pat in "jupyter-lab" "voila" "ipykernel_launcher" "streamlit run"; do
  for pid in $(pgrep -f "$pat" || true); do
    kill -9 "$pid" 2>/dev/null || true
  done
done
sleep 1
if curl -s -m 2 -o /dev/null "http://127.0.0.1:$PORT/"; then
  echo "FATAL: port $PORT still answering after kill — investigate (ss/pgrep) before relaunch"
  exit 1
fi

mkdir -p "$RUNTIME_DIR"

# TOKEN REUSE: keep the previous token if we saved one, so the user's URL (and
# an operator forward already in place) survive restarts. Fresh random token
# otherwise — never a fixed string.
TOKEN=""
if [ -f "$URL_OUT" ]; then
  TOKEN="$(grep -oE 'token=[a-f0-9]+' "$URL_OUT" | head -1 | cut -d= -f2 || true)"
fi
if [ -z "$TOKEN" ]; then
  TOKEN="$(openssl rand -hex 24 2>/dev/null || "$VENV/bin/python" -c 'import secrets; print(secrets.token_hex(24))')"
fi

# TERMINALS: terminado needs PTY allocation, which the Landlock policy only
# permits when /dev/pts is in filesystem_policy.read_write. When denied,
# launch with terminals disabled so no Terminal tile appears — otherwise
# clicking it pops "Launcher Error: Unhandled error" (500; the log's "out of
# pty devices" is CPython's fallback masking the real EACCES). The grant
# activates only at sandbox recreate (fs policy is parsed at container boot;
# a live policy apply won't enable it) — after such a recreate this script
# auto-enables terminals.
if "$VENV/bin/python" -c 'import os; os.openpty()' >/dev/null 2>&1; then
  TERMINALS_ENABLED=True
else
  TERMINALS_ENABLED=False
  echo "WARN: PTY allocation denied (Landlock /dev/pts) — launching with the Terminal tile disabled."
  echo "      Operator fix: add /dev/pts to filesystem_policy.read_write, re-apply policy, re-run this script."
fi

# Launch env — every one of these is load-bearing (see SKILL.md step 7):
#  - LD_PRELOAD: netlink shim, scoped to THIS process tree only (server +
#    kernels + spawned voila/streamlit). The SERVER needs it too, not just
#    kernels — its ZMQ client sockets also call getifaddrs.
#  - PATH: venv first so the launcher's Popen(["voila"...]) / streamlit resolve.
#  - JUPYTER_APP_LAUNCHER_PATH: the rewritten 11-tile config.
#  - JUPYTER_RUNTIME_DIR: short, writable connection-file dir.
export LD_PRELOAD="$SHIM_SO"
export JUPYTER_APP_LAUNCHER_PATH="$LAUNCHER_DIR"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR"
export PATH="$VENV/bin:$PATH"
# ragas phones usage telemetry to t.explodinggradients.com — blocked egress
# here, and each blocked ping burns retries mid-notebook. Disable at source.
export RAGAS_DO_NOT_TRACK=true

# Launch from /sandbox (NOT repo root) as an extra guard against cwd-based
# duplicate launcher-config discovery. root_dir is set explicitly to the repo.
cd /sandbox
nohup "$VENV/bin/jupyter" lab \
  --ip 127.0.0.1 --port "$PORT" --no-browser \
  --ServerApp.root_dir="$REPO" \
  --ServerApp.token="$TOKEN" \
  --ServerApp.allow_remote_access=False \
  --ServerApp.terminals_enabled="$TERMINALS_ENABLED" \
  > /tmp/jupyterlab.log 2>&1 &
SERVER_PID=$!

# READINESS: probe HTTP with the token we already hold instead of scraping
# `jupyter lab list` — the server answers requests before its server-info file
# lands, and a cold first launch can exceed 30s (which used to FATAL here,
# skip the URL write, and leave a healthy server unreported). 200 = token
# accepted; bail out early if the server process dies.
URL="http://127.0.0.1:$PORT/lab?token=$TOKEN"
ready=""
for i in $(seq 1 120); do
  sleep 1
  code="$(curl -s -m 2 -o /dev/null -w '%{http_code}' "$URL" || true)"
  if [ "$code" = "200" ]; then ready=1; break; fi
  kill -0 "$SERVER_PID" 2>/dev/null || break
done
if [ -z "$ready" ]; then
  echo "FATAL: no HTTP 200 from 127.0.0.1:$PORT after ${i}s (last code ${code:-none}); see /tmp/jupyterlab.log"
  tail -20 /tmp/jupyterlab.log
  exit 1
fi

# VERIFY the serving process actually carries the shim (a stale survivor
# would not). This exact gap cost hours once.
if ! tr '\0' '\n' < "/proc/$SERVER_PID/environ" 2>/dev/null | grep -q "LD_PRELOAD=$SHIM_SO"; then
  echo "FATAL: running server (pid $SERVER_PID) lacks LD_PRELOAD — a stale server may have kept the port. Re-run this script."
  exit 1
fi

echo "$URL" | tee "$URL_OUT"
echo "JupyterLab is up on 127.0.0.1:$PORT (pid $SERVER_PID, shim verified). Token URL saved to $URL_OUT"
echo "Next: operator runs the forward; user opens the URL — see SKILL.md 'Report back to the user'."
