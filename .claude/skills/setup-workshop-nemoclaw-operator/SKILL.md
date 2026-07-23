---
name: setup-workshop-nemoclaw-operator
description: >-
  Operator/host side of running the NVIDIA "Build an Agent" DevX workshop
  inside an OpenShell/NemoClaw sandbox. ⚠️ NOT the default workshop-setup
  path: for a generic "set up the workshop" request, use the `setup-workshop`
  skill (the standard bare-metal/Brev/AI-Workbench installer). Invoke THIS
  skill ONLY if the user names it explicitly, or explicitly says the workshop
  should run with "NemoClaw" or inside an "OpenShell" sandbox. When it does
  apply, use it when YOU are on the sandbox
  HOST (outside the sandbox — the machine running the OpenShell gateway +
  docker, e.g. via Claude Code) and the user wants the workshop set up in a
  sandbox: stage/apply the egress policy (PyPI, NIM /v1/ranking, scoped GitHub
  clone), stage the NVIDIA API key into the sandbox, kick the in-sandbox agent
  (which runs the `setup-workshop-nemoclaw` skill), then open the inbound path
  (openshell forward service + SSH/Teleport port-forward) so the user can open
  the JupyterLab token URL. Also covers sandbox lifecycle pitfalls (never
  docker-restart, recreate wipes state) and egress-denial debugging via the
  OCSF audit log. NOT for working inside the sandbox.
disable-model-invocation: false
user-invocable: true
---

# setup-workshop-nemoclaw-operator (host side)

Prepares an OpenShell/NemoClaw sandbox so the **in-sandbox agent** can stand up
the Build-an-Agent workshop, then opens the access path from the user's laptop
to the resulting JupyterLab. This is one half of a two-skill pair:

| Skill | Runs | Does |
|---|---|---|
| **this skill** | on the sandbox **host** (outside) | egress policy, secrets staging, kick + unblock the sandbox agent, port-forward, lifecycle |
| `setup-workshop-nemoclaw` | **inside** the sandbox | venv + deps, netlink shim, launcher/bridge fixes, Jupyter launch, URL hand-off |

## Should this skill run at all?

The workshop's DEFAULT setup path is the **`setup-workshop`** skill — the
standard installer for the ordinary pathways (bare metal on Brev, local
install via AI Workbench, GPU hosts). A generic request like "set up the
build-an-agent workshop" goes there, not here.

Invoke this skill ONLY when at least one of these is true:

1. The user names it explicitly (`setup-workshop-nemoclaw-operator`, or asks
   for the "nemoclaw operator" setup skill), or
2. The user explicitly says the workshop should run with **"NemoClaw"** or
   inside an **"OpenShell"** sandbox.

If neither holds, stop and use `setup-workshop` instead — do not infer the
sandbox path from circumstantial evidence (e.g. a sandbox merely existing on
the host).

## Which side am I on?

**On the host** (use this skill): `docker ps` shows an
`openshell-<sandbox>-…` container, the `openshell` CLI is on PATH, and you are
NOT user `sandbox`. **Inside the sandbox** (use the other skill): `whoami` →
`sandbox`, `/sandbox/` exists, no `docker`/`sudo`.

## Conventions

```bash
SANDBOX=hermes-direct                                    # the sandbox name (adjust)
C=$(docker ps --format '{{.Names}}' | grep "openshell-$SANDBOX")   # its container
# NemoClaw community example: policy files + .env live in the project dir, e.g.
cd <nemoclaw-community>/examples/personal-community-sentiment-triage
```

Two policy files matter in the community example: **`policy.yaml`** (the
TEMPLATE — re-rendered into the sandbox at every recreate) and
**`policy.hermes-direct.yaml`** (the live-policy capture you hand-edit). Keep
BOTH in sync with any change, or a recreate/re-apply silently reverts it.

> **If you are an agent (e.g. Claude Code) driving this:** egress-widening
> `openshell policy set` runs are typically denied by the permission layer
> unless the human runs them or explicitly names the exact hosts being opened.
> That denial is correct. Your job is to *stage and verify* the policy file,
> then hand the human one copy-paste command with a precise "this opens
> exactly: …" description. Same for the secrets write (it moves a credential).

## Phase 0 — Discover state (all read-only)

```bash
docker ps --format '{{.Names}}\t{{.Status}}' | grep "$SANDBOX"   # container up?
openshell policy get "$SANDBOX" | head -5                        # live revision + hash
docker exec "$C" ls -la /sandbox/workshop-build-an-agent 2>&1 | head -3   # repo cloned?
docker exec "$C" ls -l /sandbox/workshop-build-an-agent/secrets.env 2>&1  # key staged?
```

`docker exec` is fine for these *filesystem* peeks. It is **NOT** a valid
probe for egress/syscall behavior — exec'd processes bypass the per-process
Landlock/seccomp layers and yield false "allowed" results. Egress tests go
through `openshell sandbox exec` only (single-line commands; it rejects
multi-line args).

