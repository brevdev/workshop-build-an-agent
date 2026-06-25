#!/usr/bin/env bash
# test-hooks.sh — Smoke tests for agent sandbox hooks
# Requires: jq, bash
# Run from the hooks/ directory: ./test-hooks.sh
#
# Setup: creates a temporary common-context/.sensitive-vars for testing,
# then cleans it up afterward.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PASS=0
FAIL=0

# Setup temp .sensitive-vars and a mock spec.yaml with execution.secrets
mkdir -p "$SCRIPT_DIR/../common-context"
mkdir -p "$SCRIPT_DIR/../.project"

cat > "$SCRIPT_DIR/../common-context/.sensitive-vars" << 'EOF'
# Test sensitive vars
MY_CUSTOM_SECRET
EOF

cat > "$SCRIPT_DIR/../.project/spec.yaml" << 'EOF'
specVersion: v2
meta:
    name: test-project
execution:
    secrets:
        - variable: NVIDIA_API_KEY
          description: "NVIDIA API key"
        - variable: HF_TOKEN
          description: "Hugging Face token"
EOF

cleanup() {
  rm -rf "$SCRIPT_DIR/../common-context"
  rm -rf "$SCRIPT_DIR/../.project"
}
trap cleanup EXIT

assert_deny() {
  local test_name="$1"
  local script="$2"
  local input="$3"
  local output
  output="$(echo "$input" | "./$script" 2>/dev/null)" || true
  if echo "$output" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' > /dev/null 2>&1; then
    echo "  PASS: $test_name"
    ((PASS++))
  else
    echo "  FAIL: $test_name (expected deny, got: $output)"
    ((FAIL++))
  fi
}

assert_allow() {
  local test_name="$1"
  local script="$2"
  local input="$3"
  local exit_code=0
  local output
  output="$(echo "$input" | "./$script" 2>/dev/null)" || exit_code=$?

  # Allow means either: exit 0 with no JSON, exit 0 with allow decision, or exit 0 with updatedInput
  if [[ $exit_code -eq 0 ]]; then
    if [[ -z "$output" ]]; then
      echo "  PASS: $test_name (exit 0, no output)"
      ((PASS++))
    elif echo "$output" | jq -e '.hookSpecificOutput.permissionDecision == "allow"' > /dev/null 2>&1; then
      echo "  PASS: $test_name (explicit allow)"
      ((PASS++))
    else
      echo "  FAIL: $test_name (exit 0 but unexpected output: $output)"
      ((FAIL++))
    fi
  else
    echo "  FAIL: $test_name (exit code $exit_code, output: $output)"
    ((FAIL++))
  fi
}

assert_allow_with_wrapping() {
  local test_name="$1"
  local script="$2"
  local input="$3"
  local output
  output="$(echo "$input" | "./$script" 2>/dev/null)" || true
  if echo "$output" | jq -e '.hookSpecificOutput.updatedInput.command' > /dev/null 2>&1; then
    local wrapped
    wrapped="$(echo "$output" | jq -r '.hookSpecificOutput.updatedInput.command')"
    if [[ "$wrapped" == env\ -u* ]]; then
      echo "  PASS: $test_name (wrapped with env -u)"
      ((PASS++))
    else
      echo "  FAIL: $test_name (expected env -u wrapping, got: $wrapped)"
      ((FAIL++))
    fi
  else
    echo "  FAIL: $test_name (expected updatedInput with wrapping, got: $output)"
    ((FAIL++))
  fi
}

# ── Inner Agent: Bash ──

echo "inner-agent-bash.sh"

assert_deny "blocks nvwb status" \
  inner-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"nvwb status"}}'

assert_deny "blocks nvwb build" \
  inner-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"nvwb build"}}'

assert_deny "blocks env" \
  inner-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"env"}}'

assert_deny "blocks printenv" \
  inner-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"printenv"}}'

assert_deny "blocks export -p" \
  inner-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"export -p"}}'

# spec.yaml secrets (NVIDIA_API_KEY, HF_TOKEN) should trigger wrapping
# even without any matching env vars present
assert_allow_with_wrapping "wraps command with env -u for spec.yaml secrets" \
  inner-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'

# With a sensitive var in the environment, should also wrap
export API_KEY="test123"
assert_allow_with_wrapping "wraps ls with env -u when sensitive env vars present" \
  inner-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'

assert_allow_with_wrapping "wraps python with env -u" \
  inner-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"python3 -c \"print(1)\""}}'
unset API_KEY

echo ""

# ── Inner Agent: Files ──

echo "inner-agent-files.sh"

