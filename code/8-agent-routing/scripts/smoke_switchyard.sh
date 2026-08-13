#!/bin/bash
# Maintainer canary: run before events and on any pin bump (spec §8b.6).
#
# Checks, in order:
#   1. the pinned install (delegated to install_switchyard.sh)
#   2. routes.toml validation -- the `--dry-run` equivalent. There is no
#      `switchyard-server` binary and therefore no `--dry-run` flag; the embedded
#      Rust gateway validates a config when you construct it. See
#      docs/specs/switchyard-api-notes.md § "Server install".
#   3. one live routed call through the gateway. Three hard assertions, all read from
#      data this step already fetches:
#        a. the response `model` field names the UPSTREAM target (the Routing Client
#           depends on this)
#        b. /v1/stats reports a non-empty `tiers` map -- an empty one means two targets
#           collided on one model id and the tier split silently collapsed
#           (api-notes Deviation 6)
#        c. the judge did not burn its whole verdict budget -- that means it is emitting
#           chain-of-thought, so every request silently falls through to the strong
#           target (api-notes Deviation 5)
#      (b) and (c) are the two ways this stack fails while still returning a perfectly
#      valid upstream model id, so they must exit non-zero, not warn.
#   4. one direct hosted call to the efficient target (hosted-model-id canary --
#      the retriever-EOL lesson)
#   5. drift visibility: latest published version vs the pin
#
# Every volatile string (pinned version, model ids) is read out of
# scripts/install_switchyard.sh -- THE single pin record. Nothing is hardcoded here.
#
# TEMPORARY (remove in Task 6): `routes.toml.answers` does not exist yet, so step 2
# falls back to a probe config this script writes into a temp dir -- the same config
# the Task 1 verification spike used. Once Task 6 lands routes.toml.answers, delete
# the fallback branch and this note.
#
# Requires NVIDIA_API_KEY in the environment:
#   set -a; source secrets.env; set +a

set -euo pipefail

cd "$(dirname "$0")/.."
LAB_DIR="$(pwd)"

if [ -z "${NVIDIA_API_KEY:-}" ]; then
    echo "ERROR: NVIDIA_API_KEY is not set." >&2
    echo "       Run:  set -a; source secrets.env; set +a" >&2
    exit 1
fi

# Read a pinned value out of THE pin record. Fails loudly if the block is renamed,
# so the two files can never drift apart silently.
pin() {
    local value
    value="$(grep -m1 "^$1=" scripts/install_switchyard.sh | cut -d'"' -f2 || true)"
    if [ -z "$value" ]; then
        echo "ERROR: could not read $1 from scripts/install_switchyard.sh (the pin record)." >&2
        exit 1
    fi
    printf '%s\n' "$value"
}

PINNED="$(pin SWITCHYARD_VERSION)"
MODEL_EFFICIENT="$(pin MODEL_EFFICIENT)"
MODEL_CAPABLE="$(pin MODEL_CAPABLE)"
MODEL_JUDGE="$(pin MODEL_JUDGE)"

echo "==> [1/5] Pinned install"
bash scripts/install_switchyard.sh
PY="$(bash scripts/install_switchyard.sh --print-python)"

TMPD="$(mktemp -d)"
trap 'rm -rf "$TMPD"' EXIT

CONFIG="${LAB_DIR}/routes.toml.answers"
if [ -f "$CONFIG" ]; then
    echo "==> [2/5] Validating routes.toml.answers"
else
    CONFIG="${TMPD}/routes-probe.toml"
    echo "==> [2/5] routes.toml.answers not present yet (Task 6) — validating the Task 1 probe config"
    # Unquoted heredoc: the three model ids come from the pin record above.
    cat > "$CONFIG" <<TOML
schema_version = 1

[llm_clients.nvidia]
format = "openai_chat"
base_url = "https://integrate.api.nvidia.com/v1"
api_key_env = "NVIDIA_API_KEY"

# The judge needs its own model id: two targets sharing an id on one llm_client are
# silently deduped and routing collapses to the strong tier. And it must not "think" --
# chain-of-thought eats the whole structured-output budget and the classifier falls
# through to strong on every request. (api-notes Deviations 5 and 6.)
[targets.judge]
id = "${MODEL_JUDGE}"
llm_client = "nvidia"
extra_body = { chat_template_kwargs = { thinking = false } }

[targets.weak]
id = "${MODEL_EFFICIENT}"
llm_client = "nvidia"

[targets.strong]
id = "${MODEL_CAPABLE}"
llm_client = "nvidia"

[routes.switchyard]
id = "switchyard"
type = "llm_classifier"
mode = "capability"
classifier_target = "judge"
strong_target = "strong"
weak_target = "weak"
base_threshold = 0.5
max_output_tokens = 4096
TOML
fi