## Phase 1 — Egress policy (one-time)

The sandbox denies all egress by default. The workshop needs three additions —
exact YAML in `references/policy-blocks.md`:

| Block | Opens | Needed for |
|---|---|---|
| `github_git_clone` | git smart-HTTP on `github.com`, scoped to the one workshop repo, for the git binaries | cloning the repo (skip if already cloned) |
| `pypi_install` | read-only `GET` to `pypi.org` + `files.pythonhosted.org` | `uv pip install` of the workshop deps |
| `nvidia_retrieval` | `POST /v1/retrieval/**` on `ai.api.nvidia.com` | modules 2/3 `NVIDIARerank` — ⚠️ the legacy `/v1/ranking` rule on `integrate.api.nvidia.com` does NOT cover `llama-nemotron-rerank-1b-v2` |
| `tavily_search` | `POST /search`+`/extract` on `api.tavily.com` | module-1 docgen, module-2 local-MCP web search, module-5 search (key: `TAVILY_API_KEY`) |
| `langsmith_api` | all methods on `api.smith.langchain.com` | module-3 eval/tracing AND silencing tracing-retry spam in every notebook (`variables.env` turns tracing on globally; key: `LANGSMITH_API_KEY`) |
| `tiktoken_encodings` | `GET /encodings/**` on `openaipublic.blob.core.windows.net` | module-7 harness_lab (tiktoken BPE download at first use) |
| `/dev/pts` fs grant | rw on the devpts filesystem (PTY allocation) — under `filesystem_policy`, not `network_policies` | JupyterLab's Terminal tile (terminado → `pty.fork`); without it the tile pops "Launcher Error: Unhandled error" |

Not needed: `build.nvidia.com` (notebook prose only — every model call goes to
`integrate.api.nvidia.com`), torch/conda mirrors, npm.

⚠️ The supervisor parses `filesystem_policy` ONCE at container **boot** —
`openshell policy set` hot-reloads network rules but NOT filesystem grants
(verified live: after applying a `/dev/pts` grant, new spawns still built
the old ruleset). The grant must be in the TEMPLATE (`policy.yaml`) and
takes effect at the next sandbox **recreate**. There is no restart command,
and raw `docker restart` hits the stale-bootstrap-JWT crash loop.

Workflow (details + YAML in the reference):

1. Capture live policy: `openshell policy get "$SANDBOX" --full > /tmp/live.yaml`.
2. Build the apply file = **live policy + the new blocks and nothing else**
   (minimal delta), and structurally verify it (same block names ± the
   additions) before applying. Update `policy.yaml` AND
   `policy.hermes-direct.yaml` in the repo to the same desired state.
3. Apply (human runs it if the permission layer blocks you):
   ```bash
   openshell policy set "$SANDBOX" --policy <file> --wait
   # success: "✓ Policy version N submitted … loaded (active version: N)"
   ```
   **⚠️ `policy set` REPLACES the entire policy document — it does not
   merge.** Applying a partial/stale file silently revokes whatever it omits
   (this exact mistake once reverted a GitHub grant here). OpenShell ≥ 0.0.53
   also has `openshell policy update` for incremental adds — prefer it for
   one-block changes if available.
4. Verify under real enforcement (NOT docker exec):
   ```bash
   openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc 'curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/simple/'   # expect 200
   ```
   `scripts/verify-sandbox-ready.sh` runs the full probe set.

## Phase 2 — Stage the NVIDIA key (one-time)

The notebooks `load_dotenv()` the repo-root `secrets.env` inside the sandbox.
Write it without the key ever touching chat, logs, or shell history — use
`scripts/stage-nvidia-key.sh`, or the one-liner (community example, reusing
`COMPATIBLE_API_KEY` from the project `.env`; substitute a fresh key from
build.nvidia.com if preferred):

```bash
( set -a; . ./.env; printf 'NVIDIA_API_KEY=%s\n' "$COMPATIBLE_API_KEY" | \
  docker exec -i "$C" \
  sh -c 'umask 077; cat > /sandbox/workshop-build-an-agent/secrets.env; \
         chown sandbox:sandbox /sandbox/workshop-build-an-agent/secrets.env' )
```

Never paste keys through the agent's chat channel (the in-sandbox agent will
itself refuse them). Optional: Tavily (module-1 search) / LangSmith (module-3
tracing) — append `TAVILY_API_KEY=` / `LANGSMITH_API_KEY=` lines to the same
file AND add policy entries for `mcp.tavily.com` / `api.smith.langchain.com`.

## Phase 3 — Kick the in-sandbox agent

Message the sandbox agent (adjust repo path if it must clone first):

> Policy now allows PyPI installs and the module-2 ranking endpoint, and
> `NVIDIA_API_KEY` is staged at `/sandbox/workshop-build-an-agent/secrets.env`.
> Run the `setup-workshop-nemoclaw` skill (NOT the bare-metal
> `setup-workshop`). When JupyterLab is up, save the token URL to
> `/sandbox/workshop-url.txt` and report back; I'll open the forward.

