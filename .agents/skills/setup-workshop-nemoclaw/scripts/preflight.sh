#!/usr/bin/env bash
# preflight.sh — verify the operator contract + environment BEFORE running
# setup.sh. RUN FROM INSIDE THE SANDBOX. Read-only; safe to re-run.
#
# Exit 0  = all blocking checks pass, proceed to setup.sh
# Exit 1  = blocking gap(s); the script prints the exact operator ask for each.
#           Send those asks to the user/operator verbatim and WAIT.
set -uo pipefail

REPO="${REPO:-/sandbox/workshop-build-an-agent}"
PORT="${PORT:-8888}"
CA="/etc/openshell-tls/ca-bundle.pem"
REPO_SLUG="${REPO_SLUG:-brevdev/workshop-build-an-agent}"
BRANCH="${BRANCH:-edwli-dev}"
fail=0; warn=0

pass() { printf '  PASS  %s\n' "$1"; }
warnf() { printf '  WARN  %s\n' "$1"; warn=1; }
failf() { printf '  FAIL  %s\n' "$1"; fail=1; }
ask()  { printf '        ASK OPERATOR: %s\n' "$1"; }

echo "== setup-workshop-nemoclaw preflight (in-sandbox) =="

# 0. Are we actually inside the sandbox?
if [ "$(whoami 2>/dev/null)" = "sandbox" ] && [ -d /sandbox ]; then
  pass "running inside the sandbox (user=sandbox, /sandbox exists)"
else
  failf "this does not look like the sandbox (user=$(whoami 2>/dev/null || echo '?'))"
  ask  "you may be on the HOST — use the setup-workshop-nemoclaw-operator skill instead"
fi

# 1. Tooling + TLS bundle
command -v uv >/dev/null && pass "uv on PATH ($(uv --version 2>/dev/null | head -1))" \
  || failf "uv not on PATH — cannot install deps"
[ -f "$CA" ] && pass "proxy CA bundle at $CA" \
  || failf "proxy CA bundle missing at $CA (uv/pip TLS will fail)"

# 2. Repo present (or clonable)
if [ -d "$REPO/.git" ]; then
  pass "repo at $REPO ($(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?') branch)"
  [ "$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null)" = "$BRANCH" ] \
    || warnf "repo not on branch $BRANCH — stay on $BRANCH for the workshop"
else
  code=$(curl -sS -m 20 -o /dev/null -w '%{http_code}' \
    "https://github.com/$REPO_SLUG.git/info/refs?service=git-upload-pack" 2>/dev/null)
  if [ "$code" = "200" ]; then
    warnf "repo missing at $REPO but clone route is OPEN — run: git clone --branch $BRANCH https://github.com/$REPO_SLUG $REPO"
  else
    failf "repo missing at $REPO and github.com smart-HTTP blocked (HTTP $code)"
    ask  "add the github_git_clone policy block for $REPO_SLUG (see references/operator-contract.md), then ping me"
  fi
fi