"$PY" - "$CONFIG" <<'PY'
import sys
from switchyard_rust.server import Server
Server(sys.argv[1], port=0).close()          # binds an ephemeral port, then releases it
print("✅ config validates:", sys.argv[1])
PY

echo "==> [3/5] Live routed call through the embedded gateway"
"$PY" - "$CONFIG" <<'PY'
import json, sys, tomllib, urllib.request
from switchyard_rust.server import Server

# The judge's verdict budget, so the "judge burned its budget" assertion below stays
# correct if a routes.toml sets a non-default max_output_tokens (upstream default: 4096).
with open(sys.argv[1], "rb") as handle:
    routes = (tomllib.load(handle).get("routes") or {})
budget = max([int(route.get("max_output_tokens", 4096))
              for route in routes.values()
              if route.get("type") == "llm_classifier"] or [4096])

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
server = Server(sys.argv[1], port=0)
try:
    req = urllib.request.Request(
        server.base_url + "/v1/chat/completions",
        data=json.dumps({"model": "switchyard",
                         "messages": [{"role": "user", "content": "What is 2 + 2?"}],
                         "max_tokens": 16}).encode(),
        headers={"Content-Type": "application/json"})
    with opener.open(req, timeout=300) as response:
        body = json.load(response)
    upstream = body.get("model")
    if not upstream or upstream == "switchyard":
        raise SystemExit(
            f"❌ gateway did not report an upstream model id (got {upstream!r}).\n"
            "   The Routing Client's attribution depends on this -- see "
            "docs/specs/switchyard-api-notes.md § Gateway attribution.")
    with opener.open(server.base_url + "/v1/stats", timeout=30) as response:
        stats = json.load(response)

    classifier = stats.get("classifier") or {}
    overhead = (stats.get("routing_overhead") or {}).get("avg_ms")
    judge = (classifier.get("total_tokens") or {}).get("completion")
    tiers = stats.get("tiers") or {}

    print(f"✅ routed 'switchyard' -> {upstream}")
    print(f"   router tax: {overhead} ms avg, {judge} judge completion tokens")
    print(f"   tiers exercised: {sorted(tiers)}")

    # Both remaining failure modes still return a valid upstream model id, so neither
    # is caught by the check above. They must fail the canary, not merely warn --
    # after Task 6 this step gates routes.toml.answers itself.
    #
    # Most specific diagnosis first: a judge that exhausted its budget explains an empty
    # `tiers` map, so reporting the collapse instead would send the reader down the wrong
    # trail. A fall-through request is attributed to no tier at all, which is why the
    # `tiers` check below catches BOTH modes -- it is the deterministic backstop.
    if judge is not None and judge >= budget:
        raise SystemExit(
            f"❌ judge burned its whole {budget}-token verdict budget ({judge} completion "
            "tokens)\n   -- it is emitting chain-of-thought instead of the required JSON "
            "verdict, so the\n   classifier silently falls through to the strong target on "
            "EVERY request.\n"
            "   Set extra_body = { chat_template_kwargs = { thinking = false } } on the\n"
            "   judge target, or raise max_output_tokens --\n"
            "   see docs/specs/switchyard-api-notes.md § Deviations #5.")
    if not tiers:
        raise SystemExit(
            "❌ /v1/stats reports no tiers -- the weak/strong split collapsed and every\n"
            "   request is being served without a routing decision.\n"
            "   Most likely: two targets share a model id on one llm_client, so one was\n"
            "   silently dropped. Give the judge its own model id, or put it on a second\n"
            "   llm_client -- see docs/specs/switchyard-api-notes.md § Deviations #6.\n"
            "   Otherwise check the server's stderr for a `judge verdict unavailable` line.")
finally:
    server.close()
PY

echo "==> [4/5] Hosted efficient target reachable"
"$PY" - "$MODEL_EFFICIENT" <<'PY'
import json, os, sys, urllib.request
req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=json.dumps({"model": sys.argv[1],
                     "messages": [{"role": "user", "content": "Reply OK"}],
                     "max_tokens": 8}).encode(),
    headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}",
             "Content-Type": "application/json"})
print("✅ hosted efficient target:", json.load(urllib.request.urlopen(req))["model"])
PY

echo "==> [5/5] Drift vs the pin"
LATEST="$("$PY" -m pip index versions nemo-switchyard 2>/dev/null | sed -n 's/^nemo-switchyard (\(.*\))$/\1/p' || true)"
if [ -z "$LATEST" ]; then
    echo "   (could not query PyPI for the latest version — skipping drift check)"
elif [ "$LATEST" != "$PINNED" ]; then
    echo "⚠️  upstream is at ${LATEST}, this module is pinned to ${PINNED}."
    echo "   Bump via the runbook in code/8-agent-routing/README.md — do NOT bump ad hoc."
else
    echo "   pinned ${PINNED} == latest ${LATEST}"
fi

echo "✅ smoke complete"