NemoClaw-specific gotcha: the agent's persona (`SOUL.md`) may still say
GitHub/PyPI/serving are off-limits, making it refuse without trying. The
gateway caches `SOUL.md` at startup — after editing the durable copy and
uploading to `/sandbox/.hermes-data/SOUL.md`, either restart the agent stack
or (simpler) tell the live agent explicitly what is now allowed, as above.
Do not relay environment guesses as facts — a wrong relayed TLS path once
cost real round-trips; the in-sandbox skill now carries the correct values.

## Phase 4 — Open the access path (per session)

The agent's Jupyter binds the sandbox **inner** loopback (`127.0.0.1:8888`).
Agent processes live in an inner network namespace — a server bound even to
0.0.0.0 is unreachable at the container IP. The only inbound path:

```bash
# 1. On this host (FOREGROUND — leave the terminal open). Note: `openshell
#    forward list`/`stop` do NOT track `forward service` tunnels — stop it
#    with Ctrl-C or pkill -f "forward service $SANDBOX".
openshell forward service "$SANDBOX" --target-port 8888 --local 8888

# 2. Sanity check from another host shell (302 = alive, auth redirect):
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8888/lab

# 3. Get the token URL (gateway masks tokens in agent chat, hence the file):
docker exec "$C" cat /sandbox/workshop-url.txt
```

Then from the **laptop**, ONE of (full Teleport troubleshooting in
`references/access-and-lifecycle.md`):

```bash
ssh -N -L 8888:localhost:8888 <user>@<sandbox-host>          # vanilla ssh
tsh ssh -N -L 8888:localhost:8888 <user>@<node-name>         # Teleport: NODE NAME from `tsh ls`, not DNS/IP
```

**`-N` is silent when it works** — no output means the tunnel is UP; open the
browser before assuming a hang. Finally open the token URL:
`http://localhost:8888/lab?token=…`.

## Phase 5 — When something is denied

The L7 proxy/OCSF audit log names the exact process path and rule for every
verdict:

```bash
docker logs "$C" | grep -E "DENIED|NET:FAIL" | tail
```

Feed that line back into the policy (right block, right binary — enforcement
resolves symlinks, so e.g. `git-remote-https` → list `git-remote-http` too),
re-apply, re-verify. If the in-sandbox agent reports a blocked call, ask it
for the exact URL/error and match it against the log.

## Lifecycle pitfalls (each caused real breakage)

- **NEVER `docker restart` the sandbox container.** It boots from a static
  bootstrap JWT (1-hour TTL, not refreshed on disk); a restarted container
  re-reads the stale token and crash-loops (`Policy fetch failed …
  ExpiredSignature`), sticking the sandbox in `Provisioning`. Recovery needs a
  re-minted token or a delete/recreate/restore cycle.
- **A container restart does NOT relaunch the agent stack** (`nemoclaw-start`:
  agent, relay, bridges — and JupyterLab). Relaunch the stack (e.g. the
  community repo's autoheal `watchdog.sh`), then have the agent re-run
  `start-jupyter.sh`.
- **A sandbox recreate wipes the container filesystem** (venv, shim,
  `secrets.env`, the server). Policy is re-rendered from the `policy.yaml`
  TEMPLATE at recreate — which is why the workshop blocks must live in the
  template too. After recreate: redo Phase 2, then have the agent re-run
  `setup.sh` + `start-jupyter.sh` (both idempotent).
- **`docker exec` proves nothing about the agent's sandbox** (1 seccomp filter
  vs the agent's 4, no Landlock). Egress/syscall tests: `openshell sandbox
  exec` only.
- **The netlink/seccomp kernel-startup block has NO operator knob** — it is
  compiled into the in-container OpenShell supervisor (Rust seccompiler), not
  the Docker seccomp JSON, not the policy schema. The sanctioned fix is the
  in-sandbox LD_PRELOAD shim (the sandbox skill builds it). Do not edit Docker
  seccomp JSON for this; it has no effect.
- **Never route workshop execution through `docker exec`** to dodge seccomp —
  it also escapes Landlock egress enforcement. Forbidden.

## End-to-end verification checklist

- [ ] `openshell policy get "$SANDBOX"` shows the new revision; probes via
      `openshell sandbox exec`: pypi 200, `integrate.api.nvidia.com/v1/models` 200.
- [ ] `docker exec "$C" ls -l /sandbox/workshop-build-an-agent/secrets.env` → present, mode 600.
- [ ] Sandbox agent reports JupyterLab up; `docker exec "$C" cat /sandbox/workshop-url.txt` → URL.
- [ ] Forward running; host `curl …:8888/lab` → 302.
- [ ] Laptop tunnel up; browser shows 11 launcher tiles; a module-2 rerank cell returns 200.
- [ ] Terminal tile opens a shell (`POST /api/terminals` with token → 200) —
      needs the `/dev/pts` grant; when absent the tile is auto-hidden.
