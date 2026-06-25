#!/usr/bin/env bash
# inner-agent-files.sh — PreToolUse hook for Edit/Write inside the container
# Enforces bridge file ownership: inner agent can only write to inner.md
# and common-context/context.md within agent-bridge/.

set -euo pipefail

INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path')"

# Block writes to hook configuration and hook scripts
if [[ "$FILE_PATH" == */.claude/settings.json || \
      "$FILE_PATH" == */.claude/settings.local.json || \
      "$FILE_PATH" == */.cursor/hooks.json || \
      "$FILE_PATH" == */agent-bridge/hooks/* ]]; then
  jq -n '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": "Modifying hook configuration or hook scripts is not permitted."
    }
  }'
  exit 0
fi

# Constrain writes inside agent-bridge/
if [[ "$FILE_PATH" == */agent-bridge/* ]]; then
  BASENAME="$(basename "$FILE_PATH")"
  # Allow: inner.md, context.md (in common-context/)
  if [[ "$FILE_PATH" == */agent-bridge/inner.md ]]; then
    exit 0
  elif [[ "$FILE_PATH" == */agent-bridge/common-context/context.md ]]; then
    exit 0
  elif [[ "$FILE_PATH" == */agent-bridge/outer.md ]]; then
    jq -n '{
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "outer.md belongs to the outer agent. Write your requests to inner.md instead."
      }
    }'
    exit 0
  else
    jq -n '{
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Do not place files in agent-bridge/. It is a communication channel, not a file staging area. Write requests to inner.md and shared state to common-context/context.md."
      }
    }'
    exit 0
  fi
fi

# All other paths: allow (inner agent can freely edit project code)
exit 0