# 3. PyPI egress (curl uses the proxy CA by default in this sandbox)
code=$(curl -sS -m 15 -o /dev/null -w '%{http_code}' https://pypi.org/simple/ 2>/dev/null)
if [ "$code" = "200" ]; then pass "pypi.org reachable (200)"; else
  failf "pypi.org blocked (HTTP ${code:-000})"
  ask  "apply policy: read-only GET pypi.org + files.pythonhosted.org (uv/python binaries). Signal: my curl to pypi.org/simple/ returns 200"
fi
code=$(curl -sS -m 15 -o /dev/null -w '%{http_code}' https://files.pythonhosted.org/ 2>/dev/null)
[ "$code" = "200" ] || { failf "files.pythonhosted.org blocked (HTTP ${code:-000})"; \
  ask "same policy block must include files.pythonhosted.org"; }

# 4. NIM endpoint (chat/embeddings/models; ranking is POST-only and needs auth,
#    so reaching /v1/models with 200 is the practical probe)
code=$(curl -sS -m 15 -o /dev/null -w '%{http_code}' https://integrate.api.nvidia.com/v1/models 2>/dev/null)
if [ "$code" = "200" ]; then pass "integrate.api.nvidia.com reachable (200)"; else
  failf "integrate.api.nvidia.com blocked (HTTP ${code:-000})"
  ask  "allow the NIM routes on integrate.api.nvidia.com incl. POST /v1/ranking (module-2 reranker)"
fi

# 5. Secrets staged
if [ -s "$REPO/secrets.env" ] && grep -q '^NVIDIA_API_KEY=' "$REPO/secrets.env" 2>/dev/null; then
  pass "secrets.env staged with NVIDIA_API_KEY (contents not read)"
else
  failf "no NVIDIA_API_KEY in $REPO/secrets.env"
  ask  "stage the key from the host via docker exec (never via chat) — command in references/operator-contract.md"
fi

# 5b. Workshop integration egress (module coverage; 2026-07-21 audit).
# Key-authenticated where possible for definitive 200s. All four blocks ship
# in the community example's policy template — a failure here means policy
# drift or a missing key, and names exactly which modules degrade.
if [ -s "$REPO/secrets.env" ]; then
  set -a; . "$REPO/secrets.env" >/dev/null 2>&1; set +a
fi
code=$(curl -sS -m 20 -o /dev/null -w '%{http_code}' -X POST https://api.tavily.com/search \
  -H 'Content-Type: application/json' \
  -d "{\"api_key\":\"${TAVILY_API_KEY:-}\",\"query\":\"ping\",\"max_results\":1}" 2>/dev/null)
if [ "$code" = "200" ]; then pass "api.tavily.com POST /search: 200 (modules 1/2/5 web search)"; else
  warnf "api.tavily.com POST /search: HTTP ${code:-000} — module-1 docgen, module-2 web_search, module-5 search degrade to no-search output"
  ask  "add the tavily_search policy block (POST /search + /extract on api.tavily.com; see operator skill policy-blocks.md) and stage TAVILY_API_KEY in secrets.env"
fi
code=$(curl -sS -m 20 -o /dev/null -w '%{http_code}' https://api.smith.langchain.com/info \
  -H "x-api-key: ${LANGSMITH_API_KEY:-}" 2>/dev/null)
if [ "$code" = "200" ]; then pass "api.smith.langchain.com /info: 200 (tracing + module 3)"; else
  warnf "api.smith.langchain.com /info: HTTP ${code:-000} — EVERY notebook spams tracing retry errors (variables.env sets LANGSMITH_TRACING=true) and module-3 tracing lessons are dark"
  ask  "add the langsmith_api policy block (all methods on api.smith.langchain.com) and stage LANGSMITH_API_KEY in secrets.env"
fi
code=$(curl -sS -m 20 -o /dev/null -w '%{http_code}' -r 0-64 \
  "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken" 2>/dev/null)
if [ "$code" = "200" ] || [ "$code" = "206" ]; then pass "tiktoken BPE host reachable (module 7)"; else
  warnf "openaipublic.blob.core.windows.net: HTTP ${code:-000} — module-7 harness_lab dies at tiktoken.get_encoding (log shows the real ProxyError only in the raised chain)"
  ask  "add the tiktoken_encodings policy block (GET /encodings/** on openaipublic.blob.core.windows.net)"
fi
if [ -n "${NVIDIA_API_KEY:-}" ]; then
  code=$(curl -sS -m 25 -o /dev/null -w '%{http_code}' -X POST \
    "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-1b-v2/reranking" \
    -H "Authorization: Bearer $NVIDIA_API_KEY" -H 'Content-Type: application/json' \
    -d '{"model":"nvidia/llama-nemotron-rerank-1b-v2","query":{"text":"ping"},"passages":[{"text":"pong"}]}' 2>/dev/null)
  if [ "$code" = "200" ]; then pass "ai.api.nvidia.com reranking: 200 (modules 2/3 retriever)"; else
    warnf "ai.api.nvidia.com reranking: HTTP ${code:-000} — NVIDIARerank (modules 2/3) fails. NOTE: the integrate.api.nvidia.com /v1/ranking rule does NOT cover llama-nemotron-rerank-1b-v2"
    ask  "add the nvidia_retrieval policy block (POST /v1/retrieval/** on ai.api.nvidia.com)"
  fi
fi

# 6. Port 8888
if curl -s -m 3 -o /dev/null "http://127.0.0.1:$PORT/"; then
  warnf "something already answers on 127.0.0.1:$PORT — start-jupyter.sh will enforce single-server"
else
  pass "port $PORT free"
fi

# 6b. PTY allocation (JupyterLab Terminal tile). The Landlock policy must
# grant rw on /dev/pts. Non-blocking: notebooks/kernels use ZMQ, not PTYs —
# but without the grant the launcher's Terminal tile pops "Launcher Error:
# Unhandled error" (server log: "OSError: out of pty devices", CPython's
# fallback AFTER the real EACCES from os.openpty() was swallowed — see
# references/sandbox-internals.md). start-jupyter.sh auto-disables the tile.
if python3 -c 'import os; os.openpty()' >/dev/null 2>&1; then
  pass "PTY allocation works — Terminal tile will function"
else
  warnf "PTY allocation denied (Landlock /dev/pts) — Terminal tile will be disabled; notebooks unaffected"
  ask  "add /dev/pts to filesystem_policy.read_write in the policy TEMPLATE — it activates at the next sandbox recreate (fs policy is boot-time; a live apply will not enable it)"
fi

# 7. Disk
avail_gb=$(df -BG /sandbox 2>/dev/null | awk 'NR==2 {gsub("G","",$4); print $4}')
[ "${avail_gb:-0}" -ge 5 ] && pass "disk free on /sandbox: ${avail_gb} GB" \
  || warnf "low disk on /sandbox: ${avail_gb:-?} GB (venv needs ~2-3 GB)"

echo
if [ "$fail" -ne 0 ]; then
  echo "VERDICT: BLOCKED — send the ASK OPERATOR lines above to the user verbatim, then wait for 'try now'."
  exit 1
fi
[ "$warn" -ne 0 ] && echo "VERDICT: OK with warnings — proceed to setup.sh." || echo "VERDICT: OK — proceed to setup.sh."
exit 0
