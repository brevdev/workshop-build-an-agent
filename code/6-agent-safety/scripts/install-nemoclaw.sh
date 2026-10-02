#!/bin/bash
# Install and onboard NemoClaw from inside the Workbench project container.
#
# Why this script exists (vs. the upstream one-liner):
#
#   1. On Workbench's older glibc, NemoClaw v0.0.49's compatibility gateway
#      uses Docker host networking, but its CLI
#      dials 127.0.0.1:8080 — which inside this container is the container's
#      own loopback. A socat tunnel bridges 127.0.0.1:8080 -> the Docker
#      bridge IP, where the host's gateway listens.
#
#   2. NemoClaw's preflight port check fails if anything (including socat)
#      is bound to 127.0.0.1:8080 when onboard starts. A watcher subshell
#      waits for the gateway container to appear, then starts socat in the
#      window between preflight and the readiness poll.
#
#   3. NemoClaw's "cleanup previous session" doesn't actually destroy the
#      gateway container, so a failed prior run leaves stale state on the
#      host. We remove it explicitly.
#
#   4. Sibling containers need Docker-host bind paths. The provided adapter
#      stages gateway binaries/state in Workbench's existing shared volume.
#
# A Ready target sandbox takes the fast path. Otherwise onboarding may
# recreate gateway state; use this helper for the disposable workshop setup.

set -uo pipefail
umask 077

LOG=/tmp/nemoclaw-install.log
TUNNEL_LOG=/tmp/nemoclaw-tunnel.log
touch "$LOG" "$TUNNEL_LOG" || exit 1
chmod 600 "$LOG" "$TUNNEL_LOG" || exit 1
NEMOCLAW_TAG="${NEMOCLAW_INSTALL_TAG:-v0.0.49}"
SANDBOX_NAME="${NEMOCLAW_SANDBOX_NAME:-my-assistant}"
GATEWAY_NAME="${NEMOCLAW_OPENSHELL_GATEWAY_COMPAT_CONTAINER_NAME:-nemoclaw-openshell-gateway}"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

# Pair the pinned CLI with the base built at its release commit. Upstream's
# mutable :latest now contains an incompatible OpenClaw bundle.
if [[ "${NEMOCLAW_INSTALL_REF:-$NEMOCLAW_TAG}" == "v0.0.49" && -z "${NEMOCLAW_SANDBOX_BASE_IMAGE_REF:-}" ]]; then
    export NEMOCLAW_SANDBOX_BASE_IMAGE_REF="ghcr.io/nvidia/nemoclaw/sandbox-base@sha256:3d36a38a03e4729f97d19db5226d767fb4583dd0ea52bc083458f7601164e1c8"
fi

log() { echo "$@" | tee -a "$LOG"; }

command -v socat >/dev/null 2>&1 || {
    echo "ERROR: socat not found. It should have been installed via preBuild.bash."
    echo "       Manual install: sudo apt-get update && sudo apt-get install -y socat"
    exit 1
}

DOCKER_HOST_IP=$(awk '$2=="00000000"{printf "%d.%d.%d.%d\n", "0x"substr($3,7,2), "0x"substr($3,5,2), "0x"substr($3,3,2), "0x"substr($3,1,2); exit}' /proc/net/route)
log "=== NemoClaw setup $(date) ==="
log "Docker host IP: $DOCKER_HOST_IP"

ensure_tunnel() {
    pgrep -f "socat TCP-LISTEN:8080" >/dev/null 2>&1 && return 0
    nohup socat TCP-LISTEN:8080,bind=127.0.0.1,fork,reuseaddr "TCP:${DOCKER_HOST_IP}:8080" \
        > "$TUNNEL_LOG" 2>&1 &
    disown
    sleep 0.5
}

stop_tunnel() {
    pkill -f "socat TCP-LISTEN:8080" 2>/dev/null || true
}

sandbox_ready() {
    local status_out
    status_out="$(timeout 20 nemoclaw "$SANDBOX_NAME" status 2>&1)" || return 1
    printf '%s\n' "$status_out" \
        | sed -r 's/\x1b\[[0-9;]*[a-zA-Z]//g' \
        | grep -iE '^[[:space:]]*Phase:[[:space:]]*Ready([[:space:]]|$)' >/dev/null
}

gateway_bind_is_private() {
    local gateway_env
    gateway_env=$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$GATEWAY_NAME" 2>/dev/null) || return 0
    printf '%s\n' "$gateway_env" | grep -Fx "OPENSHELL_BIND_ADDRESS=$DOCKER_HOST_IP" >/dev/null
}

# Fast path: NemoClaw already installed — just ensure the tunnel and exit
if command -v nemoclaw >/dev/null 2>&1; then
    ensure_tunnel
    if sandbox_ready && gateway_bind_is_private; then
        log "✓ NemoClaw sandbox '$SANDBOX_NAME' is Ready."
        exit 0
    fi
    log "NemoClaw sandbox '$SANDBOX_NAME' is not Ready or its gateway bind needs repair; will re-onboard."
    stop_tunnel
fi

