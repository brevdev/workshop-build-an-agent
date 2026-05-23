#!/bin/bash
# Install and onboard NemoClaw from inside the Workbench project container.
#
# Why this script exists (vs. the upstream one-liner):
#
#   1. NemoClaw v0.0.49's gateway uses Docker host networking, but its CLI
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
# Idempotent: safe to re-run. If NemoClaw is already installed and the
# gateway is responsive, the script just ensures the tunnel is up and exits.

set -u

LOG=/tmp/nemoclaw-install.log
TUNNEL_LOG=/tmp/nemoclaw-tunnel.log
NEMOCLAW_TAG="${NEMOCLAW_INSTALL_TAG:-v0.0.49}"

log() { echo "$@" | tee -a "$LOG"; }

command -v socat >/dev/null 2>&1 || {
    echo "ERROR: socat not found. It should have been installed via preBuild.bash."
    echo "       Manual install: sudo apt-get update && sudo apt-get install -y socat"
    exit 1
}

DOCKER_HOST_IP=$(awk 'NR==2{printf "%d.%d.%d.%d\n", "0x"substr($3,7,2), "0x"substr($3,5,2), "0x"substr($3,3,2), "0x"substr($3,1,2)}' /proc/net/route)
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

# Fast path: NemoClaw already installed — just ensure the tunnel and exit
if command -v nemoclaw >/dev/null 2>&1; then
    ensure_tunnel
    if nemoclaw status >/dev/null 2>&1; then
        log "✓ NemoClaw already installed and gateway responsive."
        exit 0
    fi
    log "NemoClaw installed but gateway not responsive; will re-onboard."
    stop_tunnel
fi

# Full install path
log "Cleaning up any stale gateway container..."
docker rm -f nemoclaw-openshell-gateway >> "$LOG" 2>&1 || true

log "Starting deferred-tunnel watcher (will fire socat once the gateway appears)..."
: > "$TUNNEL_LOG"
(
    while ! docker ps --filter "name=nemoclaw-openshell-gateway" \
                      --filter "status=running" -q 2>/dev/null | grep -q .; do
        sleep 0.5
    done
    echo "[watcher $(date +%T)] gateway container up; starting socat" >> "$TUNNEL_LOG"
    exec socat TCP-LISTEN:8080,bind=127.0.0.1,fork,reuseaddr "TCP:${DOCKER_HOST_IP}:8080" \
        >> "$TUNNEL_LOG" 2>&1
) &
disown

log "Running NemoClaw installer (tag: ${NEMOCLAW_TAG})..."
log ""

if curl -fsSL https://www.nvidia.com/nemoclaw.sh \
       | NEMOCLAW_INSTALL_TAG="${NEMOCLAW_TAG}" NEMOCLAW_NO_EXPRESS=1 bash; then
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
