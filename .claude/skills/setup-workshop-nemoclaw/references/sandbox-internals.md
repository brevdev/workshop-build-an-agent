# Sandbox internals — root causes, diagnostics & manual fixes

Reference for when a script step fails and you need to fix it by hand, or to
understand *why* each step exists. All of this was discovered iteratively in a
live session (Jul 2026); the scripts encode the final working answers. Errors
below are quoted verbatim so you can match symptoms.

## TLS / CA bundle

- uv and pip do **not** use the system trust store. TLS terminates at the
  OpenShell L7 proxy, which presents its own CA.
- Correct bundle: `SSL_CERT_FILE=/etc/openshell-tls/ca-bundle.pem` (also set
  `PIP_CERT` to the same path for the pip fallback). This is curl's actual
  default CAfile in the sandbox (`curl -v` shows `CAfile: /etc/openshell-tls/ca-bundle.pem`).
- `/etc/ssl/certs/ca-certificates.crt` is the *wrong* bundle here — it lacks
  the proxy CA. Symptom: uv fails with
  `invalid peer certificate: UnknownIssuer`; curl forced onto that bundle
  fails with `SSL certificate problem: self-signed certificate in certificate
  chain`. uv's `--native-tls` / `--system-certs` do NOT help.
- Plain `curl` (no override) works because it already uses the right default —
  so "curl works but uv fails" is the signature of this exact problem.

## Netlink / seccomp — the kernel-startup blocker

Symptom: Jupyter opens, but every kernel dies (`Kernel died before replying to
kernel_info`, `AsyncIOLoopKernelRestarter: restarting kernel (1/5)…` … `(5/5)`)
and every voila tile hangs at "Running…". Server log shows
`jupyter_client/localinterfaces.py:58: UserWarning: Unexpected error
discovering local network interfaces: [Errno 1] Operation not permitted` and
voila `--debug` shows the decisive line:
`Operation not permitted (src/ip_resolver.cpp:542)`.

Root cause chain:
1. The in-container OpenShell supervisor (`/opt/openshell/bin/openshell-sandbox`,
   Rust seccompiler; `/proc/self/status` shows `Seccomp: 2`,
   `Seccomp_filters: 4`) denies `socket(AF_NETLINK, …)` → EPERM. `AF_INET` and
   `AF_UNIX` are fine. (Contrast check that proves it's seccomp, not
   capabilities: `socket(AF_INET, SOCK_RAW)` fails with a *different* errno,
   EPROTONOSUPPORT.)
2. `getifaddrs()` uses AF_NETLINK under the hood → returns -1 EPERM;
   `if_nameindex()` likewise.
3. ipykernel binds ZMQ sockets at startup and libzmq enumerates interfaces at
   bind time **regardless of transport** — switching kernels to IPC transport
   (`c.KernelManager.transport = "ipc"`) does NOT avoid it (verified: IPC
   kernels still die at `ip_resolver.cpp:542`). An **empty** interface list is
   also fatal: ZMQ asserts `ifa != NULL (src/ip_resolver.cpp:543)`.

Fix (in-sandbox LD_PRELOAD shim — operator-pre-approved, since there is no
host-side knob: the filter is compiled into the supervisor, not the Docker
seccomp JSON, not the policy schema):
- `templates/netlink-stub.c` overrides four libc functions:
  `getifaddrs()` → returns a **non-empty** one-entry list (`lo`, 127.0.0.1,
  `IFF_UP|IFF_LOOPBACK|IFF_RUNNING`); `freeifaddrs()`; `if_nameindex()` →
  `[(1,"lo")]`; `if_freenameindex()`. Non-empty is mandatory (see assert
  above; a first attempt returning `*ifap = NULL` failed).
- No system compiler exists (`gcc`/`cc`/`clang`/`tcc` absent; npm 403-blocked;
  distutils gone). Build with the **ziglang pip wheel**:
  ```bash
  "$VENV/bin/python" -m ziglang cc -shared -fPIC -O2 -o netlink-stub.so netlink-stub.c
  ```
- Scope: `LD_PRELOAD` only on the Jupyter process tree (exported in
  start-jupyter.sh right before launch, inherited by kernels/voila/streamlit
  children). Never exported session-wide.
- It does NOT weaken egress — it only stubs interface *enumeration*; all
  socket I/O still passes the sandbox's Landlock/proxy enforcement.
