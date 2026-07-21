---
name: setup-workshop-nemoclaw
description: >-
  Set up the NVIDIA "Build an Agent" DevX workshop as a working JupyterLab
  environment from INSIDE a locked-down OpenShell/NemoClaw sandbox, and hand
  the user the token URL + access commands. Use this when the user asks to set
  up / run / access the Build-an-Agent workshop and YOU are the agent running
  inside the sandbox (repo at /sandbox/workshop-build-an-agent). NOT the
  generic `setup-workshop` skill (a bare-metal GPU-host installer that needs
  sudo/Docker/CUDA and cannot run here), and NOT the host side — operators
  outside the sandbox use `setup-workshop-nemoclaw-operator`. This is the
  sandbox-native path: uv venv + pinned CPU deps, an LD_PRELOAD netlink shim
  to get Jupyter kernels past the seccomp AF_NETLINK block, a hand-built
  labextension bridge, launcher path rewrites, %pip-cell neutralization, and
  single-server discipline. Modules 1-3 (CPU) work end-to-end; modules 4 & 6
  (GPU: torch/unsloth/cudf) do not run here by design.
disable-model-invocation: false
user-invocable: true
---

# setup-workshop-nemoclaw (in-sandbox side)

Sets up the NVIDIA **Build an Agent** workshop as an accessible JupyterLab
instance inside an OpenShell/NemoClaw sandbox, then hands the user the
port-forward + SSH commands and the token URL to open it in their browser.

This is one half of a two-skill pair:

| Skill | Runs | Does |
|---|---|---|
| `setup-workshop-nemoclaw-operator` | on the sandbox **host** (outside) | egress policy, secrets staging, port-forward, lifecycle |
| **this skill** | **inside** the sandbox | venv + deps, netlink shim, launcher/bridge fixes, Jupyter launch, URL hand-off |

## Which side am I on?

Run the checks before doing anything. **Inside the sandbox** (use this skill):
`whoami` → `sandbox`, `/sandbox/` exists, `docker`/`sudo` are *not found*, and
egress 403s come from the OpenShell proxy. **On the host** (use the operator
skill instead): `docker ps` shows an `openshell-<sandbox>-…` container and the
`openshell` CLI is on PATH.

## When to use this skill

- User wants to run / access / go through the **Build an Agent workshop** from
  this sandbox. The repo lives (or will be cloned) at
  `/sandbox/workshop-build-an-agent`, branch `edwli-dev` — stay on it.
- Do **NOT** use the generic `setup-workshop` skill here — it is a bare-metal
  installer (`nvwb` + Docker + CUDA + sudo) for a GPU host. It fails in the
  sandbox by design, not by bug.

## Operator prerequisites (the handoff contract)

Two things must be true before setup can succeed, and only the operator
(outside the sandbox) can make them true. Verify them with
`scripts/preflight.sh`; if missing, send the operator the exact asks from
`references/operator-contract.md` and **stop until they confirm**:

1. **Egress policy** allows: `GET pypi.org` + `files.pythonhosted.org`
   (installs), `POST /v1/ranking` on `integrate.api.nvidia.com` (module-2
   reranker; chat/embeddings/models routes are typically allowlisted already),
   and — only if the repo is not yet cloned — git smart-HTTP on `github.com`
   scoped to the workshop repo.
2. **NVIDIA key staged** at `/sandbox/workshop-build-an-agent/secrets.env` as
   `NVIDIA_API_KEY=...` (notebooks `load_dotenv()` it themselves). Never
   accept the key through chat; the operator writes it via `docker exec`.

