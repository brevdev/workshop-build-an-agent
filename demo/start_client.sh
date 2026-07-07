#!/bin/bash
# Resilient launcher for the Deep Agents Client (Module 5 demo).
#
# The JupyterLab App Launcher tile runs this with the proxy port as $1. The
# tile is `type: local-server`, so the launcher waits for a server to bind that
# port — if nothing ever binds it, the whole launcher hangs.
#
# The demo has two manual prerequisites (see
# .devx/5-deep-agents/experience_deep_agent.md): the backend running, and
# `npm install` in this directory. If a learner clicks the tile before doing
# them, `npm run build` fails (no node_modules), `npm run preview` never starts,
# the port never binds, and the launcher spins forever.
#
# This wrapper guarantees the port ALWAYS binds quickly: when the frontend is
# ready it serves the real app; otherwise it serves a clear "setup required"
# page instead of hanging. It installs nothing — the manual setup stays a
# deliberate Module 5 step.

set -u

PORT="${1:?usage: start_client.sh <port>}"
DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DEMO_DIR" || exit 1

# Serve a static "setup required" page on $PORT and block, so the launcher shows
# guidance instead of an infinite spinner. Binds immediately (pure stdlib).
serve_setup_page() {
    local headline="$1"
    python3 - "$PORT" "$headline" <<'PYEOF'
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

port = int(sys.argv[1])
headline = sys.argv[2] if len(sys.argv) > 2 else "Setup required"

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Deep Agents Client - setup required</title>
<style>
  :root { color-scheme: dark; }
  body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
         background:#0c0c0c; color:#e8e8e8;
         font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; padding:24px; }
  .card { max-width:640px; padding:40px 44px; background:#151515; border:1px solid #2a2a2a;
          border-radius:14px; box-shadow:0 10px 40px rgba(0,0,0,.5); }
  h1 { margin:0 0 6px; font-size:22px; color:#76b900; }
  p.sub { margin:0 0 24px; color:#a8a8a8; font-size:15px; }
  ol { margin:0; padding-left:22px; line-height:1.7; }
  li { margin-bottom:14px; }
  .term { display:block; background:#0c0c0c; border:1px solid #2a2a2a; border-radius:8px;
          padding:12px 14px; margin-top:6px; white-space:pre-wrap; color:#c6c6c6;
          font-family:"JetBrains Mono",ui-monospace,Menlo,monospace; font-size:13px; }
  code { background:#0c0c0c; border:1px solid #2a2a2a; border-radius:6px; padding:2px 7px;
         font-family:"JetBrains Mono",ui-monospace,Menlo,monospace; font-size:13px; color:#8fcb2b; }
  .note { margin-top:26px; padding-top:18px; border-top:1px solid #2a2a2a;
          color:#8f8f8f; font-size:13px; }
</style></head>
<body><div class="card">
  <h1>Deep Agents Client &mdash; setup required</h1>
  <p class="sub">__HEADLINE__</p>
  <p>Open a <strong>Terminal</strong> in JupyterLab, run these one-time steps, then reopen this tile:</p>
  <ol>
    <li><strong>Start the backend</strong> (first run creates its virtual env):
      <span class="term">cd /project/demo/backend
python3.12 -m venv .venv &amp;&amp; source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000</span>
    </li>
    <li><strong>Install the frontend</strong> (in a second terminal):
      <span class="term">cd /project/demo &amp;&amp; npm install</span>
    </li>
    <li><strong>Reopen the &ldquo;Deep Agents Client&rdquo; tile</strong> from the Launcher.</li>
  </ol>
  <p class="note">You're seeing this page (instead of a spinning Launcher) because the client
  isn't built yet. Full walkthrough: <code>.devx/5-deep-agents/experience_deep_agent.md</code>.</p>
</div></body></html>"""

PAGE = PAGE.replace("__HEADLINE__", headline)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # keep the launcher log quiet

ThreadingHTTPServer.allow_reuse_address = True
ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
PYEOF
}

# 1. Frontend deps missing → can't build or preview. Guide, don't hang.
if [ ! -d node_modules ]; then
    echo "[start_client] node_modules missing — serving setup page on :$PORT"
    serve_setup_page "Frontend dependencies aren't installed yet (run 'npm install' in /project/demo)."
    exit 0
fi

# 2. Deps present → build. If the build fails, show guidance rather than letting
#    the preview server never start (the failure mode that hangs the launcher).
echo "[start_client] building frontend…"
if ! npm run build; then
    echo "[start_client] build failed — serving setup page on :$PORT"
    serve_setup_page "The frontend build failed. Re-run 'npm install' in /project/demo, then reopen this tile."
    exit 0
fi

# 3. Ready — serve the real app. This binds $PORT.
echo "[start_client] starting preview on :$PORT"
exec npm run preview -- --port "$PORT"
