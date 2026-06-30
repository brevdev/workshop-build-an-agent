#!/usr/bin/env bash
# inner-agent-bash.sh — PreToolUse hook for Bash commands inside the container
# Blocks nvwb commands (not available in container), blocks env dumps,
# and scrubs sensitive variables from all other commands.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/sensitive-patterns.sh"

INPUT="$(cat)"
COMMAND="$(echo "$INPUT" | jq -r '.tool_input.command')"

# Block nvwb commands — redirect to bridge
if [[ "$COMMAND" =~ ^[[:space:]]*nvwb(\ |$) ]]; then
  jq -n '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": "nvwb is not available inside the container. Write your request to /project/agent-bridge/inner.md and the outer agent will run it on the local machine."
    }
  }'
  exit 0
fi

# Block environment variable dump commands
if is_env_dump_command "$COMMAND"; then
  jq -n '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": "Dumping environment variables is blocked to protect sensitive values (API keys, tokens). Access specific non-sensitive variables individually if needed."
    }
  }'
  exit 0
fi

# For all other commands: wrap with env -u to scrub sensitive vars
WRAPPED="$(wrap_command "$COMMAND")"

if [[ "$WRAPPED" != "$COMMAND" ]]; then
  # Sensitive vars found — rewrite command
  jq -n --arg cmd "$WRAPPED" '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "allow",
      "updatedInput": {
        "command": $cmd
      }
    }
  }'
else
  # No sensitive vars to scrub — allow as-is
  exit 0
fi
