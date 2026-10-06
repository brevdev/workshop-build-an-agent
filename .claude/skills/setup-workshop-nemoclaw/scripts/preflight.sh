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
BRANCH="${BRANCH:-main}"
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
#    so reaching /v1/models with 200 is the practical probe).
# ⚠️ Probe with python3, NOT curl: the community example's `nvidia` policy
# block allowlists only hermes/python binaries — an exec'd curl is DENIED at
# NET:OPEN (`binary '/usr/bin/curl' not allowed in policy 'nvidia'`) and
# returns 000 even when the route is open, wrongly BLOCKING preflight.
code=$(python3 -c "import urllib.request,ssl;print(urllib.request.urlopen('https://integrate.api.nvidia.com/v1/models',context=ssl.create_default_context(cafile='$CA'),timeout=15).status)" 2>/dev/null)
if [ "$code" = "200" ]; then pass "integrate.api.nvidia.com reachable (200)"; else
  failf "integrate.api.nvidia.com blocked (python probe: ${code:-no-response})"
  ask  "allow chat/embedding routes on integrate.api.nvidia.com for the Python binaries"
fi

# 5. Secrets — NON-BLOCKING by design.
# Keys can be entered later in Secrets Manager. Notebook setup reloads saved keys;
# existing agent processes must restart to load changes.
if [ -s "$REPO/secrets.env" ] && grep -q '^NVIDIA_API_KEY=' "$REPO/secrets.env" 2>/dev/null; then
  pass "secrets.env carries NVIDIA_API_KEY (contents not read)"
else
  warnf "no NVIDIA_API_KEY in $REPO/secrets.env — add it in Secrets Manager before model calls."
fi

# 5b. Reachability only: capability and credential checks run in Workshop Health
# after setup. Keep keys out of subprocess arguments and diagnostics.
python3 - "$CA" <<'PY_CHECK'
import ssl, sys, urllib.error, urllib.request
context = ssl.create_default_context(cafile=sys.argv[1])
warning = False
for name, url, data in (
    ("Tavily search", "https://api.tavily.com/search", b"{}"),
    ("Tavily MCP", "https://mcp.tavily.com/mcp/", b"{}"),
    ("Optional LangSmith", "https://api.smith.langchain.com/info", None),
    ("Token encodings", "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken", None),
):
    try:
        request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, context=context, timeout=15) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    except OSError:
        status = None
    if status is None or status == 403:
        warning = True
        print(f"  WARN  {name}: check the network, proxy CA and Python egress rules.")
    else:
        print(f"  PASS  {name}: reached HTTP {status}; this does not test credentials or model capability.")
sys.exit(1 if warning else 0)
PY_CHECK
[ "$?" -eq 0 ] || warn=1
# The frontend downloads through Node, whose egress is checked separately.
if command -v node >/dev/null 2>&1; then
  code=$(node -e 'const h=require("https");const r=h.get("https://registry.npmjs.org/react",x=>{console.log(x.statusCode);x.destroy();});r.on("error",()=>console.log("000"));r.setTimeout(20000,()=>{console.log("000");r.destroy();});' 2>/dev/null | tail -1)
  if [ "$code" = "200" ]; then pass "registry.npmjs.org reachable via node (module-5 client)"; else
    warnf "registry.npmjs.org: HTTP ${code:-000} — the client frontend needs its build dependencies"
    ask "check the npm_install policy block for /usr/local/bin/node"
  fi
fi
printf '  INFO  After setup, open Workshop Utilities → Workshop Health and run endpoint checks.\n'

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
  ask  "run the operator skill's Phase 1b token-window-guarded restart — /dev/pts ships in the Phase 1 apply, but fs policy is boot-time (a live apply will not enable it)"
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
