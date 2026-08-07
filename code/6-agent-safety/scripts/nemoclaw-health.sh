#!/bin/bash
# NemoClaw control-plane health check — Module 6.
#
# A fast, READ-ONLY status probe for the four moving parts the Module 6
# hands-on exercises depend on:
#
#   1. socat tunnel     (127.0.0.1:8080 -> Docker bridge; the CLI's link to the gateway)
#   2. nemoclaw CLI     (install integrity — a partial install throws "Cannot find module")
#   3. NemoClaw gateway (reachable — `nemoclaw status` can list sandboxes)
#   4. NemoClaw sandbox (my-assistant reports `Phase: Ready`)
#
# It mutates nothing and never touches the network. Run it whenever an
# exercise in `using_nemoclaw.md` or `evaluating_safety.md` fails, to see
# which layer is down and exactly what to run to bring it back.
#
#   bash code/6-agent-safety/scripts/nemoclaw-health.sh
#
# Notes on correctness:
#   * The gateway is verified through `nemoclaw`/`openshell` (the host CLIs) —
#     NOT `openclaw`, which in a NemoClaw deployment runs *inside* the sandbox
#     ("Agent: OpenClaw ...") and is not a host binary.
#   * Readiness uses the SAME signal the workshop code keys on
#     (`nemoclaw <sandbox> status` -> `Phase: Ready`, per
#     nemoclaw_wrapper._check_sandbox_running), and — like that wrapper — strips
#     ANSI color codes first, since the CLI renders `Phase:` dimmed
#     (`\x1b[2mPhase:\x1b[0m Ready`) and a raw grep would miss it.

set -u

SANDBOX_NAME="${NEMOCLAW_SANDBOX_NAME:-my-assistant}"
RECOVER_CMD="bash code/6-agent-safety/scripts/install-nemoclaw.sh"

# Streamlit/JupyterLab terminals can hand us a stripped PATH; add the install
# locations the wrappers probe so binary discovery matches the app's.
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:$PATH"

ok()   { printf '  [ OK ]  %s\n' "$1"; }
fail() { printf '  [FAIL]  %s\n' "$1"; }
warn() { printf '  [WARN]  %s\n' "$1"; }
info() { printf '          %s\n' "$1"; }

# Strip ANSI/SGR escape sequences so plain-text greps match colorized CLI output.
strip_ansi() { sed -r 's/\x1b\[[0-9;]*[a-zA-Z]//g'; }

# Track the first layer that is down so the summary can point at the root cause.
FIRST_BROKEN=""
note_broken() { [ -z "$FIRST_BROKEN" ] && FIRST_BROKEN="$1"; }

echo
echo "=============================================================="
echo " NemoClaw control-plane health check"
echo "=============================================================="

# ---------------------------------------------------------------------------
# 1. socat tunnel — the CLI dials 127.0.0.1:8080; socat forwards it to the
#    gateway on the Docker bridge. Without it, every nemoclaw call times out.
# ---------------------------------------------------------------------------
echo
echo "1. socat tunnel (127.0.0.1:8080 -> gateway)"
if pgrep -f "socat TCP-LISTEN:8080" >/dev/null 2>&1; then
    ok "tunnel process is running"
else
    fail "no socat tunnel on 127.0.0.1:8080"
    info "The installer starts this for you; recovery below restores it."
    note_broken "tunnel"
fi

# ---------------------------------------------------------------------------
# 2. nemoclaw CLI integrity — a partial/corrupt install still resolves on
#    PATH but throws "Cannot find module '.../dist/lib/agent/runtime'" on
#    every invocation. Detect that explicitly so the fix is obvious. Checked
#    before the gateway/sandbox probes below, which use this CLI.
# ---------------------------------------------------------------------------
echo
echo "2. nemoclaw CLI"
if ! command -v nemoclaw >/dev/null 2>&1; then
    fail "nemoclaw CLI not found on PATH"
    info "Install/repair with: $RECOVER_CMD"
    note_broken "nemoclaw-cli"
    NEMOCLAW_USABLE=0
