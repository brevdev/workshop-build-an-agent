#!/usr/bin/env bash

# Shared helpers for the operator scripts. Source, don't execute.

# resolve_sandbox_container <sandbox-name>
# Prints the single container name for the sandbox, selected by OpenShell
# runtime labels (stable across versions; container NAME patterns are not).
# Fail-closed: exactly one match or return 1 with a diagnostic on stderr.
resolve_sandbox_container() {
  local sandbox="$1" c
  c=$(docker ps --filter 'label=openshell.ai/managed-by=openshell' \
                --filter "label=openshell.ai/sandbox-name=${sandbox}" \
                --format '{{.Names}}')
  if [ -n "$c" ] && [ "$(printf '%s\n' "$c" | wc -l)" -eq 1 ]; then
    printf '%s\n' "$c"
  else
    echo "expected exactly one container labeled openshell.ai/sandbox-name=${sandbox}, got: ${c:-none}" >&2
    return 1
  fi
}
