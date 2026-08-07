#!/usr/bin/env bash
# cursor-inner-read.sh — Cursor beforeReadFile hook for the inner agent
# Blocks reading of sensitive files (env files, credentials, keys).
#
# Cursor hook: beforeReadFile (fail-closed: script failure blocks the read)
# Input: { file_path, content, attachments }
# Output: { permission: "allow"|"deny", user_message }

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/sensitive-patterns.sh"

INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | jq -r '.file_path')"

if is_sensitive_file "$FILE_PATH"; then
  jq -n --arg path "$FILE_PATH" '{
    "permission": "deny",
    "user_message": ("Blocked: " + $path + " may contain sensitive values.")
  }'
  exit 0
fi

# All other files: allow
jq -n '{"permission": "allow"}'
