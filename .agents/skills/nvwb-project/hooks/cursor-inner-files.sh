#!/usr/bin/env bash
# cursor-inner-files.sh — Cursor preToolUse hook (Write matcher) for the inner agent
# Enforces bridge file ownership: inner agent can only write to inner.md
# and common-context/context.md within agent-bridge/.
#
# Cursor hook: preToolUse (matcher: "Write")
# Input: { tool_name, tool_input: { file_path, ... }, tool_use_id, cwd, agent_message }
# Output: { decision: "allow"|"deny", reason }

set -euo pipefail

INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path')"

# Block writes to hook configuration and hook scripts
if [[ "$FILE_PATH" == */.claude/settings.json || \
      "$FILE_PATH" == */.claude/settings.local.json || \
      "$FILE_PATH" == */.cursor/hooks.json || \
      "$FILE_PATH" == */agent-bridge/hooks/* ]]; then
  jq -n '{
    "decision": "deny",
    "reason": "Modifying hook configuration or hook scripts is not permitted."
  }'
  exit 0
fi

# Constrain writes inside agent-bridge/
if [[ "$FILE_PATH" == */agent-bridge/* ]]; then
  # Allow: inner.md
  if [[ "$FILE_PATH" == */agent-bridge/inner.md ]]; then
    jq -n '{"decision": "allow"}'
    exit 0
  fi

  # Allow: common-context/context.md
  if [[ "$FILE_PATH" == */agent-bridge/common-context/context.md ]]; then
    jq -n '{"decision": "allow"}'
    exit 0
  fi

  # Deny: outer.md (belongs to outer agent)
  if [[ "$FILE_PATH" == */agent-bridge/outer.md ]]; then
    jq -n '{
      "decision": "deny",
      "reason": "outer.md belongs to the outer agent. Write your requests to inner.md instead."
    }'
    exit 0
  fi

  # Deny: anything else in agent-bridge/
  jq -n '{
    "decision": "deny",
    "reason": "Do not place files in agent-bridge/. It is a communication channel, not a file staging area. Write requests to inner.md and shared state to common-context/context.md."
  }'
  exit 0
fi

# All other paths: allow (inner agent can freely edit project code)
jq -n '{"decision": "allow"}'
