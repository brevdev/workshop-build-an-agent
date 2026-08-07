#!/usr/bin/env bash
# outer-agent-files.sh — PreToolUse hook for Edit/Write on the local machine
# Restricts outer agent to writing only bridge response files.
# The outer agent should not modify project code.

set -euo pipefail

INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path')"

# Allow: outer.md (bridge response)
if [[ "$FILE_PATH" == */agent-bridge/outer.md ]]; then
  exit 0
fi

# Allow: common-context/context.md (shared task state)
if [[ "$FILE_PATH" == */agent-bridge/common-context/context.md ]]; then
  exit 0
fi

# Deny everything else
jq -n --arg path "$FILE_PATH" '{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": ("Outer agent cannot modify project files. Write responses to agent-bridge/outer.md and shared state to agent-bridge/common-context/context.md. Blocked: " + $path)
  }
}'
exit 0