else
    nemoclaw_out="$(timeout 20 nemoclaw --version 2>&1)"
    if printf '%s' "$nemoclaw_out" | grep -q "Cannot find module"; then
        fail "nemoclaw is installed but its files are incomplete (corrupt install)"
        info "Signature: \"Cannot find module '.../dist/lib/agent/runtime'\""
        info "Repair by reinstalling: $RECOVER_CMD"
        note_broken "nemoclaw-corrupt"
        NEMOCLAW_USABLE=0
    else
        ok "nemoclaw CLI responds"
        NEMOCLAW_USABLE=1
    fi
fi

# ---------------------------------------------------------------------------
# 3. NemoClaw gateway — reachable if `nemoclaw status` can query it and list
#    sandboxes (this is what the exercises talk to, via the tunnel above).
# ---------------------------------------------------------------------------
echo
echo "3. NemoClaw gateway (OpenShell)"
if [ "${NEMOCLAW_USABLE:-0}" -ne 1 ]; then
    warn "skipped — fix the nemoclaw CLI (step 2) first"
    note_broken "gateway"
else
    gw_raw="$(timeout 20 nemoclaw status 2>&1)"; gw_rc=$?
    gw_out="$(printf '%s' "$gw_raw" | strip_ansi)"
    if [ "$gw_rc" -eq 0 ] && printf '%s' "$gw_out" | grep -qiE 'sandbox'; then
        ok "gateway reachable (nemoclaw listed sandboxes)"
    else
        fail "gateway not reachable"
        info "The gateway container or the socat tunnel (step 1) is likely down."
        info "Restore with: $RECOVER_CMD"
        note_broken "gateway"
    fi
fi

# ---------------------------------------------------------------------------
# 4. Sandbox readiness — the exact signal the workshop code keys on. Strip
#    ANSI first (the CLI dims the `Phase:` label). Skipped if the CLI itself
#    is unusable (would just re-print the module error).
# ---------------------------------------------------------------------------
echo
echo "4. NemoClaw sandbox ($SANDBOX_NAME)"
if [ "${NEMOCLAW_USABLE:-0}" -ne 1 ]; then
    warn "skipped — fix the nemoclaw CLI (step 2) first"
    note_broken "sandbox"
else
    status_out="$(timeout 30 nemoclaw "$SANDBOX_NAME" status 2>&1 | strip_ansi)"
    if printf '%s' "$status_out" | grep -qiE '^[[:space:]]*Phase:[[:space:]]*Ready\b'; then
        ok "sandbox is up and Phase: Ready"
    else
        fail "sandbox is not Ready"
        snippet="$(printf '%s' "$status_out" | grep -iE 'Phase:' | head -1 | sed 's/^[[:space:]]*//')"
        [ -z "$snippet" ] && snippet="$(printf '%s' "$status_out" | grep -vE '^[[:space:]]*$' | head -1 | sed 's/^[[:space:]]*//')"
        [ -n "$snippet" ] && info "status said: ${snippet}"
        info "Onboard/restore it with: $RECOVER_CMD"
        note_broken "sandbox"
    fi
fi

# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
echo
echo "=============================================================="
if [ -z "$FIRST_BROKEN" ]; then
    echo " READY — all four layers are up."
    echo " You can run every exercise in using_nemoclaw.md end to end."
else
    echo " NOT READY — the live sandbox is unavailable."
    echo
    echo " To bring the control plane back up, run:"
    echo
    echo "     $RECOVER_CMD"
    echo
    echo " It is idempotent: if parts are already healthy it just restores"
    echo " the tunnel; if the install is corrupt or the sandbox is missing it"
    echo " reinstalls and re-onboards. Then re-run this health check."
    echo
    echo " Can't bring it up right now? You are NOT blocked. The Python"
    echo " sidekicks and the safety-evaluation capstone in evaluating_safety.md"
    echo " run fully offline against the built-in leaky mock agent — only the"
    echo " live-sandbox walkthroughs (Exercises 1-4) need the control plane."
fi
echo "=============================================================="
echo