# The shared volume is mounted at a different path on the Docker host.
# Keep this adapter local to the installer and its gateway child processes.
DOCKER_ADAPTER_DIR=""
if [[ -d /nvwb-shared-volume || -n "${WORKSHOP_NEMOCLAW_SHARED_DIR:-}" ]]; then
    export WORKSHOP_NEMOCLAW_SHARED_DIR="${WORKSHOP_NEMOCLAW_SHARED_DIR:-/nvwb-shared-volume/nemoclaw}"
    export NEMOCLAW_OPENSHELL_GATEWAY_STATE_DIR="${NEMOCLAW_OPENSHELL_GATEWAY_STATE_DIR:-$WORKSHOP_NEMOCLAW_SHARED_DIR/state}"
    mkdir -p "$WORKSHOP_NEMOCLAW_SHARED_DIR" "$NEMOCLAW_OPENSHELL_GATEWAY_STATE_DIR" || exit 1
    chmod 700 "$WORKSHOP_NEMOCLAW_SHARED_DIR" "$NEMOCLAW_OPENSHELL_GATEWAY_STATE_DIR" || exit 1
    export WORKSHOP_REAL_DOCKER
    WORKSHOP_REAL_DOCKER=$(command -v docker) || exit 1
    export WORKSHOP_DOCKER_HOST_IP="$DOCKER_HOST_IP"
    export NEMOCLAW_OPENSHELL_GATEWAY_CONTAINER_PATCH=1
    DOCKER_ADAPTER_DIR=$(mktemp -d /tmp/nemoclaw-docker.XXXXXX) || exit 1
    cp "$SCRIPT_DIR/workbench_docker.py" "$DOCKER_ADAPTER_DIR/docker" || exit 1
    chmod 755 "$DOCKER_ADAPTER_DIR/docker"
    python3 - "$DOCKER_ADAPTER_DIR/config.json" <<'PY'
import json, os, sys
from pathlib import Path
settings = {name: os.environ[name] for name in (
    'WORKSHOP_REAL_DOCKER', 'WORKSHOP_NEMOCLAW_SHARED_DIR',
    'NEMOCLAW_OPENSHELL_GATEWAY_STATE_DIR', 'WORKSHOP_DOCKER_HOST_IP')}
settings['NEMOCLAW_OPENSHELL_GATEWAY_COMPAT_CONTAINER_NAME'] = os.environ.get(
    'NEMOCLAW_OPENSHELL_GATEWAY_COMPAT_CONTAINER_NAME', 'nemoclaw-openshell-gateway')
settings['WORKSHOP_CLIENT_CONTAINER'] = os.environ.get('WORKSHOP_CLIENT_CONTAINER', os.environ.get('HOSTNAME', ''))
Path(sys.argv[1]).write_text(json.dumps(settings))
PY
    if [[ $? -ne 0 ]]; then rm -rf -- "$DOCKER_ADAPTER_DIR"; exit 1; fi
    export PATH="$DOCKER_ADAPTER_DIR:$PATH"
fi

# Full install path
log "Cleaning up any stale gateway container..."
docker rm -f "$GATEWAY_NAME" >> "$LOG" 2>&1 || true

log "Starting deferred-tunnel watcher (will fire socat once the gateway appears)..."
: > "$TUNNEL_LOG"
(
    while ! docker ps --filter "name=$GATEWAY_NAME" \
                      --filter "status=running" -q 2>/dev/null | grep -q .; do
        sleep 0.5
    done
    echo "[watcher $(date +%T)] gateway container up; starting socat" >> "$TUNNEL_LOG"
    exec socat TCP-LISTEN:8080,bind=127.0.0.1,fork,reuseaddr "TCP:${DOCKER_HOST_IP}:8080" \
        >> "$TUNNEL_LOG" 2>&1
) &
WATCHER_PID=$!
disown "$WATCHER_PID"
trap 'kill "$WATCHER_PID" 2>/dev/null || true; if [[ -n "$DOCKER_ADAPTER_DIR" ]]; then rm -rf -- "$DOCKER_ADAPTER_DIR"; fi' EXIT

log "Running NemoClaw installer (tag: ${NEMOCLAW_TAG})..."
log ""

if curl -fsSL https://www.nvidia.com/nemoclaw.sh \
       | NEMOCLAW_INSTALL_TAG="${NEMOCLAW_TAG}" NEMOCLAW_NO_EXPRESS=1 bash 2>&1 | tee -a "$LOG"; then
    if ! sandbox_ready || ! gateway_bind_is_private; then
        log "Installer finished, but sandbox readiness or the private gateway bind check failed. Run the health check before continuing."
        exit 1
    fi
    # A native gateway needs no compatibility tunnel or waiting watcher.
    if ! docker ps --filter "name=$GATEWAY_NAME" --filter "status=running" -q | grep -q .; then
        kill "$WATCHER_PID" 2>/dev/null || true
    fi
    trap - EXIT
    if [[ -n "$DOCKER_ADAPTER_DIR" ]]; then rm -rf -- "$DOCKER_ADAPTER_DIR"; fi
    log ""
    log "✓ NemoClaw installed and onboarded."
    log "  Tunnel PID: $(pgrep -f 'socat TCP-LISTEN:8080' || echo '?')"
    log "  Logs: $LOG (install), $TUNNEL_LOG (tunnel)"
    log "  If the project container restarts, re-run this script to restore the tunnel."
    exit 0
else
    rc=$?
    log "Installer exited with code ${rc}. See $LOG and $TUNNEL_LOG for details."
    exit "$rc"
fi
