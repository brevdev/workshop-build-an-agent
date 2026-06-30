#!/usr/bin/env bash
# sync-codex-skills.sh — regenerate the Codex skill tree (.agents/skills/) from the
# canonical Claude Code skill tree (.claude/skills/).
#
# WHY THIS EXISTS
# ---------------
# This workshop ships its tutor as *skills*. The "Agent Skills" format (SKILL.md +
# progressive-disclosure references/) is a cross-harness standard, so Claude Code
# (.claude/skills/) and Codex (.agents/skills/) can share ~95% of the same content.
# Codex auto-discovers project skills from <repo>/.agents/skills/ (verified via
# `codex debug prompt-input`), exactly as Claude auto-discovers <repo>/.claude/skills/.
#
# The remaining ~5% is harness-specific: a handful of invocation/path phrases ("run
# `claude`" -> "run `codex`", `.claude/skills/` -> `.agents/skills/`) and two files
# that are genuine Codex rewrites (see HAND_AUTHORED below). This script applies the
# safe, mechanical transforms deterministically so the Codex tree is reproducible and
# auditable. It is IDEMPOTENT and SURVEY-SAFE: it only rewrites exact invocation/path
# strings, never the educational content in Module 7 / the glossary that legitimately
# *names* "Claude Code" and "Codex" as objects of study, and never the `claude`->llama
# model-alias references in Module 5.
#
# USAGE
#   bash .agents/sync-codex-skills.sh          # regenerate .agents/skills from .claude/skills
#   bash .agents/sync-codex-skills.sh --check  # dry-run: fail if regenerate would change tracked output
#
# The HAND_AUTHORED files are NEVER overwritten by this script (they are Codex-specific
# rewrites maintained by hand and committed to git). After editing a .claude/skills/
# source, re-run this script and review the diff.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/.claude/skills"
DST="$REPO_ROOT/.agents/skills"

# Files (relative to the skills root) that are Codex-specific rewrites. The script
# NEITHER copies the Claude original into DST NOR overwrites the DST version.
# The cross-harness hook scripts (inner-agent-*.sh / outer-agent-*.sh) emit the
# hookSpecificOutput/PreToolUse/permissionDecision wire format that BOTH Claude Code and
# Codex consume, so they are synced (shared), not duplicated. Only files that are genuine
# Codex rewrites are hand-authored and preserved across syncs:
HAND_AUTHORED=(
  "nvwb/references/codex-in-container.md"        # Codex rewrite of nvwb/references/claude-in-container.md
  "nvwb-project/references/agent-bridge.md"      # adds a Codex-hooks wiring section
  "VENDORED.md"                                  # Codex provenance/sync note
)
# Claude/Cursor-only source files that should NOT be carried into the Codex tree.
SKIP_FROM_SRC=(
  "nvwb/references/claude-in-container.md"       # replaced by codex-in-container.md
)

is_in() { local n="$1"; shift; local x; for x in "$@"; do [ "$x" = "$n" ] && return 0; done; return 1; }

# --- surgical, survey-safe text transforms applied to *.md (most specific first) ---
apply_subs() {
  # stdin -> stdout
  sed -E \
    -e 's#~/\.claude/skills#~/.codex/skills#g' \
    -e 's#\.claude/skills#.agents/skills#g' \
    -e 's#Claude Code / their editor#Codex / their editor#g' \
    -e 's#Claude Code against a clone#Codex against a clone#g' \
    -e 's#running `claude`#running `codex`#g' \
    -e 's#Claude using this skill#Codex using this skill#g' \
    -e 's#Running in Claude Code instead#Running in a CLI agent (e.g. Codex) instead#g' \
    -e 's#Running Claude Code inside the container#Running Codex inside the container#g' \
    -e 's#inner Claude#inner agent#g' \
    -e 's#outer Claude#outer agent#g' \
    -e 's#Inner Claude#Inner agent#g' \
    -e 's#Outer Claude#Outer agent#g' \
    -e 's#when Claude is working inside#when Codex is working inside#g' \
    -e 's#references/claude-in-container\.md#references/codex-in-container.md#g' \
    -e 's#for a specific module; setup is in#for a specific module (or run `/skills` to pick one from a menu); setup is in#' \
    -e 's#(^|[`" (,])/(nvwb-project|nvwb|setup-workshop|workshop|module-[0-9N]+)([`" .,)]|$)#\1$\2\3#g'
}

mode="${1:-write}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Build the desired DST (skills only) into $tmp/skills, then compare/install.
mkdir -p "$tmp/skills"
while IFS= read -r -d '' f; do
  rel="${f#"$SRC"/}"
  is_in "$rel" "${SKIP_FROM_SRC[@]}" && continue
  is_in "$rel" "${HAND_AUTHORED[@]}" && continue   # preserve committed hand-authored file
  dest="$tmp/skills/$rel"
  mkdir -p "$(dirname "$dest")"
  case "$f" in
    *.md) apply_subs < "$f" > "$dest" ;;
    *)    cp -a "$f" "$dest" ;;
  esac
done < <(find "$SRC" -type f -print0)

if [ "$mode" = "--check" ]; then
  # Compare generated mechanical files against what's committed (ignoring hand-authored).
  rc=0
  while IFS= read -r -d '' g; do
    rel="${g#"$tmp"/skills/}"
    if ! diff -q "$g" "$DST/$rel" >/dev/null 2>&1; then
      echo "DRIFT: $rel"; rc=1
    fi
  done < <(find "$tmp/skills" -type f -print0)
  [ "$rc" = 0 ] && echo "OK: .agents/skills mechanical files match .claude/skills"
  exit "$rc"
fi

# Install: copy generated mechanical files over DST (without touching hand-authored).
while IFS= read -r -d '' g; do
  rel="${g#"$tmp"/skills/}"
  mkdir -p "$DST/$(dirname "$rel")"
  cp -a "$g" "$DST/$rel"
done < <(find "$tmp/skills" -type f -print0)

# Remove any stale Claude-only files that may linger in DST from older runs.
for s in "${SKIP_FROM_SRC[@]}"; do rm -f "$DST/$s"; done

echo "Synced .agents/skills <- .claude/skills (hand-authored files preserved: ${#HAND_AUTHORED[@]})"