- NEVER work around this with `docker exec` — that also escapes Landlock.
- ⚠️ The shim must be on the **server process itself**, not just kernels: the
  server's own ZMQ client sockets call `getifaddrs` too. If kernels have the
  shim but the server doesn't (stale server — see single-server discipline),
  kernels start and are never tracked ("starting" forever, no
  `ip_resolver` error in the log — that absence is the tell).
- Leftover from the failed IPC experiment: if
  `/sandbox/.jupyter/jupyter_server_config.py` sets `transport = "ipc"`,
  remove it (setup.sh does). `JUPYTER_RUNTIME_DIR=/tmp/jrt` is kept — short
  socket/connection-file paths, harmless.

## PTY / the Terminal tile — Landlock, not seccomp

Clicking Terminal in the launcher pops "Launcher Error: Unhandled error";
`POST /api/terminals` returns 500 and the server log traceback ends with

    File ".../pty.py", line 67, in _open_terminal
        raise OSError('out of pty devices')

That message is a red herring. CPython's `pty.openpty()` first calls
`os.openpty()` and **swallows its exception**, then falls back to the legacy
BSD `/dev/ptyXY` names — which don't exist on modern Linux — and raises
"out of pty devices". Probe the real failure directly:

    python3 -c "import os; os.openpty()"                     # PermissionError: [Errno 13]
    python3 -c "import os; os.open('/dev/ptmx', os.O_RDWR)"  # PermissionError: '/dev/ptmx'

EACCES (not EPERM) plus `ls /dev/pts` → "Permission denied" = **Landlock
filesystem denial**. Unlike the netlink block this is NOT compiled-in
seccomp — there IS an operator knob: the sandbox policy's
`filesystem_policy.read_write` simply lacks `/dev/pts`. (`/dev/ptmx` is a
symlink to `pts/ptmx`, so the one grant covers master and slaves.)

