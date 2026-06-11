#!/usr/bin/env bash
# Upload the Hermes package into the Module 6 sandbox (Module 7, Exercise 5).
#
# Usage:
#   bash sandbox/upload_hermes.sh            # upload your student package
#   bash sandbox/upload_hermes.sh --answers  # upload the completed answer key
#
# Prerequisite: Module 6's NemoClaw/OpenShell stack is up (a sandbox named
# "my-assistant" is running). Every command below is from Module 6.
set -euo pipefail

SANDBOX="${HERMES_SANDBOX:-my-assistant}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$DIR/hermes"
[ "${1:-}" = "--answers" ] && SRC="$DIR/answer_key/hermes"

echo "[1/3] Removing any previous upload (ok if absent)..."
openshell sandbox exec "$SANDBOX" -- bash -c "rm -rf /sandbox/hermes/hermes" || true

echo "[2/3] Uploading $SRC -> /sandbox/hermes/hermes ..."
openshell sandbox upload "$SANDBOX" "$SRC" /sandbox/hermes/hermes

echo "[3/3] Keyless smoke test (gateway injects credentials, no NVIDIA_API_KEY)..."
openshell sandbox exec "$SANDBOX" -- bash -c \
  "cd /sandbox/hermes && HERMES_BASE_URL=https://inference.local/v1 HERMES_AUTO_APPROVE=1 python3 -m hermes --once 'Say OK if you can hear me.'"

echo
echo "Done. For the interactive REPL inside the sandbox:"
echo "    openshell sandbox connect $SANDBOX     # (or: nemoclaw $SANDBOX connect)"
echo "  then, inside the sandbox:"
echo "    cd /sandbox/hermes && export HERMES_BASE_URL=https://inference.local/v1 && python3 -m hermes"
