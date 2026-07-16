#!/usr/bin/env bash
# stage-nvidia-key.sh — write NVIDIA_API_KEY into the sandbox's workshop
# secrets.env WITHOUT the key touching chat, argv, logs, or shell history.
# Run on the sandbox HOST. A human should run this (it moves a credential).
#
# Key source (first match wins):
#   1. $NVIDIA_API_KEY already exported in the environment
#   2. --env-file <path>  : a dotenv file; uses NVIDIA_API_KEY or COMPATIBLE_API_KEY
#      (the NemoClaw community example's ./.env works here)
#   3. stdin (piped):     printf '%s' "$KEY" | stage-nvidia-key.sh
#
# Optional extra lines (only if the user wants those integrations; policy for
# mcp.tavily.com / api.smith.langchain.com must be added separately):
#   TAVILY_API_KEY, LANGSMITH_API_KEY — exported in env or present in --env-file.
set -euo pipefail

SANDBOX="${SANDBOX:-hermes-direct}"
DEST="${DEST:-/sandbox/workshop-build-an-agent/secrets.env}"
ENV_FILE=""
[ "${1:-}" = "--env-file" ] && ENV_FILE="${2:?usage: stage-nvidia-key.sh [--env-file <path>]}"

C=$(docker ps --format '{{.Names}}' | grep "openshell-$SANDBOX" | head -1)
[ -n "$C" ] || { echo "FATAL: no running container matching openshell-$SANDBOX"; exit 1; }

# Resolve the key into KEY without echoing it.
KEY="${NVIDIA_API_KEY:-}"
TAVILY="${TAVILY_API_KEY:-}"
LANGSMITH="${LANGSMITH_API_KEY:-}"
if [ -z "$KEY" ] && [ -n "$ENV_FILE" ]; then
  [ -f "$ENV_FILE" ] || { echo "FATAL: env file not found: $ENV_FILE"; exit 1; }
  # Subshell substitutions — the key never touches disk or argv.
  # shellcheck disable=SC1090
  KEY=$(set -a; . "$ENV_FILE" >/dev/null 2>&1; printf '%s' "${NVIDIA_API_KEY:-${COMPATIBLE_API_KEY:-}}")
  # shellcheck disable=SC1090
  TAVILY=$(set -a; . "$ENV_FILE" >/dev/null 2>&1; printf '%s' "${TAVILY_API_KEY:-}")
  # shellcheck disable=SC1090
  LANGSMITH=$(set -a; . "$ENV_FILE" >/dev/null 2>&1; printf '%s' "${LANGSMITH_API_KEY:-}")
fi
if [ -z "$KEY" ] && [ ! -t 0 ]; then
  KEY=$(cat)
fi
[ -n "$KEY" ] || { echo "FATAL: no key found (env NVIDIA_API_KEY, --env-file, or stdin). Never paste keys into agent chat."; exit 1; }

# Compose the file content and pipe it straight into the container.
{
  printf 'NVIDIA_API_KEY=%s\n' "$KEY"
  [ -n "$TAVILY" ]    && printf 'TAVILY_API_KEY=%s\n' "$TAVILY"
  [ -n "$LANGSMITH" ] && printf 'LANGSMITH_API_KEY=%s\n' "$LANGSMITH"
} | docker exec -i "$C" sh -c "umask 077; cat > $DEST && chown sandbox:sandbox $DEST"

# Verify without reading contents back.
docker exec "$C" ls -l "$DEST"
echo "Staged $DEST in $C (mode 600, owner sandbox). Tell the in-sandbox agent to re-run preflight."
