#!/usr/bin/env bash
# inner-agent-read.sh — PreToolUse hook for Read inside the container
# Blocks reading of sensitive files (env files, credentials, keys).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/sensitive-patterns.sh"

INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path')"

if is_sensitive_file "$FILE_PATH"; then
  jq -n --arg path "$FILE_PATH" '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": ("Reading " + $path + " is blocked because it may contain sensitive values (API keys, tokens, passwords). If you need to know which variables are set, ask the user.")
    }
  }'
  exit 0
fi

# All other files: allow
exit 0
