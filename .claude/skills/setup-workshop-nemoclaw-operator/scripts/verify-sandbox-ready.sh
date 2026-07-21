#!/usr/bin/env bash
# verify-sandbox-ready.sh — READ-ONLY host-side readiness probe for the
# Build-an-Agent workshop sandbox. Run on the sandbox HOST (outside).
#
# Checks the operator contract the in-sandbox agent depends on:
#   container up · policy live (pypi / NIM) · repo present · secrets staged ·
#   (if a forward is up) Jupyter answering.
# Egress probes run via `openshell sandbox exec` (Landlock-real).
# Exit 0 = ready to tell the sandbox agent "try now"; exit 1 = gaps printed.
set -uo pipefail

SANDBOX="${SANDBOX:-hermes-direct}"
REPO_IN_SANDBOX="${REPO_IN_SANDBOX:-/sandbox/workshop-build-an-agent}"
PORT="${PORT:-8888}"
fail=0

pass() { printf '  PASS  %s\n' "$1"; }
warnf() { printf '  WARN  %s\n' "$1"; }
failf() { printf '  FAIL  %s\n' "$1"; fail=1; }

sx() { # single-line command under real sandbox enforcement
  openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc "$1" 2>/dev/null
}

echo "== workshop sandbox readiness ($SANDBOX) =="

# 0. Host-side tooling
command -v openshell >/dev/null || { failf "openshell CLI not on PATH — is this the sandbox host?"; echo "VERDICT: BLOCKED"; exit 1; }
command -v docker >/dev/null    || { failf "docker not on PATH — is this the sandbox host?"; echo "VERDICT: BLOCKED"; exit 1; }

# 1. Container
C=$(docker ps --format '{{.Names}}' | grep "openshell-$SANDBOX" | head -1)
if [ -n "$C" ]; then pass "container up: $C"; else
  failf "no running container matching openshell-$SANDBOX (docker ps)"; echo "VERDICT: BLOCKED"; exit 1
fi

# 2. Policy revision (informational) + egress probes under enforcement
openshell policy get "$SANDBOX" 2>/dev/null | sed -n '1,3p' | sed 's/^/        /'
code=$(sx 'curl -s -m 15 -o /dev/null -w "%{http_code}" https://pypi.org/simple/')
[ "$code" = "200" ] && pass "pypi.org from inside: 200" \
  || failf "pypi.org from inside: HTTP ${code:-000} — apply the pypi_install policy block (references/policy-blocks.md)"
code=$(sx 'curl -s -m 15 -o /dev/null -w "%{http_code}" https://files.pythonhosted.org/')
[ "$code" = "200" ] || failf "files.pythonhosted.org from inside: HTTP ${code:-000}"
# curl is NOT in the nvidia block's binaries — an exec'd curl probe returns
# 000 even when the route is open (false negative). Probe with python
# (allowed in the block) + the proxy CA.
code=$(sx 'python3 -c "import urllib.request,ssl;print(urllib.request.urlopen(\"https://integrate.api.nvidia.com/v1/models\",context=ssl.create_default_context(cafile=\"/etc/openshell-tls/ca-bundle.pem\"),timeout=15).status)"')
[ "$code" = "200" ] && pass "integrate.api.nvidia.com from inside: 200" \
  || failf "integrate.api.nvidia.com from inside: HTTP ${code:-000} — NIM routes missing"
if [ "$(sx 'python3 -c "import os; os.openpty()" >/dev/null 2>&1 && echo ok')" = "ok" ]; then
  pass "PTY allocation from inside: ok (Terminal tile will work)"
else
  warnf "PTY allocation denied — Terminal tile auto-hidden until /dev/pts is rw in filesystem_policy (references/policy-blocks.md); re-run start-jupyter.sh after granting"
fi

# 3. Repo + secrets (filesystem peeks — docker exec is fine for these)
if docker exec "$C" test -d "$REPO_IN_SANDBOX/.git" 2>/dev/null; then
  pass "repo present at $REPO_IN_SANDBOX"
else
  warnf "repo NOT at $REPO_IN_SANDBOX — sandbox agent will clone (needs github_git_clone block)"
  code=$(sx 'curl -s -m 20 -o /dev/null -w "%{http_code}" "https://github.com/brevdev/workshop-build-an-agent.git/info/refs?service=git-upload-pack"')
  [ "$code" = "200" ] && pass "github.com clone route from inside: 200" \
    || failf "github.com clone route from inside: HTTP ${code:-000} — add github_git_clone block"
fi
if docker exec "$C" sh -c "test -s $REPO_IN_SANDBOX/secrets.env && grep -q '^NVIDIA_API_KEY=' $REPO_IN_SANDBOX/secrets.env" 2>/dev/null; then
  pass "secrets.env staged with NVIDIA_API_KEY"
else
  failf "secrets.env missing/empty at $REPO_IN_SANDBOX — run scripts/stage-nvidia-key.sh"
fi

# 4. Forward + Jupyter (only meaningful after the sandbox agent launched it)
if pgrep -f "forward service $SANDBOX" >/dev/null 2>&1; then
  code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/lab" 2>/dev/null)
  if [ "$code" = "302" ] || [ "$code" = "200" ]; then
    pass "forward up + Jupyter answering on host 127.0.0.1:$PORT (HTTP $code)"
    docker exec "$C" cat /sandbox/workshop-url.txt 2>/dev/null | sed 's/^/        URL: /' || true
  else
    warnf "forward process found but host :$PORT gives HTTP ${code:-000} — is Jupyter up inside yet?"
  fi
else
  warnf "no 'openshell forward service $SANDBOX' running — start it once the agent reports Jupyter is up"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "VERDICT: BLOCKED — fix the FAIL lines (policy: references/policy-blocks.md; secrets: scripts/stage-nvidia-key.sh)."
  exit 1
fi
echo "VERDICT: READY — tell the in-sandbox agent to run the setup-workshop-nemoclaw skill ('try now')."
exit 0
