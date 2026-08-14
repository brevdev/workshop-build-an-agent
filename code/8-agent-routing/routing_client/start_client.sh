#!/bin/bash
# Routing Client tile entry point (jp_app_launcher.yaml). Usage: start_client.sh $PORT
#
# The tile is `type: local-server`, so the JupyterLab launcher waits for something
# to bind $PORT -- if nothing ever does, the tile spins forever (the Module 5 client
# lesson). Every path below therefore ends in a listening socket: the real client
# when it can run, a page explaining the one fix when it cannot.
#
# The client imports the learner's routing_lab.py, so it must run on the same
# interpreter the lab does: the Module 8 venv if install_switchyard.sh already made
# one (that is where the Switchyard SDK lives), otherwise the ambient python3.
# Override with ROUTING_CLIENT_PYTHON=/path/to/python.
#
# ROUTING_LAB_MODULE=routing_lab.answers renders the completed lab instead of the
# learner's copy -- the demo/screenshot path, never the default.

set -uo pipefail

PORT="${1:?usage: start_client.sh <port>}"
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1          # routing_client/

VENV_PY="${SWITCHYARD_VENV:-$HOME/.local/share/module8-switchyard-venv}/bin/python"
PY="${ROUTING_CLIENT_PYTHON:-}"
if [ -z "$PY" ]; then
    if [ -x "$VENV_PY" ]; then PY="$VENV_PY"; else PY="$(command -v python3 || true)"; fi
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

echo "[start_client] serving the Routing Client on http://127.0.0.1:$PORT (lab: ${ROUTING_LAB_MODULE:-routing_lab})"
exec "$PY" -m uvicorn server:app --host 127.0.0.1 --port "$PORT"