assert_allow "allows write to inner.md" \
  inner-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/inner.md","content":"test"}}'

assert_allow "allows write to common-context/context.md" \
  inner-agent-files.sh \
  '{"tool_name":"Edit","tool_input":{"file_path":"/project/agent-bridge/common-context/context.md","old_string":"a","new_string":"b"}}'

assert_deny "blocks write to outer.md" \
  inner-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/outer.md","content":"test"}}'

assert_deny "blocks arbitrary file in agent-bridge" \
  inner-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/somefile.py","content":"test"}}'

assert_allow "allows write to project code" \
  inner-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/code/server.py","content":"test"}}'

assert_deny "blocks write to .claude/settings.json" \
  inner-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/home/workbench/.claude/settings.json","content":"{}"}}'

assert_deny "blocks write to .cursor/hooks.json" \
  inner-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/.cursor/hooks.json","content":"{}"}}'

assert_deny "blocks write to hook scripts" \
  inner-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/hooks/inner-agent-bash.sh","content":"exit 0"}}'

echo ""

# ── Inner Agent: Read ──

echo "inner-agent-read.sh"

assert_deny "blocks reading .env" \
  inner-agent-read.sh \
  '{"tool_name":"Read","tool_input":{"file_path":"/project/.env"}}'

assert_deny "blocks reading .claude.json" \
  inner-agent-read.sh \
  '{"tool_name":"Read","tool_input":{"file_path":"/home/workbench/.claude.json"}}'

assert_allow "allows reading normal project files" \
  inner-agent-read.sh \
  '{"tool_name":"Read","tool_input":{"file_path":"/project/code/server.py"}}'

assert_allow "allows reading bridge files" \
  inner-agent-read.sh \
  '{"tool_name":"Read","tool_input":{"file_path":"/project/agent-bridge/outer.md"}}'

echo ""

# ── Outer Agent: Bash ──

echo "outer-agent-bash.sh"

assert_allow "allows nvwb status" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"nvwb status"}}'

assert_allow "allows nvwb build" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"nvwb build"}}'

assert_allow "allows nvwb compose up" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"nvwb compose up"}}'

assert_allow "allows ssh to remote context" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"ssh my-remote cat /project/agent-bridge/inner.md"}}'

assert_allow "allows ls" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"ls agent-bridge/"}}'

assert_allow "allows git status" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"git status"}}'

assert_deny "blocks env" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"env"}}'

assert_deny "blocks arbitrary python" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"python3 -c \"import os; print(os.environ)\""}}'

assert_deny "blocks npm install" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"npm install express"}}'

assert_deny "blocks rm" \
  outer-agent-bash.sh \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /project/code"}}'

echo ""

# ── Outer Agent: Files ──

echo "outer-agent-files.sh"

assert_allow "allows write to outer.md" \
  outer-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/outer.md","content":"response"}}'

assert_allow "allows write to common-context/context.md" \
  outer-agent-files.sh \
  '{"tool_name":"Edit","tool_input":{"file_path":"/project/agent-bridge/common-context/context.md","old_string":"a","new_string":"b"}}'

assert_deny "blocks write to inner.md" \
  outer-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/inner.md","content":"test"}}'

assert_deny "blocks write to project code" \
  outer-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/code/server.py","content":"test"}}'

assert_deny "blocks write to arbitrary path" \
  outer-agent-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/home/user/.bashrc","content":"test"}}'

echo ""

# ── Cursor Helpers ──
# Cursor hooks use "decision" (preToolUse) or "permission" (beforeReadFile) instead of
# Claude Code's "hookSpecificOutput.permissionDecision".

assert_cursor_deny() {
  local test_name="$1"
  local script="$2"
  local input="$3"
  local output
  output="$(echo "$input" | "./$script" 2>/dev/null)" || true
  if echo "$output" | jq -e '(.decision == "deny") or (.permission == "deny")' > /dev/null 2>&1; then
    echo "  PASS: $test_name"
    ((PASS++))
  else
    echo "  FAIL: $test_name (expected deny, got: $output)"
    ((FAIL++))
  fi
}

assert_cursor_allow() {
  local test_name="$1"
  local script="$2"
  local input="$3"
  local output
  output="$(echo "$input" | "./$script" 2>/dev/null)" || true
  if echo "$output" | jq -e '(.decision == "allow") or (.permission == "allow")' > /dev/null 2>&1; then
    echo "  PASS: $test_name"
    ((PASS++))
  else
    echo "  FAIL: $test_name (expected allow, got: $output)"
    ((FAIL++))
  fi
}

