#!/bin/bash
# Routing Client tile entry point (jp_app_launcher.yaml). Usage: start_client.sh $PORT
#
# The tile is `type: local-server`, so the JupyterLab launcher waits for something
# to bind $PORT -- if nothing ever does, the tile spins forever (the Module 5 client
# lesson). Every path below therefore ends in a listening socket: the real client
# when it can run, a page explaining the one fix when it cannot.
#
# The client imports the learner's routing_lab.py, so it must run on an interpreter
# that CAN — which is not a fixed path. Inside the Workbench container the ambient
# `python3` is a bare system 3.10 while JupyterLab's own 3.12 (reachable as
# `python3.12`) carries the whole workshop stack; on other machines it is the
# Module 8 venv install_switchyard.sh built. So candidates are PROBED, never
# assumed: first one that can import the lab's dependencies wins, preferring one
# that also has the Switchyard SDK. Override with ROUTING_CLIENT_PYTHON=/path.
#
# ROUTING_LAB_MODULE=routing_lab.answers renders the completed lab instead of the
# learner's copy -- the demo/screenshot path, never the default.

set -uo pipefail

PORT="${1:?usage: start_client.sh <port>}"
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1          # routing_client/

VENV_PY="${SWITCHYARD_VENV:-$HOME/.local/share/module8-switchyard-venv}/bin/python"

# find_spec, not import: the probe must stay cheap (a tile launch, not a test run)
# and must not execute package code just to ask whether it exists.
has_module() {   # has_module <python> <module>
    "$1" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$2') else 1)" \
        >/dev/null 2>&1
}

runnable() {     # a candidate that exists: absolute paths by -x, bare names by PATH
    case "$1" in
        /*) [ -x "$1" ] ;;
        *)  command -v "$1" >/dev/null 2>&1 ;;
    esac
}

PY="${ROUTING_CLIENT_PYTHON:-}"
if [ -z "$PY" ]; then
    LAB_PY=""            # best interpreter that can run the lab (but not the SDK)
    ANY_PY=""            # best interpreter full stop — the setup-page fallback
    for cand in "$VENV_PY" python3.12 python3 python; do
        runnable "$cand" || continue
        [ -n "$ANY_PY" ] || ANY_PY="$cand"
        if has_module "$cand" langchain_nvidia_ai_endpoints; then
            if has_module "$cand" switchyard; then PY="$cand"; break; fi
            [ -n "$LAB_PY" ] || LAB_PY="$cand"
        fi
    done
    # No lab-capable interpreter at all: fall back to anything that can at least
    # serve the UI — the server then shows lab_error with the install hint, which
    # beats a static setup page because it updates live once the deps arrive.
    PY="${PY:-$LAB_PY}"
    PY="${PY:-$ANY_PY}"
fi

setup_page() {   # bind $PORT with guidance instead of leaving the launcher hanging
    "${PY:-python3}" - "$PORT" "$1" <<'PYEOF'
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
port, problem = int(sys.argv[1]), sys.argv[2]
PAGE = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Routing Client - setup required</title><style>
:root{{color-scheme:dark}} body{{margin:0;min-height:100vh;display:flex;align-items:center;
justify-content:center;background:#0e1116;color:#e6edf3;padding:24px;
font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
.card{{max-width:620px;padding:36px 40px;background:#161b22;border:1px solid #2a3441;border-radius:14px}}
h1{{margin:0 0 6px;font-size:21px;color:#76b900}} p{{color:#8b98a9;line-height:1.6}}
pre{{background:#0e1116;border:1px solid #2a3441;border-radius:8px;padding:12px 14px;
color:#c6d0da;font-size:13px;white-space:pre-wrap}}</style></head><body><div class="card">
<h1>Routing Client &mdash; setup required</h1><p>{problem}</p>
<p>Open a <strong>Terminal</strong> in JupyterLab, run this, then reopen the tile:</p>
<pre>cd /project/code/8-agent-routing
python3 -m pip install fastapi uvicorn</pre>
<p>The exercises do not depend on this client: <code>python3 routing_lab.py --exercise N</code>
verifies every one of them from the terminal.</p></div></body></html>"""
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = PAGE.encode()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
ThreadingHTTPServer.allow_reuse_address = True
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
PYEOF
}

if [ -z "$PY" ]; then
    echo "[start_client] no python3 on PATH" >&2
    setup_page "No python3 interpreter was found on this machine's PATH."
    exit 0
fi

# Two dependencies, installed on first launch. Pinning lives with the rest of the
# module's pins, not inline here.
if ! "$PY" -c 'import fastapi, uvicorn' 2>/dev/null; then
    echo "[start_client] installing fastapi + uvicorn into $PY …"
    "$PY" -m pip install --quiet fastapi uvicorn
fi

if ! "$PY" -c 'import fastapi, uvicorn' 2>/dev/null; then
    echo "[start_client] fastapi/uvicorn still missing — serving setup page on :$PORT" >&2
    setup_page "The client's two dependencies (fastapi, uvicorn) could not be installed."
    exit 0
fi

echo "[start_client] serving the Routing Client on http://127.0.0.1:$PORT (python: $PY · lab: ${ROUTING_LAB_MODULE:-routing_lab})"
exec "$PY" -m uvicorn server:app --host 127.0.0.1 --port "$PORT"
