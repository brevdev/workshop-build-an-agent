#!/bin/bash
# Maintainer canary: run before events and on any pin bump (spec §8b.6).
#
# Checks, in order:
#   1. the pinned install (delegated to install_switchyard.sh)
#   2. routes.toml validation -- the `--dry-run` equivalent. There is no
#      `switchyard-server` binary and therefore no `--dry-run` flag; the embedded
#      Rust gateway validates a config when you construct it. See
#      docs/specs/switchyard-api-notes.md § "Server install".
#   3. one live routed call through the gateway, asserting the response `model`
#      field names the UPSTREAM target (the Routing Client depends on this)
#   4. one direct hosted call to the efficient target (hosted-model-id canary --
#      the retriever-EOL lesson)
#   5. drift visibility: latest published version vs the pin
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
    cat > "$CONFIG" <<'TOML'
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
id = "nvidia/nemotron-3-nano-30b-a3b"
llm_client = "nvidia"
extra_body = { chat_template_kwargs = { thinking = false } }

[targets.weak]
id = "nvidia/nemotron-3.5-lightning-30b-a3b"
llm_client = "nvidia"

[targets.strong]
id = "nvidia/nemotron-3-super-120b-a12b"
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
import json, sys, urllib.request
from switchyard_rust.server import Server

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
    overhead = (stats.get("routing_overhead") or {}).get("avg_ms")
    judge = (stats.get("classifier") or {}).get("total_tokens", {}).get("completion")
    print(f"✅ routed 'switchyard' -> {upstream}")
    print(f"   router tax: {overhead} ms avg, {judge} judge completion tokens")
    if judge is not None and judge >= 4096:
        print("⚠️  judge burned its whole verdict budget -- it is probably emitting "
              "chain-of-thought. Check extra_body chat_template_kwargs.thinking = false "
              "(api-notes Deviation 5); routing will silently fall through to strong.")
finally:
    server.close()
PY

echo "==> [4/5] Hosted efficient target reachable"
"$PY" - <<'PY'
import json, os, urllib.request
req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=json.dumps({"model": "nvidia/nemotron-3.5-lightning-30b-a3b",
                     "messages": [{"role": "user", "content": "Reply OK"}],
                     "max_tokens": 8}).encode(),
    headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}",
             "Content-Type": "application/json"})
print("✅ hosted efficient target:", json.load(urllib.request.urlopen(req))["model"])
PY

echo "==> [5/5] Drift vs the pin"
LATEST="$("$PY" -m pip index versions nemo-switchyard 2>/dev/null | sed -n 's/^nemo-switchyard (\(.*\))$/\1/p' || true)"
PINNED="$(grep -m1 '^SWITCHYARD_VERSION=' scripts/install_switchyard.sh | cut -d'"' -f2)"
if [ -z "$LATEST" ]; then
    echo "   (could not query PyPI for the latest version — skipping drift check)"
elif [ "$LATEST" != "$PINNED" ]; then
    echo "⚠️  upstream is at ${LATEST}, this module is pinned to ${PINNED}."
    echo "   Bump via the runbook in code/8-agent-routing/README.md — do NOT bump ad hoc."
else
    echo "   pinned ${PINNED} == latest ${LATEST}"
fi

echo "✅ smoke complete"
