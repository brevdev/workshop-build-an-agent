#!/bin/bash
# Remove the workshop's NemoClaw install from this Workbench project — Module 6.
#
# `nemoclaw <sandbox> destroy --cleanup-gateway` removes the sandbox, but
# install-nemoclaw.sh's Workbench adaptations leave more behind: the
# compatibility gateway container, its network, gateway state in the shared
# volume, the socat tunnel, and build images. This script removes the sandbox,
# runs the official uninstaller, then removes those leftovers so disk space and
# port 8080 return to their pre-install state.
#
#   bash code/6-agent-safety/scripts/uninstall-nemoclaw.sh          # asks first
#   bash code/6-agent-safety/scripts/uninstall-nemoclaw.sh --yes    # no prompt
#
# Add --all-images to also remove the public base images the sandbox build
# pulled (python, ubuntu, node, busybox). Leave them if other projects on this
# Docker host use them.
#
# Destroying the sandbox deletes its workspace files. Save anything you need
# first. Reinstall later with install-nemoclaw.sh.

set -u

SANDBOX_NAME="${NEMOCLAW_SANDBOX_NAME:-my-assistant}"
GATEWAY_NAME="${NEMOCLAW_OPENSHELL_GATEWAY_COMPAT_CONTAINER_NAME:-nemoclaw-openshell-gateway}"
SHARED_DIR="${WORKSHOP_NEMOCLAW_SHARED_DIR:-/nvwb-shared-volume/nemoclaw}"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"

ASSUME_YES=0
ALL_IMAGES=0
for arg in "$@"; do
    case "$arg" in
        --yes|-y) ASSUME_YES=1 ;;
        --all-images) ALL_IMAGES=1 ;;
        -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Unknown option: $arg (see --help)"; exit 2 ;;
    esac
done

step() { printf '\n== %s\n' "$1"; }
note() { printf '   %s\n' "$1"; }

if [[ "$ASSUME_YES" != "1" ]]; then
    echo "This removes the NemoClaw sandbox '$SANDBOX_NAME' (including its workspace files),"
    echo "the NemoClaw and OpenShell CLIs, the gateway, and their Docker resources."
    read -r -p "Continue? [y/N] " answer
    [[ "$answer" =~ ^[Yy]([Ee][Ss])?$ ]] || { echo "Nothing removed."; exit 1; }
fi

DOCKER_HOST_IP=$(awk '$2=="00000000"{printf "%d.%d.%d.%d\n", "0x"substr($3,7,2), "0x"substr($3,5,2), "0x"substr($3,3,2), "0x"substr($3,1,2); exit}' /proc/net/route)
gateway_running() {
    docker ps --filter "name=^/${GATEWAY_NAME}$" --filter status=running -q 2>/dev/null | grep -q .
}

if command -v nemoclaw >/dev/null 2>&1; then
    step "Destroying sandbox '$SANDBOX_NAME'"
    # The CLI reaches the compatibility gateway through the workshop tunnel.
    if gateway_running && ! pgrep -f "socat TCP-LISTEN:8080" >/dev/null 2>&1 && command -v socat >/dev/null 2>&1; then
        setsid socat TCP-LISTEN:8080,bind=127.0.0.1,fork,reuseaddr "TCP:${DOCKER_HOST_IP}:8080" >/dev/null 2>&1 &
        disown
        sleep 0.5
    fi
    if timeout 180 nemoclaw "$SANDBOX_NAME" destroy --yes --cleanup-gateway; then
        note "Sandbox removed."
    else
        note "Sandbox destroy did not complete; continuing with direct cleanup."
    fi

    step "Running the official NemoClaw uninstaller"
    if timeout 300 nemoclaw uninstall --yes; then
        note "NemoClaw CLI, OpenShell and their state removed."
    else
        note "The official uninstaller did not complete; continuing with direct cleanup."
    fi
else
    step "NemoClaw CLI not found; cleaning up remaining resources"
fi

step "Stopping the workshop tunnel"
pkill -f "socat TCP-LISTEN:8080" 2>/dev/null && note "Tunnel stopped." || note "No tunnel running."

step "Removing workshop gateway resources"
# Sandbox containers are children of the gateway; remove them first.
mapfile -t containers < <(docker ps -a --format '{{.ID}} {{.Image}} {{.Names}}' 2>/dev/null \
    | grep -iE 'openshell|openclaw|nemoclaw' | awk '{print $1}')
if ((${#containers[@]})); then
    docker rm -f "${containers[@]}" >/dev/null 2>&1 && note "Removed ${#containers[@]} container(s)."
else
    note "No NemoClaw containers left."
fi
docker rm -f "$GATEWAY_NAME" >/dev/null 2>&1 || true
for network in $(docker network ls --format '{{.Name}}' 2>/dev/null | grep -E '^openshell'); do
    docker network rm "$network" >/dev/null 2>&1 && note "Removed network $network."
done
for volume in $(docker volume ls --format '{{.Name}}' 2>/dev/null | grep -iE 'openshell|nemoclaw'); do
    docker volume rm "$volume" >/dev/null 2>&1 && note "Removed volume $volume."
done

step "Removing NemoClaw images"
mapfile -t images < <(docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' 2>/dev/null \
    | grep -iE 'openshell|openclaw|nemoclaw' | awk '{print $2}' | sort -u)
if ((${#images[@]})); then
    docker rmi -f "${images[@]}" >/dev/null 2>&1
    note "Removed ${#images[@]} image(s)."
else
    note "No NemoClaw images left."
fi
if [[ "$ALL_IMAGES" == "1" ]]; then
    for image in python:3.11-slim ubuntu:24.04 busybox:latest busybox; do
        docker rmi "$image" >/dev/null 2>&1 && note "Removed $image."
    done
    for image in $(docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -E '^node:'); do
        docker rmi "$image" >/dev/null 2>&1 && note "Removed $image."
    done
fi
# Untagged layers left by the sandbox build; never removes tagged images.
docker image prune -f >/dev/null 2>&1 && note "Removed dangling build layers."

step "Removing workshop state"
if [[ -d "$SHARED_DIR" ]]; then
    rm -rf -- "$SHARED_DIR" && note "Removed $SHARED_DIR."
fi
rm -rf -- /tmp/nemoclaw-docker.* 2>/dev/null
note "Logs kept for reference: /tmp/nemoclaw-install.log, /tmp/nemoclaw-tunnel.log"

step "Done"
note "Reinstall with: bash $SCRIPT_DIR/install-nemoclaw.sh"