Optional third item — **`/dev/pts` read-write in `filesystem_policy`** — is
needed only for the launcher's Terminal tile (terminado → `pty.fork`).
Setup does NOT block on it: `start-jupyter.sh` probes `os.openpty()` and
launches with terminals disabled when denied. The grant only takes effect at
a sandbox **recreate** (the supervisor parses filesystem policy at container
boot; a live policy apply won't activate it, even for new processes) — after
a recreate that includes it, setup enables terminals automatically.

There is **no operator knob for the netlink/seccomp block** — it is compiled
into the in-container OpenShell supervisor (Rust seccompiler), not the Docker
profile. You fix it *inside* the sandbox with the LD_PRELOAD shim below; this
was operator-pre-approved as the sanctioned fallback. Never dodge seccomp via
`docker exec` — that also escapes Landlock egress enforcement. FORBIDDEN.

## Fast path (idempotent scripts)

`SKILL_DIR` is wherever this skill lives — resolve it, don't assume. Known
locations: the repo checkout (`/sandbox/workshop-build-an-agent/.claude/skills/setup-workshop-nemoclaw`)
or the agent skill library (`/sandbox/.hermes-data/skills/**/setup-workshop-nemoclaw`).

```bash
SKILL_DIR=$(dirname "$(find /sandbox -maxdepth 6 -path '*/setup-workshop-nemoclaw/SKILL.md' 2>/dev/null | head -1)")
bash "$SKILL_DIR/scripts/preflight.sh"      # verifies the operator contract + environment; prints exact asks if not met
bash "$SKILL_DIR/scripts/setup.sh"          # venv+deps, shim, bridge, launcher, %pip neutralize
bash "$SKILL_DIR/scripts/start-jupyter.sh"  # ONE server on 127.0.0.1:8888, prints + saves token URL
cat /sandbox/workshop-url.txt               # http://127.0.0.1:8888/lab?token=...
```

All three scripts are idempotent and verify before acting. If a step fails,
read the matching section of `references/sandbox-internals.md` for the root
cause and manual commands.

## What the scripts do (and why) — the hard-won details

Do NOT skip or reorder these. Each fixes a specific sandbox failure discovered
the hard way (full rationale + diagnostics in `references/sandbox-internals.md`).

1. **TLS / CA bundle.** uv and pip do **not** use the system trust store, and
   TLS terminates at the OpenShell L7 proxy. You MUST export
   `SSL_CERT_FILE=/etc/openshell-tls/ca-bundle.pem` (and `PIP_CERT` = same).
   ⚠️ `/etc/ssl/certs/ca-certificates.crt` is WRONG here — it lacks the proxy
   CA and breaks uv with `invalid peer certificate: UnknownIssuer`
   (`--native-tls` / `--system-certs` do not help).

2. **venv + pinned CPU deps.** `uv venv $REPO/.venv`; install the exact pinned
   set in `templates/requirements-sandbox.txt`. It includes the packages the
   repo's `requirements.txt` needs for the UI that early attempts missed:
   `jupyter-app-launcher` (zero tiles without it), `voila`, `jupyterlab-git`,
   `streamlit` + `langgraph-sdk` (client tiles), and `ziglang` (shim compiler).
   **Never** install torch/unsloth/cudf — modules 4 & 6 need a GPU this
   sandbox doesn't have, and installing them hangs voila.

3. **Netlink LD_PRELOAD shim** (`templates/netlink-stub.c`). The sandbox
   seccomp filter denies `socket(AF_NETLINK,…)` → EPERM, so `getifaddrs()`
   fails; ipykernel calls it at ZMQ bind **regardless of transport** (IPC does
   not avoid it), and an *empty* interface list trips a ZMQ assert
   (`ip_resolver.cpp:543`) → every kernel dies, voila hangs at "Running…".
   The shim stubs `getifaddrs`/`if_nameindex` to return a one-entry
   `lo`/127.0.0.1 list (non-empty is mandatory). Build with
   **`python -m ziglang cc`** (no system gcc; npm is 403-blocked). Preload it
   **only on the Jupyter process tree**, never session-wide.

4. **Bridge labextension** (`assets/devx-jupyterapp-bridge.tar.gz`). The
   in-lesson buttons call `openVoila()` → `window.parent.jupyterapp`, which
   only AI Workbench's DevX layer normally injects. npm being 403-blocked,
   this is a hand-crafted federated labextension (Module Federation
   `remoteEntry.js`, ~2 KB) whose plugin sets `window.jupyterapp = app`.
   Extract into `$VENV/share/jupyter/labextensions/` — no build step.

5. **Launcher config + anti-duplication** (`templates/jp_app_launcher.yaml`,
   11 tiles: 7 modules + Secrets Manager + Simple Agents/Deep Agents/NemoClaw
   clients). The workshop YAML hardcodes `/project/...` (a Workbench mount
   that doesn't exist here; symlinking `/project` fails — no root). The
   template rewrites paths to the repo; it goes in `$REPO/.launcher-config/`
   with `JUPYTER_APP_LAUNCHER_PATH` pointing at it. The extension merges
   configs from **both** cwd AND that path, so ALSO move the repo-root
   `jp_app_launcher.yaml` aside (to `/sandbox/original-root-jp_app_launcher.yaml.bak`),
   delete any stale `.ipynb_checkpoints/jp_app_launcher-checkpoint.yaml`, and
   launch from cwd `/sandbox` — or you get **22 duplicate tiles** (the extra
   set shows letter icons like 1A/2A/…). The **Secrets Manager tile MUST be
   `type: jupyterlab-commands`** invoking `docmanager:open` with
   `factory: "Voila Preview"` — the authenticated in-app path the per-module
   buttons use. `type: notebook-voila` deadlocks behind jupyter-server-proxy
   (HTTP 599); a raw `type: url` → `/voila/render/...` iframe carries no auth
   token → 302 → login → hangs at "Running…".

6. **Neutralize %pip cells** (`scripts/neutralize_pip_cells.py`). Cell 1 of
   the 8 `code/secrets_management/secrets_management_*.ipynb` notebooks runs
   `%pip install -r ../../requirements.txt` (pulls torch etc. → hangs voila;
   the uv venv has no pip anyway). The script comments out only that line and
   preserves the `load_dotenv` calls. Idempotent.

7. **Single-server discipline** (`scripts/start-jupyter.sh`). Keep exactly
   **one** JupyterLab server on 8888. Stale servers steal the port bind — the
   relaunched (shim-carrying) server never takes over, tiles vanish, and the
   shim "mysteriously" stops working. Jupyter traps SIGTERM, so the script
   `kill -9`s stale `jupyter-lab`/`voila`/`ipykernel`, confirms the port is
   free, launches with the full env (`SSL_CERT_FILE`,
   `JUPYTER_APP_LAUNCHER_PATH`, venv-first `PATH` so spawned `voila`/
   `streamlit` resolve, `JUPYTER_RUNTIME_DIR=/tmp/jrt`, `LD_PRELOAD=<shim>`)
   from cwd `/sandbox` with `--ServerApp.root_dir=$REPO --ip 127.0.0.1
   --port 8888 --no-browser --ServerApp.allow_remote_access=False`, then
   **verifies the running server's `/proc/<pid>/environ` actually contains
   `LD_PRELOAD`**. It reuses the previous token when one exists so the user's
   saved URL stays valid across restarts.

8. **Workshop skills → agent skill library** (`setup.sh`, final step). The
   NemoClaw harness only scans its own library
   (`/sandbox/.hermes-data/skills/`) — repo-local `.claude/skills` are
   invisible to it, so without this step a resident agent asked about the
   workshop denies knowing any workshop skills even after a successful setup.
   `setup.sh` copies every workshop skill (modules 1–7, `workshop`, `nvwb`,
   `nvwb-project`, and this skill itself) into the library. They appear in
   `hermes skills list` as `local`/`enabled` immediately, and new agent
   sessions pick them up automatically; a session already in flight may need
   a fresh session to see them. Excluded on purpose:
   `setup-workshop-nemoclaw-operator` (host-side) and `setup-workshop`
   (bare-metal GPU installer).

## Report back to the user (the skill's real output)

The Jupyter token is masked by the gateway's secret redaction, so the URL is
saved to `/sandbox/workshop-url.txt` — point the user there rather than pasting
the token. Once `start-jupyter.sh` succeeds, send the user/operator:

> JupyterLab is up (one server, `127.0.0.1:8888`, kernels verified).
> To reach it: **(1)** on the sandbox host, run
> `openshell forward service <sandbox> --target-port 8888 --local 8888`
> (foreground — leave it open); **(2)** from your laptop,
> `ssh -N -L 8888:localhost:8888 <user>@<host>` (Teleport:
> `tsh ssh -N -L 8888:localhost:8888 <user>@<node-name>` — node name from
> `tsh ls`; `-N` is SILENT when it works); **(3)** open the token URL from
> `/sandbox/workshop-url.txt` (readable on the host via
> `docker exec <container> cat /sandbox/workshop-url.txt`).

Agent processes live in an inner network namespace — a server bound even to
0.0.0.0 is unreachable at the container IP. The gRPC forward + SSH hop is the
only inbound path. Details live in the operator skill.

## Verification

- `$VENV/bin/jupyter lab list` shows exactly one server on `127.0.0.1:8888`,
  and `tr '\0' '\n' < /proc/<server-pid>/environ | grep LD_PRELOAD` shows the shim.
- `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8888/lab` → `302`
  (auth redirect = alive); with the token appended → `200`.
- Tile check without a browser: `curl -X POST http://127.0.0.1:8888/jupyterlab-app-launcher?token=… -d '{"method":"init_launcher"}'`
  → 11 tiles. (GET on that route → 405; `/jupyter_app_launcher/get_config` → 404 — both expected.)
- Skill propagation: `hermes skills list` shows `module-1`…`module-7`,
  `workshop`, and `setup-workshop-nemoclaw` as `local`/`enabled`.
- Terminal tile (only when `/dev/pts` is granted): POST `/api/terminals`
  with the token → 200 (spawns a shell; DELETE `/api/terminals/<name>`
  to clean up).
- In the browser: 11 tiles, no duplicates; module lesson pages load; the
  Secrets Manager tile and in-lesson secrets buttons open Voila Previews (not
  a "Running…" hang); kernels start; a module-2 rerank call returns 200.

## Pitfalls

- Terminal tile → "Launcher Error: Unhandled error" (500 on POST
  `/api/terminals`; log ends `OSError: out of pty devices`) → the real error
  is a swallowed EACCES from `os.openpty()`: Landlock lacks rw `/dev/pts`.
  Operator adds it to the policy TEMPLATE; it activates at the next sandbox
  recreate (fs policy is parsed at container boot — a live apply changes
  nothing, even for new processes). Details in
  `references/sandbox-internals.md`.
- Wrong CA bundle (`ca-certificates.crt`) → uv TLS failures. Use
  `/etc/openshell-tls/ca-bundle.pem`.
- Skipping the shim → kernels never start (`Kernel died before replying to
  kernel_info`); voila tiles hang at "Running…". Empty-list shims are NOT
  enough — the interface list must contain `lo`.
- A leftover `/sandbox/.jupyter/jupyter_server_config.py` forcing
  `transport = "ipc"` (an abandoned experiment) — remove it; IPC alone never
  fixes kernels and just adds moving parts. `setup.sh` cleans it up.
- Not moving the root launcher YAML / launching from the repo root → 22
  duplicate tiles.
- Any `type: url` tile without `args: {}` → frontend crash
  (`Cannot read properties of undefined (reading 'createNewWindow')`).
- Installing torch/unsloth/cudf → hangs, wasted egress; GPU-only (mods 4 & 6).
- More than one Jupyter server on 8888 → tiles vanish / stale server without
  the shim answers. `kill -9`; SIGTERM is trapped.
- `curl` through `/proxy/absolute/<port>/` appears to hang (chunked stream)
  and `curl -I` returns 405 — red herrings; test voila via
  `/voila/render/...` with the token, or in the browser.
- duckdb import segfaults in this sandbox — harmless, nothing in `code/`
  uses it. joblib "serial mode" warning — benign.
- Trying `docker exec` to bypass seccomp → ALSO bypasses Landlock. FORBIDDEN.
- Switching off branch `edwli-dev` (e.g. `nvwb switch-branch`) → don't.
- Simple Agents Client renders but needs a separate LangGraph backend (a
  module exercise) to chat; Deep Agents Client intentionally serves a "setup
  required" page until its demo backend exists. Neither is a setup defect.
