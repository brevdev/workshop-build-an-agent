#!/usr/bin/env bash
# sensitive-patterns.sh — Shared utility for env var protection
# Source this file from other hook scripts.

# Patterns that indicate a sensitive variable name (case-insensitive grep)
SENSITIVE_NAME_PATTERNS='KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH|PRIVATE'

# Known sensitive files (substrings matched against full path)
SENSITIVE_FILE_PATTERNS=(
  ".env"
  ".claude.json"
  ".netrc"
  ".npmrc"
  "credentials"
  "id_rsa"
  "id_ed25519"
)

# Resolve the hooks directory (where this script lives) to find config files
HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SENSITIVE_VARS_FILE="$HOOKS_DIR/../common-context/.sensitive-vars"

# Find spec.yaml — walk up from hooks dir looking for .project/spec.yaml
_find_spec_yaml() {
  local dir="$HOOKS_DIR"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/.project/spec.yaml" ]]; then
      echo "$dir/.project/spec.yaml"
      return
    fi
    dir="$(dirname "$dir")"
  done
  # Also check /project/ (standard container mount)
  if [[ -f "/project/.project/spec.yaml" ]]; then
    echo "/project/.project/spec.yaml"
  fi
}
SPEC_YAML="$(_find_spec_yaml)"

# get_sensitive_vars — collect sensitive variable names from:
#   1. execution.secrets in spec.yaml (the authoritative source)
#   2. .sensitive-vars file (additional project-specific overrides)
#   3. current environment variable names matching SENSITIVE_NAME_PATTERNS
# Outputs one variable name per line, deduplicated.
get_sensitive_vars() {
  {
    # From spec.yaml execution.secrets
    if [[ -n "$SPEC_YAML" && -f "$SPEC_YAML" ]]; then
      grep -A1 '^\s*- variable:' "$SPEC_YAML" | grep 'variable:' | sed 's/.*variable:\s*//' | tr -d '"'"'" | tr -d ' '
    fi

    # From explicit list
    if [[ -f "$SENSITIVE_VARS_FILE" ]]; then
      grep -v '^\s*#' "$SENSITIVE_VARS_FILE" | grep -v '^\s*$'
    fi

    # From environment — names matching sensitive patterns
    env | cut -d= -f1 | grep -iE "$SENSITIVE_NAME_PATTERNS"
  } | sort -u
}

# build_env_u_args — returns a string of -u VAR flags for use with env command
build_env_u_args() {
  local args=""
  while IFS= read -r var; do
    [[ -n "$var" ]] && args="$args -u $var"
  done < <(get_sensitive_vars)
  echo "$args"
}

# wrap_command — takes a command string, returns it wrapped with env -u for all sensitive vars
wrap_command() {
  local cmd="$1"
  local env_args
  env_args="$(build_env_u_args)"
  if [[ -n "$env_args" ]]; then
    echo "env$env_args $cmd"
  else
    echo "$cmd"
  fi
}

# is_sensitive_file — checks if a file path matches known sensitive files
# Returns 0 (true) if sensitive, 1 (false) if not.
is_sensitive_file() {
  local filepath="$1"
  local basename
  basename="$(basename "$filepath")"

  # Check built-in patterns
  for pattern in "${SENSITIVE_FILE_PATTERNS[@]}"; do
    if [[ "$basename" == *"$pattern"* || "$filepath" == *"$pattern"* ]]; then
      return 0
    fi
  done

  # Check .sensitive-vars for file paths (lines starting with /)
  if [[ -f "$SENSITIVE_VARS_FILE" ]]; then
    while IFS= read -r line; do
      [[ "$line" =~ ^/ ]] && [[ "$filepath" == *"$line"* ]] && return 0
    done < <(grep -v '^\s*#' "$SENSITIVE_VARS_FILE" | grep -v '^\s*$')
  fi

  return 1
}

# is_env_dump_command — checks if a command is trying to dump environment variables
# Returns 0 (true) if it's an env dump, 1 (false) if not.
is_env_dump_command() {
  local cmd="$1"
  # Strip leading whitespace
  cmd="$(echo "$cmd" | sed 's/^[[:space:]]*//')"

  # Exact commands or commands with pipes/redirects
  if [[ "$cmd" =~ ^(env|printenv|export\ -p|declare\ -x)(\ |$|\|) ]]; then
    return 0
  fi
  # Bare 'set' (without arguments that would make it something else)
  if [[ "$cmd" == "set" || "$cmd" =~ ^set[[:space:]]*[\|\>] ]]; then
    return 0
  fi

  return 1
}
