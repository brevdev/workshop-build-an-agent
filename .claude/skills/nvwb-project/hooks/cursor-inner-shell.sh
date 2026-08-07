#!/usr/bin/env bash
# cursor-inner-shell.sh — Cursor preToolUse hook (Shell matcher) for the inner agent
# Blocks nvwb commands (not available in container), blocks env dumps,
# and scrubs sensitive variables from all other commands.
#
# Cursor hook: preToolUse (matcher: "Shell")
# Input: { tool_name, tool_input: { command }, tool_use_id, cwd, agent_message }
# Output: { decision: "allow"|"deny", reason, updated_input }

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/sensitive-patterns.sh"

INPUT="$(cat)"
COMMAND="$(echo "$INPUT" | jq -r '.tool_input.command')"

# Block nvwb commands — redirect to bridge
if [[ "$COMMAND" =~ ^[[:space:]]*nvwb(\ |$) ]]; then
  jq -n '{
    "decision": "deny",
    "reason": "nvwb is not available inside the container. Write your request to /project/agent-bridge/inner.md and the outer agent will run it on the local machine."
  }'
  exit 0
fi

# Block environment variable dump commands
if is_env_dump_command "$COMMAND"; then
  jq -n '{
    "decision": "deny",
    "reason": "Dumping environment variables is blocked to protect sensitive values (API keys, tokens). Access specific non-sensitive variables individually if needed."
  }'
  exit 0
fi

# For all other commands: wrap with env -u to scrub sensitive vars
WRAPPED="$(wrap_command "$COMMAND")"

if [[ "$WRAPPED" != "$COMMAND" ]]; then
  jq -n --arg cmd "$WRAPPED" '{
    "decision": "allow",
    "updated_input": {
      "command": $cmd
    }
  }'
else
  jq -n '{"decision": "allow"}'
fi