Fix (operator side): apply `- /dev/pts` under `filesystem_policy.read_write`
with the rest of the workshop policy (operator skill Phase 1), then run that
skill's Phase 1b recreate-from-live so a fresh boot picks it up. A live `openshell policy
set` does NOT activate fs grants: the supervisor parses `filesystem_policy`
once at container boot and builds every per-spawn Landlock ruleset from that
boot-time copy (verified: after a live apply added /dev/pts, new spawns
still requested the old rw set — the supervisor's `Landlock ruleset built`
log kept showing the old rw count; network rules hot-reload, fs rules
don't). There is no sandbox restart command, and raw `docker restart` hits
the stale-bootstrap-JWT crash loop.

Until granted, `start-jupyter.sh` probes `os.openpty()` and launches with
`--ServerApp.terminals_enabled=False` so the Terminal tile disappears
entirely instead of popping the error dialog (verified: installed
jupyter_server_terminals 0.5.4 honors `ServerApp.terminals_enabled`). No
LD_PRELOAD shim can help here — a PTY is a kernel object; you cannot stub it
in userspace the way `getifaddrs` was stubbed.

## Launcher tiles: paths, duplication, the Secrets-Manager tile type saga

**Paths.** The workshop's `jp_app_launcher.yaml` hardcodes `/project/...`
(the AI Workbench mount). `/project` doesn't exist here and can't be
symlinked (`ln -s` → `Permission denied`; no root). Fix: write a rewritten
copy (`/project` → `$REPO`) into `$REPO/.launcher-config/` and set
`JUPYTER_APP_LAUNCHER_PATH` to that dir. `templates/jp_app_launcher.yaml` is
that file, pre-rewritten for `/sandbox/workshop-build-an-agent`; setup.sh
re-sed's if `$REPO` differs.

**Duplicate tiles (22 instead of 11).** The `jupyter-app-launcher` extension
merges configs from BOTH `os.getcwd()` AND `JUPYTER_APP_LAUNCHER_PATH`
(source: its `handlers.py`; it also scans `<jupyter_data_path>/jupyter_app_launcher/`).
Signature: a second set of tiles with letter icons (1A, 2A, … SM, SA, DA, NC)
because the duplicate set's `/project/...` icon paths are broken. Fix, all
three layers (belt & braces): move the repo-root `jp_app_launcher.yaml` to
`/sandbox/original-root-jp_app_launcher.yaml.bak`, delete
`$REPO/.ipynb_checkpoints/jp_app_launcher-checkpoint.yaml`, and launch from
cwd `/sandbox` (not the repo) with `--ServerApp.root_dir=$REPO`.

**Secrets Manager (master) tile — why it must be `jupyterlab-commands`.**
Three designs were tried; two fail:
1. `type: notebook-voila` (upstream default): the backend factory
   `Popen(["voila", …])`s a per-tile voila and fronts it through
   jupyter-server-proxy. Two failures: (a) bare `voila` must be on the
   server's PATH (hence venv-first PATH at launch — the factory does
   `FileNotFoundError: 'voila'` otherwise); (b) even then, browser GETs go
   through jupyter-server-proxy's *buffered* handler, which `await`s the
   **entire** body — voila streams chunked output and holds the connection
   open for the widget kernel, so the proxy times out: log shows
   `405 HEAD /proxy/absolute/<port>/` then `599 GET /proxy/absolute/<port>/`
   (Tornado 599 = client timeout). Downgrading jupyter-server-proxy
   4.5.0→4.1.2 does NOT help (same single buffered fetch).
2. `type: url` with `source: /voila/render/<nb>`: uses voila's in-process
   server extension (no subprocess, no proxy) — renders fine server-side, BUT
   a cold IFrame carries no token and the session cookie doesn't reliably
   travel: `HTTP 302 → Location: /login?next=%2Fvoila%2Frender%2F…` → the
   spinner never finishes. Also: any `type: url` tile MUST carry `args: {}`
   or the frontend crashes (`Cannot read properties of undefined (reading
   'createNewWindow')`).
3. ✅ `type: jupyterlab-commands` with `source: [{label, id: docmanager:open,
   args: {path: code/secrets_management/secrets_management_master.ipynb,
   factory: "Voila Preview"}}]` — executes the same authenticated in-app
   command path the in-lesson buttons use (`@voila-dashboards/jupyterlab-preview`).
   This is what the template ships.

**Client tiles.** "Simple Agents Client" / "NemoClaw Client" are
`type: local-server` running `streamlit run … --server.port $PORT`; without
`streamlit` installed the child dies instantly and the tile "loads" forever
(the launcher polls the port forever). Install `streamlit` + `langgraph-sdk`
(in requirements-sandbox.txt). Launcher-spawned children inherit the server's
env — venv-first PATH and LD_PRELOAD both matter here. Note: Simple Agents
Client renders but needs a separate LangGraph backend (module exercise) to be
interactive; Deep Agents Client (`demo/start_client.sh`) deliberately serves
a "setup required" page until its backend exists.

## Bridge labextension (window.jupyterapp)

The in-lesson HTML buttons (e.g. `.devx/*/secrets.md`) call `openVoila(path)`
from `.devx/_static/js/jupyter-link.js`, which expects
`window.parent.jupyterapp` to be the JupyterLab `app` object and logs
`JupyterLab app is not available on window.jupyterapp` without it. That global
is injected by AI Workbench's DevX layer — absent in plain JupyterLab.

- Fix: tiny federated labextension `devx-jupyterapp-bridge` (v1.0.0) whose
  plugin `activate(app)` sets `window.jupyterapp = app`.
- npm registry is 403-blocked, so it was hand-crafted by mirroring a prebuilt
  extension's structure: a Module Federation `remoteEntry.js` (~2 KB container
  implementing `init(sharedScope)` + `get('./extension')`) plus a
  `package.json` with the `jupyterlab: {"_build": {"load":
  "static/remoteEntry.js", "extension": "./extension"}}` markers. Shipped as
  `assets/devx-jupyterapp-bridge.tar.gz`; extract into
  `$VENV/share/jupyter/labextensions/` — no build step.
- Verify: `jupyter labextension list` shows `devx-jupyterapp-bridge v1.0.0
  enabled OK`, and the lab page's `federated_extensions` config includes it.
- The docsify lesson pages also load CDN assets (jsdelivr/unpkg) — the
  **user's browser** fetches those, not the sandbox, so the sandbox 403 on
  those hosts is irrelevant.

## %pip install cells

`code/secrets_management/secrets_management_*.ipynb` (8 files: `_1`–`_7` +
`_master`) begin with a cell running
`%pip install -r ../../requirements.txt > /dev/null` followed by
`load_dotenv("../../variables.env")` / `load_dotenv("../../secrets.env")`.
voila executes every cell before rendering; requirements.txt pulls
torch/unsloth/cudf → hang. (The uv venv has no `pip` module at all, so the
magic can only fail.) `scripts/neutralize_pip_cells.py` replaces just the
`%pip` line with a marker comment, preserving the `load_dotenv` lines.
Idempotent — skips already-neutralized cells; never touches
`.ipynb_checkpoints`.

## Single-server discipline

Multiple JupyterLab servers piled up on port 8888 during iteration (4 at one
point). The stale one keeps the bind; relaunches "succeed" but the OLD server
keeps answering — this caused vanished tiles AND the
shim-on-kernels-but-not-server failure above. Rules, encoded in
start-jupyter.sh:
- `kill -9` stale `jupyter-lab` **and** `voila` / `ipykernel` children —
  Jupyter traps SIGTERM.
- Confirm 8888 is actually free before launching.
- After launch, verify the serving pid's env:
  `tr '\0' '\n' < /proc/<pid>/environ | grep LD_PRELOAD`.
- Reuse the existing token (`--ServerApp.token`) when restarting so the
  user's saved URL and the operator's forward keep working.

## Inbound path

Agent processes run in an inner network namespace; a server bound even to
0.0.0.0 is unreachable at the container IP (connection refused). The only
inbound path is `openshell forward service <sandbox> --target-port 8888
--local 8888` on the host (gRPC tunnel to the sandbox inner loopback), then an
SSH/tsh `-L` forward from the laptop. Verified end-to-end HTTP 200. Details +
Teleport troubleshooting: operator skill.

## Verification without a browser

- Tiles: `curl -X POST 'http://127.0.0.1:8888/jupyterlab-app-launcher?token=…' -d '{"method":"init_launcher"}'`
  → JSON with 11 tiles. GET → 405 Method Not Allowed;
  `/jupyter_app_launcher/get_config` → 404. Both are normal, not breakage.
- voila: `curl -m 20 'http://127.0.0.1:8888/voila/render/code/secrets_management/secrets_management_master.ipynb?token=…'`
  → 200 with `voila_process(6, 6)` / `window.voila_finish()` in the body.
- Proxied voila (`/proxy/absolute/<port>/`) streams chunked and holds the
  connection → curl "hangs" at timeout and `-I` (HEAD) → 405. Red herrings.
- Kernel: `POST /api/kernels` then poll — `execution_state` must leave
  `"starting"`. Stuck at starting = shim problem.
- The token is masked in tool output by the gateway's secret redaction. Read
  it from `$JUPYTER_RUNTIME_DIR/jpserver-<pid>.json` (or `jupyter lab list`)
  and write the URL to `/sandbox/workshop-url.txt` instead of echoing it.

## Model routing / policy

- `ChatNVIDIA` / `NVIDIAEmbeddings` (chat, completions, embeddings) go to
  `integrate.api.nvidia.com` (allowlisted). `build.nvidia.com` is NOT needed
  (notebook prose only).
- ⚠️ **`NVIDIARerank` for `nvidia/llama-nemotron-rerank-1b-v2` (modules 2/3)
  does NOT use `integrate.api.nvidia.com/v1/ranking`** — it POSTs
  `ai.api.nvidia.com/v1/retrieval/<model>/reranking`. The old `/v1/ranking`
  rule only covers earlier rerank models; the `nvidia_retrieval` policy block
  (POST `/v1/retrieval/**` on `ai.api.nvidia.com`) is what modules 2/3 need.
  Verified live 2026-07-21 from the SDK's own error URL.
- Blocked calls are diagnosed on the HOST: `docker logs <container> | grep
  DENIED` names the process path and rule. Ask the operator (see
  operator-contract.md).

## Integration egress (Tavily / LangSmith / tiktoken / ragas)

Four additional routes the workshop content actually exercises (exact YAML
for every one lives in the operator skill's policy-blocks.md; preflight.sh
probes them):

- `api.tavily.com` `POST /search|/extract` — `tavily-python` REST (module-1
  docgen tool, module-2 local MCP server, module-5 search). Without it the
  agents still complete but write no-search reports (silently degraded).
- `api.smith.langchain.com` (all methods) — `variables.env` sets
  `LANGSMITH_TRACING=true` which EVERY notebook loads in cell 1, so without
  this route every LangChain call spams `Failed to multipart ingest runs`
  retries (700+ denials/90min observed); module-3 tracing lessons are dark.
  Key: `LANGSMITH_API_KEY` in secrets.env.
- `openaipublic.blob.core.windows.net` `GET /encodings/**` — tiktoken
  downloads its BPE file at first `get_encoding()`; module-7 harness_lab dies
  there otherwise. (CPython chains the real ProxyError under a misleading
  tiktoken traceback.)
- `t.explodinggradients.com` — ragas usage telemetry. Do NOT open it;
  start-jupyter.sh exports `RAGAS_DO_NOT_TRACK=true` instead.

ragas import gotcha: ragas 0.4.x hard-imports
`langchain_community.chat_models.vertexai`, removed in langchain-community
1.x, so a bare `import ragas` raises ModuleNotFoundError even though ragas IS
installed. The module-3 evaluate notebooks ship a stub-module workaround cell
— run it before importing ragas (verified working).

## Module-2 web_search: remote MCP vs local server

The shipped `rag_agent.py` PART 2A uses Tavily's REMOTE MCP via
`npx -y mcp-remote https://mcp.tavily.com/mcp/...`. In this sandbox that is a
dead end twice over: npx must download `mcp-remote` from `registry.npmjs.org`
(blocked; and npm's retry backoff makes agent tool calls hang for minutes —
this is what times out module-3's rag eval), and `mcp.tavily.com` is not
allowlisted. **Use PART 2B (commented out in the same file): the local MCP
server.** Its deps (`mcp`, `starlette`, `uvicorn`, `tavily`) are all in the
sandbox pins; run `uvicorn mcp_server:app --port 8000` in module-2's dir and
swap the `web_search` tool to the SSE config. Only `api.tavily.com` egress is
needed. Verified end-to-end 2026-07-21.

## Module coverage on this sandbox (audited 2026-07-21)

- **Fully working (CPU + workshop policy blocks):** module 1 (both notebooks),
  module 2 (RAG + local-MCP web search; `langgraph dev` serving needs the
  langgraph-cli pin), module 3 (generate + eval; rag-eval needs the module-2
  local-MCP swap to avoid npx hangs), module-4 `bash_agent` + `01_synthetic`
  (data-designer pin), module 6 safety pipeline (92.5% on the hardened
  policy), module 7 (tiktoken route + pins), secrets manager, all 11 tiles,
  all three client UIs.
- **GPU-only by design (do NOT install torch/unsloth/cudf — hangs, wasted
  egress):** module-4 `02_grpo_training` + `03_run_agent`; module-7's
  optional cudf exercise degrades gracefully.
- **Not available in-sandbox:** module-6 NemoClaw/OpenClaw CLI demos (Node
  CLIs absent; installer needs `www.nvidia.com` + npm egress), module-5
  Docker sandbox backend + Deep Agents client build (no Docker daemon; npm
  blocked — the client serves its setup page as designed).

## Environment quirks

- pip is absent inside the uv venv — use `uv pip …` or `importlib.metadata`
  for package queries, not `pip show`.
- duckdb 1.5.4 (and 1.1.3) abort on import in this sandbox
  (`duckdb::InternalException` → SIGABRT) — and `data_designer.essentials`
  imports duckdb, so the crash kills every module-3/4 synthetic-data kernel
  (`nbclient DeadKernelError`). Pin `duckdb==1.3.2` (verified importable);
  do not bump it without re-testing `import duckdb` in-sandbox.
- Even with 1.3.2, `duckdb.connect()` probes `/sys/fs/cgroup/{memory,cpu}.max`
  and raises `IOException: Permission denied` unless the filesystem policy
  grants `/sys/fs/cgroup` read-only (no config bypass exists — setting
  `memory_limit` still probes `cpu.max`; verified on 1.2.2/1.3.2). The
  operator applies the grant to the sandbox's LIVE policy — the deployment
  recipe's `policy.yaml` template stays stock (the operator skill's
  policy-blocks.md documents the grant); like all `filesystem_policy`
  entries it activates at sandbox RECREATE, not live apply. Until then
  modules 3/4 SDG cells raise that IOException.
- joblib warns and falls back to serial mode (sandbox blocks semaphores) —
  benign.
- Background waits are clamped (e.g. 180 s) and sessions have tool-iteration
  caps — run installs/servers as background processes with watch patterns
  (`"is running at"`), and write large artifacts incrementally.
- Stay on git branch `edwli-dev`; do not `nvwb switch-branch` or switch to main.
- Key pinned versions proven working: CPython 3.13.5, jupyterlab 4.6.1,
  jupyter-app-launcher 0.3.2, voila 0.5.12, jupyter-server-proxy 4.5.0,
  streamlit 1.59.2, ziglang 0.16.0.
