#!/bin/bash
# Entry point for the "Claude Code" and "Codex CLI" tiles in jp_app_launcher.yaml.
#
# Why this wrapper exists: clicking a tile used to drop the learner at a bare TUI
# with no sign that this repo ships a workshop tutor. The gap was never that the
# assistant was missing — it was that nobody knew what to ask it. So instead of
# documenting the tutor somewhere else, this makes the assistant introduce itself.
#
# What it does, in order:
#   1. CLI missing (npm hiccup during postBuild) → print the install command and
#      drop to a shell rather than dying with "command not found".
#   2. Harness not authenticated yet → print the orientation card and wait for
#      Enter. The pause is the point: both TUIs can take over the screen, so
#      anything printed immediately before exec is not guaranteed to survive.
#   3. First *authenticated* launch → hand the CLI an opening prompt so the tutor
#      orients the learner in its own voice, inside the TUI where it can't be
#      wiped. This also models how to ask. Later launches start clean, so a
#      learner returning to ask a real question isn't made to sit through it.
#
# The "already oriented" marker lives in the harness config dir because those are
# the directories .project/spec.yaml persists across container rebuilds.
#
# Usage: start-assistant.sh claude|codex

set -u

HARNESS="${1:-claude}"

# Repo root, derived rather than hardcoded (.devx/bin → repo root). The tile sets
# cwd already; this makes the script correct if it's ever run from elsewhere.
# Skills only load when the CLI starts from the repo root.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 1

case "$HARNESS" in
  claude)
    CLI="claude"
    LABEL="Claude Code"
    CONFIG_DIR="$HOME/.claude"
    INSTALL_CMD="sudo npm install -g @anthropic-ai/claude-code"
    PREFIX="/"
    AUTH_STEPS="Paste an Anthropic API key at the prompt (get one at console.anthropic.com),
  or press Enter to sign in through your browser."
    AUTHED=0
    if [ -s "$CONFIG_DIR/.credentials.json" ] || [ -n "${ANTHROPIC_API_KEY:-}" ]; then
      AUTHED=1
    fi
    ;;
  codex)
    CLI="codex"
    LABEL="Codex CLI"
    CONFIG_DIR="$HOME/.codex"
    INSTALL_CMD="sudo npm install -g @openai/codex"
    PREFIX="\$"
    AUTH_STEPS="Run 'codex login' to sign in with a ChatGPT account,
  or set OPENAI_API_KEY in your environment."
    AUTHED=0
    if [ -s "$CONFIG_DIR/auth.json" ] || [ -n "${OPENAI_API_KEY:-}" ]; then
      AUTHED=1
    fi
    ;;
  *)
    echo "start-assistant.sh: unknown harness '$HARNESS' (expected claude or codex)" >&2
    exit 2
    ;;
esac

# --- colors (only when attached to a terminal) -------------------------------
if [ -t 1 ]; then
  G=$'\033[92m'; B=$'\033[1m'; D=$'\033[2m'; R=$'\033[0m'
else
  G=""; B=""; D=""; R=""
fi

RULE="────────────────────────────────────────────────────────────────────"

print_card() {
  cat <<EOF

${G}${RULE}${R}
  ${B}NVIDIA Build-an-Agent workshop${R}  ${D}·${R}  ${B}${LABEL}${R}
${G}${RULE}${R}

  This repo ships its workshop tutor as Agent Skills. It explains each
  module's concepts in the workshop's own framing, gives graduated hints
  ${B}without ever completing your exercises${R}, and helps you troubleshoot
  the environment when something breaks.

  ${G}One thing to remember${R}   ${B}${PREFIX}workshop${R}   ${D}— orientation, prerequisites, what's next${R}

  ${G}Per module${R}             ${B}${PREFIX}module-1${R} … ${B}${PREFIX}module-7${R}

  ${G}Or just describe it${R}    the right module skill loads on its own:
                          ${D}"explain the ReAct pattern"${R}
                          ${D}"I'm stuck on the reranker exercise"${R}
                          ${D}"my langgraph dev server won't start"${R}

  ${B}First, authenticate.${R}
  ${D}${AUTH_STEPS}${R}
  ${D}This is separate from your NVIDIA workshop key.${R}

${G}${RULE}${R}
EOF
}

# --- 1. CLI missing ----------------------------------------------------------
if ! command -v "$CLI" >/dev/null 2>&1; then
  cat <<EOF

  ${B}${LABEL} isn't installed.${R}

  postBuild.bash installs it, but keeps the step non-fatal so an npm hiccup
  can't break the workshop build. Install it now with:

      ${B}${INSTALL_CMD}${R}

  Then click the ${LABEL} tile again.

EOF
  exec "${SHELL:-/bin/bash}"
fi

MARKER="$CONFIG_DIR/.devx-oriented"

# --- 2. Not authenticated: show the card, hold the screen --------------------
if [ "$AUTHED" -eq 0 ]; then
  print_card
  printf '  %sPress Enter to start %s…%s ' "$D" "$LABEL" "$R"
  read -r _ || true
  echo
  exec "$CLI"
fi

# --- 3. Authenticated ---------------------------------------------------------
if [ ! -e "$MARKER" ]; then
  mkdir -p "$CONFIG_DIR" 2>/dev/null
  : > "$MARKER" 2>/dev/null || true
  exec "$CLI" "${PREFIX}workshop I just opened you from the JupyterLab launcher tile in the Build-an-Agent workshop. Give me a short orientation: what you can help me with, how to reach the per-module tutors, the kinds of questions worth bringing to you, and where to start."
fi

# Returning learner: one line, no ceremony. If the TUI takes the screen this is
# lost — that's what the Claude Code status line in .claude/settings.json covers.
printf '\n  %sworkshop tutor:%s %s%sworkshop%s to get oriented · %s%smodule-1…7%s · or just ask.\n\n' \
  "$D" "$R" "$B" "$PREFIX" "$R" "$B" "$PREFIX" "$R"
exec "$CLI"
