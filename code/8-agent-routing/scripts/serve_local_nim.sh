#!/bin/bash
# Exercise 4b (optional, needs a GPU): run the weak target on YOUR hardware.
#
#   bash scripts/serve_local_nim.sh
#
# Same runbook as Module 2's "Migrate to Local NIM" page (.devx/2-agentic-rag/migrate.md),
# parameterised. Override any of these:
#   NIM_IMAGE=nvcr.io/nim/nvidia/nemotron-3-nano:latest
#   NIM_NAME=nemotron  NIM_PORT=8000  NIM_NETWORK=workbench  NIM_GPUS=1  NIM_CACHE=nim-cache
#
# Then point [targets.weak] at it in routes.toml (see the 4b block at the bottom of
# routes.toml.template) and restart the gateway. The route id, the algorithm and your
# app all stay exactly as they were — only where the tokens are made changes.

set -euo pipefail

command -v docker >/dev/null 2>&1 || {
    echo "Docker required — Ex4b is optional; Ex4a is the full exercise." >&2; exit 1; }
[ -n "${NVIDIA_API_KEY:-}" ] || {
    echo "ERROR: NVIDIA_API_KEY is not set (it is also the NGC pull secret)." >&2
    echo "       Run:  set -a; source secrets.env; set +a" >&2; exit 1; }

NIM_IMAGE="${NIM_IMAGE:-nvcr.io/nim/nvidia/nemotron-3-nano:latest}"
NIM_NAME="${NIM_NAME:-nemotron}"
NIM_PORT="${NIM_PORT:-8000}"
NIM_NETWORK="${NIM_NETWORK:-workbench}"
NIM_GPUS="${NIM_GPUS:-1}"
NIM_CACHE="${NIM_CACHE:-nim-cache}"

echo "==> [1/3] Logging in to nvcr.io"
echo "$NVIDIA_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin

echo "==> [2/3] NIM model cache volume: ${NIM_CACHE}"
docker volume create "$NIM_CACHE" >/dev/null

# The workshop's agent containers share the `workbench` docker network, which is how
# routes.toml can name the NIM `http://nemotron:8000/v1`. Outside it, fall back to the
# default bridge and reach the NIM on localhost instead.
NET_ARGS=(--network "$NIM_NETWORK")
BASE_URL="http://${NIM_NAME}:${NIM_PORT}/v1"
if ! docker network inspect "$NIM_NETWORK" >/dev/null 2>&1; then
    echo "    (no docker network '${NIM_NETWORK}' — using the default bridge)"
    NET_ARGS=()
    BASE_URL="http://localhost:${NIM_PORT}/v1"
fi

echo "==> [3/3] Starting ${NIM_IMAGE}"
echo "    First run pulls the image and the model weights — expect several minutes."
echo "    Ready when it logs 'Application startup complete'."
echo "    Then in routes.toml:  base_url = \"${BASE_URL}\""
exec docker run -it --rm \
    --name "$NIM_NAME" \
    "${NET_ARGS[@]}" \
    --gpus "$NIM_GPUS" \
    --shm-size=16GB \
    -e NGC_API_KEY="$NVIDIA_API_KEY" \
    -v "${NIM_CACHE}:/opt/nim/.cache" \
    -u "$(id -u)" \
    -p "${NIM_PORT}:8000" \
    "$NIM_IMAGE"