assert_cursor_allow_with_wrapping() {
  local test_name="$1"
  local script="$2"
  local input="$3"
  local output
  output="$(echo "$input" | "./$script" 2>/dev/null)" || true
  if echo "$output" | jq -e '.updated_input.command' > /dev/null 2>&1; then
    local wrapped
    wrapped="$(echo "$output" | jq -r '.updated_input.command')"
    if [[ "$wrapped" == env\ -u* ]]; then
      echo "  PASS: $test_name (wrapped with env -u)"
      ((PASS++))
    else
      echo "  FAIL: $test_name (expected env -u wrapping, got: $wrapped)"
      ((FAIL++))
    fi
  else
    echo "  FAIL: $test_name (expected updated_input with wrapping, got: $output)"
    ((FAIL++))
  fi
}

# ── Cursor Inner Agent: Shell ──

echo "cursor-inner-shell.sh"

assert_cursor_deny "blocks nvwb status" \
  cursor-inner-shell.sh \
  '{"tool_name":"Shell","tool_input":{"command":"nvwb status"},"tool_use_id":"t1","cwd":"/project"}'

assert_cursor_deny "blocks nvwb build" \
  cursor-inner-shell.sh \
  '{"tool_name":"Shell","tool_input":{"command":"nvwb build"},"tool_use_id":"t2","cwd":"/project"}'

assert_cursor_deny "blocks env" \
  cursor-inner-shell.sh \
  '{"tool_name":"Shell","tool_input":{"command":"env"},"tool_use_id":"t3","cwd":"/project"}'

assert_cursor_deny "blocks printenv" \
  cursor-inner-shell.sh \
  '{"tool_name":"Shell","tool_input":{"command":"printenv"},"tool_use_id":"t4","cwd":"/project"}'

# spec.yaml secrets should trigger wrapping
assert_cursor_allow_with_wrapping "wraps ls with env -u for spec.yaml secrets" \
  cursor-inner-shell.sh \
  '{"tool_name":"Shell","tool_input":{"command":"ls -la"},"tool_use_id":"t5","cwd":"/project"}'

export API_KEY="test123"
assert_cursor_allow_with_wrapping "wraps python with env -u for env vars" \
  cursor-inner-shell.sh \
  '{"tool_name":"Shell","tool_input":{"command":"python3 test.py"},"tool_use_id":"t6","cwd":"/project"}'
unset API_KEY

echo ""

# ── Cursor Inner Agent: Files ──

echo "cursor-inner-files.sh"

assert_cursor_allow "allows write to inner.md" \
  cursor-inner-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/inner.md"},"tool_use_id":"t1","cwd":"/project"}'

assert_cursor_allow "allows write to common-context/context.md" \
  cursor-inner-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/common-context/context.md"},"tool_use_id":"t2","cwd":"/project"}'

assert_cursor_deny "blocks write to outer.md" \
  cursor-inner-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/outer.md"},"tool_use_id":"t3","cwd":"/project"}'

assert_cursor_deny "blocks arbitrary file in agent-bridge" \
  cursor-inner-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/somefile.py"},"tool_use_id":"t4","cwd":"/project"}'

assert_cursor_allow "allows write to project code" \
  cursor-inner-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/code/server.py"},"tool_use_id":"t5","cwd":"/project"}'

assert_cursor_deny "blocks write to .claude/settings.json" \
  cursor-inner-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/home/workbench/.claude/settings.json"},"tool_use_id":"t6","cwd":"/project"}'

assert_cursor_deny "blocks write to .cursor/hooks.json" \
  cursor-inner-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/.cursor/hooks.json"},"tool_use_id":"t7","cwd":"/project"}'

assert_cursor_deny "blocks write to hook scripts" \
  cursor-inner-files.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"/project/agent-bridge/hooks/cursor-inner-shell.sh"},"tool_use_id":"t8","cwd":"/project"}'

echo ""

# ── Cursor Inner Agent: Read ──

echo "cursor-inner-read.sh"

assert_cursor_deny "blocks reading .env" \
  cursor-inner-read.sh \
  '{"file_path":"/project/.env","content":""}'

assert_cursor_deny "blocks reading .claude.json" \
  cursor-inner-read.sh \
  '{"file_path":"/home/workbench/.claude.json","content":""}'

assert_cursor_allow "allows reading normal project files" \
  cursor-inner-read.sh \
  '{"file_path":"/project/code/server.py","content":""}'

assert_cursor_allow "allows reading bridge files" \
  cursor-inner-read.sh \
  '{"file_path":"/project/agent-bridge/outer.md","content":""}'

echo ""

# ── Summary ──

echo "================================"
echo "Results: $PASS passed, $FAIL failed"
echo "================================"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
