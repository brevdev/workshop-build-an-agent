#!/usr/bin/env bash
# outer-agent-bash.sh — PreToolUse hook for Bash commands on the local machine
# Restricts outer agent to nvwb commands, SSH (for remote bridge access),
# and basic read commands. Blocks everything else.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/sensitive-patterns.sh"

INPUT="$(cat)"
COMMAND="$(echo "$INPUT" | jq -r '.tool_input.command')"

# Strip leading whitespace for matching
TRIMMED="$(echo "$COMMAND" | sed 's/^[[:space:]]*//')"

# Block environment variable dump commands
if is_env_dump_command "$COMMAND"; then
  jq -n '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": "Dumping environment variables is blocked to protect sensitive values (API keys, tokens)."
    }
  }'
  exit 0
fi

# Allowlist: commands the outer agent may run
ALLOWED=false

# nvwb commands
if [[ "$TRIMMED" =~ ^nvwb(\ |$) ]]; then
  ALLOWED=true
# ssh (for remote bridge access)
elif [[ "$TRIMMED" =~ ^ssh(\ |$) ]]; then
  ALLOWED=true
# Read-only commands for inspecting bridge files and project state
elif [[ "$TRIMMED" =~ ^(cat|head|tail|less|ls|find|wc)(\ |$) ]]; then
  ALLOWED=true
# Git read-only commands
elif [[ "$TRIMMED" =~ ^git\ (status|diff|log|show|branch)(\ |$) ]]; then
  ALLOWED=true
fi

if [[ "$ALLOWED" == "true" ]]; then
  # Wrap allowed commands with env -u to scrub sensitive vars
  WRAPPED="$(wrap_command "$COMMAND")"
  if [[ "$WRAPPED" != "$COMMAND" ]]; then
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
    exit 0
  fi
else
  jq -n --arg cmd "$TRIMMED" '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": ("Outer agent is restricted to nvwb commands, ssh, and read-only operations. Blocked: " + $cmd)
    }
  }'
  exit 0
fi
