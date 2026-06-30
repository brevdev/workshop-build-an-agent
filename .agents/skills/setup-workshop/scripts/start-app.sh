#!/usr/bin/env bash
# start-app.sh — (re)start DevX-Lab and resolve its local browser URL.
#
# Standalone (resolves the project itself) and reused by setup.sh and the
# optional systemd unit. Writes the URL to ~/.workshop-app-url and prints it.
# Idempotent: starting an already-running app is a no-op.
#
# Optional env: PROJECT_PATH, PROJECT_NAME (skip lookup), TARGET_APPLICATION,
#               GIT_REPO, URL_FILE.
set -o pipefail   # NOT -u: the nvwb function / bashrc are not -u-clean

GIT_REPO="${GIT_REPO:-https://github.com/brevdev/workshop-build-an-agent}"
TARGET_APPLICATION="${TARGET_APPLICATION:-DevX-Lab}"
URL_FILE="${URL_FILE:-$HOME/.workshop-app-url}"

# Load the nvwb shell function (bashrc may early-return for non-interactive shells)
source "$HOME/.bashrc" >/dev/null 2>&1 || true
[ -f "$HOME/.local/share/nvwb/nvwb-wrapper.sh" ] && source "$HOME/.local/share/nvwb/nvwb-wrapper.sh" >/dev/null 2>&1 || true
type nvwb >/dev/null 2>&1 || { echo "nvwb unavailable — source ~/.local/share/nvwb/nvwb-wrapper.sh"; exit 1; }

nvwb activate local >/dev/null 2>&1 || true

# Resolve project unless caller supplied it
SEL='.result[] | (.RemoteUrl // "") as $u | select($u==$r or ($u|sub("\\.git$";""))==$r or ($u|test("workshop-build-an-agent")))'
PROJECT_PATH="${PROJECT_PATH:-$(nvwb list projects -o json 2>/dev/null | jq -r --arg r "$GIT_REPO" "$SEL | .Path" | head -1)}"
PROJECT_NAME="${PROJECT_NAME:-$(nvwb list projects -o json 2>/dev/null | jq -r --arg r "$GIT_REPO" "$SEL | .Name" | head -1)}"
[ -n "$PROJECT_PATH" ] || { echo "project not found — clone/build it first"; exit 1; }

# Start. --no-browser is headless-safe; --timeout gives Jupyter time to come up.
start_out="$(nvwb start "$TARGET_APPLICATION" --no-browser --timeout 120 \
  --context local --project "$PROJECT_PATH" 2>&1)" || true
echo "$start_out"

# Prefer a URL nvwb printed; else construct from the local proxy port + project name.
proxy_port="$(jq -r '.[] | select(.name=="local").proxyPort // 10000' "$HOME/.nvwb/contexts.json" 2>/dev/null || echo 10000)"
url="$(printf '%s\n' "$start_out" | grep -oE 'https?://[^ ]+/projects/[^ ]+/applications/[^ ]+' | head -1)"
[ -n "$url" ] || url="http://localhost:${proxy_port}/projects/${PROJECT_NAME}/applications/${TARGET_APPLICATION}/"

echo "$url" > "$URL_FILE"
echo "DevX-Lab is available at: $url"
