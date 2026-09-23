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
  clone), optionally stage the NVIDIA API key, kick the in-sandbox agent
  (which runs the `setup-workshop-nemoclaw` skill), then open the inbound path
  (openshell forward service + SSH/Teleport port-forward) so the user can open
  the JupyterLab token URL. Also covers sandbox lifecycle pitfalls (container
  restarts are only token-window-safe, recreate wipes state) and
  egress-denial debugging via the OCSF audit log. NOT for working inside the
  sandbox.
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
# Its container — exact, fail-closed selection by OpenShell runtime labels
# (substring grep can match a similarly named sandbox, e.g. hermes-direct-2):
C=$(docker ps --filter 'label=openshell.ai/managed-by=openshell' \
              --filter "label=openshell.ai/sandbox-name=$SANDBOX" --format '{{.Names}}')
[ "$(printf '%s\n' "$C" | grep -c .)" -eq 1 ] || echo "FATAL: not exactly one container for '$SANDBOX': ${C:-none}"
# NemoClaw community example: the deployment (scripts + policy.yaml + .env)
# and the workshop skills ship together in
cd <nemoclaw-community>/examples/recipes/nvidia/agentic-ai-learning-path
```

Policy ownership: the deployment's `policy.yaml` template belongs to the
deployment recipe — this flow does NOT edit it (or any other file of that
example). The workshop policy lives in the sandbox's **live** policy: Phase 1
applies live + the additions from `references/policy-blocks.md`, and the
live policy is thereafter the source of truth. Captures
(`openshell policy get "$SANDBOX" --full | sed '1,/^---$/d'`) are scratch
artifacts — regenerate on demand, do not track them. Consequence: a recreate
through the deployment's own machinery (e.g. its `scripts/bring-up.sh` /
`scripts/03-sandbox.sh`) re-renders the STOCK template, silently reverting
every workshop grant (network AND filesystem) and wiping the workshop
filesystem — after such a recreate, re-run Phase 1, then 1b, then Phase 3
(all idempotent).

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

(`openshell policy get` prints `Active: 0` next to `Status: Loaded` for a
policy that has never been superseded — normal for a fresh sandbox, not "no
policy active".)

Then extract the live policy and establish which way drift runs — do NOT
assume the sandbox is running the recipe's stock policy. `--full` prepends a
metadata header (`Version:`/`Hash:`/… plus a `---` line) that must be
stripped before the YAML is usable:

```bash
openshell policy get "$SANDBOX" --full | sed '1,/^---$/d' > /tmp/live.yaml
python3 -c 'import yaml,sys
a,b=[sorted(yaml.safe_load(open(f))["network_policies"]) for f in sys.argv[1:]]
print("template-only:", [k for k in a if k not in b])
print("live-only:    ", [k for k in b if k not in a])' policy.yaml /tmp/live.yaml
```

Read the result in BOTH directions. `template-only` blocks = the live policy
is missing stock grants (unusual — investigate before overwriting them).
`live-only` blocks = the workshop additions are already applied (the expected
state after Phase 1, or after a prior run) → Phase 1's apply is a no-op.
Either way the template stays untouched — it is the recipe's file, and a
recreate from it always reverts to stock; Phase 1b and the lifecycle notes
below deal with that.

`docker exec` is fine for these *filesystem* peeks. It is **NOT** a valid
probe for egress/syscall behavior — exec'd processes bypass the per-process
Landlock/seccomp layers and yield false "allowed" results. Egress tests go
through `openshell sandbox exec` only (single-line commands; it rejects
multi-line args).

## Phase 1 — Egress policy (one-time)

The sandbox denies all egress by default. The workshop needs the additions
below — but do not assume they are absent: go by the Phase 0 drift check (if
they are already live, skip the apply; the live policy is the source of
truth and no repo file needs syncing). Exact YAML in
`references/policy-blocks.md`:

| Block | Opens | Needed for |
|---|---|---|
| `github_git_clone` | git smart-HTTP on `github.com`, scoped to the one workshop repo, for the git binaries | cloning the repo (skip if already cloned) |
| `pypi_install` | read-only `GET` to `pypi.org` + `files.pythonhosted.org` | `uv pip install` of the workshop deps |
| `nvidia_retrieval` | `POST /v1/retrieval/**` on `ai.api.nvidia.com` | modules 2/3 `NVIDIARerank` — ⚠️ the legacy `/v1/ranking` rule on `integrate.api.nvidia.com` does NOT cover `llama-nemotron-rerank-1b-v2` |
| `tavily_search` | `POST /search`+`/extract` on `api.tavily.com` | module-1 docgen, module-2 local-MCP web search, module-5 search (key: `TAVILY_API_KEY`) |
| `langsmith_api` | all methods on `api.smith.langchain.com` | module-3 eval/tracing AND silencing tracing-retry spam in every notebook (`variables.env` turns tracing on globally; key: `LANGSMITH_API_KEY`) |
| `tiktoken_encodings` | `GET /encodings/**` on `openaipublic.blob.core.windows.net` | module-7 harness_lab (tiktoken BPE download at first use) |
| `npm_install` | read-only `GET` to `registry.npmjs.org` (binary: `/usr/local/bin/node`) | module-5 "Deep Agents Client" tile — `demo/` needs `npm install` or the tile only serves its "setup required" page; also fetches the `mcp-remote` transport for the block below |
| `mcp_tavily` | `GET`/`POST`/`DELETE` on `mcp.tavily.com` (binary: `/usr/local/bin/node`) | module-2 PART 2A remote MCP — the shipped default. ⚠️ Policy alone is not enough: the MCP stdio transport drops the proxy env, so the in-sandbox `tune_remote_mcp_env.py` is also required |
| `/dev/pts` fs grant | rw on the devpts filesystem (PTY allocation) — under `filesystem_policy`, not `network_policies` | JupyterLab's Terminal tile (terminado → `pty.fork`); without it the tile pops "Launcher Error: Unhandled error" |

Not needed: `build.nvidia.com` (notebook prose only — every model call goes to
`integrate.api.nvidia.com`), torch/conda mirrors, npm.

⚠️ The supervisor parses `filesystem_policy` ONCE at container **boot** —
`openshell policy set` hot-reloads network rules but NOT filesystem grants
(verified live on OpenShell v0.0.53 AND v0.0.96: after applying a `/dev/pts`
grant, new spawns still built the old ruleset). Include the fs grants in the
Phase 1 apply anyway (they ride along dormant), then boot them with the
**Phase 1b token-TTL-guarded restart** below.

Workflow (details + YAML in the reference):

1. Capture the live policy WITH the metadata header stripped (raw `--full`
   output is not valid apply input; already done if you ran the Phase 0
   drift check):
   `openshell policy get "$SANDBOX" --full | sed '1,/^---$/d' > /tmp/live.yaml`
2. Build the apply file = **live policy + the new blocks and nothing else**:
   `python3 scripts/build-workshop-policy.py /tmp/live.yaml /tmp/apply.yaml`
   (composes the additions, structurally self-verifies, idempotent — exits
   non-zero on any surprise). The `filesystem_policy` additions (`/dev/pts`
   rw, `/sys/fs/cgroup` ro) ride along dormant until Phase 1b boots them.
   Do NOT edit the deployment recipe's files: the applied live policy is the
   only carrier of workshop state.
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

## Phase 1b — Boot the filesystem grants (token-TTL-guarded restart)

The `/dev/pts` + `/sys/fs/cgroup` grants applied in Phase 1 stay dormant
until a container boot. Probe under real enforcement:

```bash
openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc 'python3 -c "import os; os.openpty()" && echo PTY-OK'
```

`PTY-OK` → skip this phase. Denied → boot the grants with a container
restart. A restart is safe ONLY while the sandbox's bootstrap token is
valid: the token is written once at create
(`/etc/openshell/auth/sandbox.jwt`) and never refreshed on disk, so the
supervisor re-reads it on boot — valid token → clean recovery (verified on
OpenShell v0.0.96: Ready again in ~10 s, fs grants live); expired token →
Unauthenticated/`ExpiredSignature` crash loop, sandbox stuck in
`Provisioning` (verified live on v0.0.53-created and v0.0.96-resumed
sandboxes). Guard on container age and fail closed:

```bash
CREATED=$(docker inspect "$C" --format '{{.Created}}')
AGE=$(( $(date +%s) - $(date -d "$CREATED" +%s) ))
if [ "$AGE" -lt 2700 ]; then    # 45-min guard against the ~1 h token TTL
  docker restart "$C"
else
  echo "sandbox older than the token-safe window — use the recipe-recreate fallback below"
fi
```

In the normal flow the sandbox is minutes old, so the guard always passes.
After the restart: wait for `openshell sandbox list` to show `Ready`
(seconds), re-resolve `$C` (label selection, as in Conventions), re-probe
PTY (expect `PTY-OK`).

A container restart does NOT relaunch the agent stack (`nemoclaw-start`).
Relaunch it with the create-time authorization env rebuilt **from the
deployment recipe's `.env`** — the recipe is the source of truth for those
values; never scrape them from a live process's `/proc` and never expand
them through create/exec argv. The exact procedure (env file, mode 600,
sourced inside a supervisor session) is
references/access-and-lifecycle.md § Recovering lost create-time env — run
it after the restart, then verify:

```bash
docker exec "$C" sh -c 'pid=$(pgrep -f "[h]ermes gateway run" | head -1); tr "\0" "\n" < /proc/$pid/environ' | grep -cE '^(SLACK_ALLOW|OUTLOOK_)'   # expect ≥ 1
```

**Fallback — sandbox older than the token-safe window** (long-running
deployment, or workshop state you can afford to lose): recreate through the
deployment recipe's own machinery (e.g. `03-sandbox.sh`/`bring-up.sh`),
which owns sandbox lifecycle and injects the authorization env its
supported way. That recreate boots the STOCK policy template and wipes the
container filesystem, so afterwards re-run Phase 1 (apply the workshop
blocks), this phase's restart (the fresh sandbox is well inside the token
window), and the remaining phases — every step is idempotent. Do not
hand-roll a delete/create in this flow.

Then continue with the next phases.

## Phase 2 — Keys: leave NVIDIA_API_KEY UNSET (default)

**Do nothing here in the normal flow.** The learner sets `NVIDIA_API_KEY` in
the workshop's own **Secrets Manager** tile, which writes the repo-root
`secrets.env` that every notebook `load_dotenv()`s. Leaving the variable absent
at server-launch time is deliberate, not an oversight:

`start-jupyter.sh` `set -a`-sources `secrets.env` into the Jupyter server env at
launch, and kernels inherit that env. `load_dotenv()` does **not** override
variables already present in the environment — so anything baked in at launch
**shadows later edits to the file**. Stage a key before launch and the learner's
Secrets Manager change is silently ignored until the server restarts; leave it
unset and `load_dotenv()` stays authoritative, so the key takes effect on the
next cell run with no restart. This is exactly why the Tavily and LangSmith
keys never exhibited the problem — they were never injected.

`scripts/verify-sandbox-ready.sh` agrees: an absent key is a PASS in its
default mode. Set `EXPECT_PRESEEDED=1` only when auditing an image that is
supposed to carry a baked-in key.

⚠️ **Never fall back to `COMPATIBLE_API_KEY` / `OPENAI_API_KEY`.** Those name
the NemoClaw *agent's* inference credential — in the community example an
`sk-…` key for the host TLS proxy (`NEMOCLAW_ENDPOINT_URL`), not a
build.nvidia.com `nvapi-…` key. The old one-liner did this and produced a
`secrets.env` that looked correctly populated while every notebook died with
`AuthenticationError: 401` against `integrate.api.nvidia.com`. Real incident;
`stage-nvidia-key.sh` now refuses that fallback and warns on any non-`nvapi-`
key.

Only pre-seed a key when you actually want one baked in (unattended classroom
image), and pass a real `nvapi-…` key explicitly:

```bash
printf '%s' 'nvapi-…' | SANDBOX=<sandbox> bash scripts/stage-nvidia-key.sh
# or, from a dotenv file that carries a genuine NVIDIA_API_KEY:
SANDBOX=<sandbox> bash scripts/stage-nvidia-key.sh --env-file ./.env
```

The script merges (never truncates) — the Secrets Manager tile rewrites the
same file wholesale, so a truncating write would destroy keys the learner
already set. It reports key NAMES only, never values. If you pre-seed while
JupyterLab is already up, re-run `start-jupyter.sh` (token/URL survive) so
kernels pick the key up.

Never paste keys through the agent's chat channel (the in-sandbox agent will
itself refuse them). Tavily (modules 1/2/5 search) and LangSmith (module-3
tracing) are handled the same way — set them in the Secrets Manager, or pass
them to the same script; their policy blocks are in `references/policy-blocks.md` too.

## Phase 3 — Kick the in-sandbox agent

Message the sandbox agent (adjust repo path if it must clone first):

> Policy now allows the workshop-repo clone route, PyPI installs, and the
> NIM/reranking endpoints. Run the `setup-workshop-nemoclaw` skill (NOT the
> bare-metal `setup-workshop`). When JupyterLab is up, save the token URL to
> `/sandbox/workshop-url.txt` and report back; I'll open the forward.
> `NVIDIA_API_KEY` is deliberately not staged — the learner sets it in the
> Secrets Manager tile.

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
# Agent-driven runs (e.g. Claude Code): a session-tied background task dies
# with the session, silently cutting the user's access (happened live).
# Start it detached instead, so it outlives the session:
#   setsid nohup openshell forward service "$SANDBOX" \
#     --target-port 8888 --local 8888 >/tmp/forward-"$SANDBOX".log 2>&1 </dev/null &

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

**Hand-off rule — the final access-steps message ALWAYS includes the
host-side forward command,** even when a forward is already up and serving.
The forward is the one leg the user cannot see: `forward list` does not
track it, and it dies silently with whatever shell or agent session spawned
it (a Claude Code exit cut a user's access exactly this way). Alongside the
laptop tunnel + token URL, hand the user something like:

> FYI — the JupyterLab URL depends on a port-forward running on the sandbox
> host. If the URL stops responding, restart it there:
> `openshell forward service <sandbox> --target-port 8888 --local 8888`
> (leave it running; stop with `pkill -f "forward service <sandbox>"`), then
> reload the page. Re-read the token URL any time with:
> `docker exec <container> cat /sandbox/workshop-url.txt`.

If the deployment's `.env` configured Slack (or Outlook), append an optional
pointer — the resident agent carries the workshop tutor skills on every
channel it serves:

> Optional: your deployment's Slack bot is the same sandboxed agent — DM it
> a workshop question (e.g. "quiz me on module 1") to meet your tutor
> outside JupyterLab.

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

Two verdict patterns that are NOT policy gaps (both observed live):

- **Boot-time noise:** a `/usr/bin/python3.13` DENIED to `github.com:443`
  ("binary not allowed in policy 'github_git_clone'") right after sandbox
  start is agent-stack startup traffic. Python is deliberately absent from
  that block's `binaries` — ignore it; it is not workshop breakage.
- **First-touch flake:** a probe reports curl `000` while the audit log shows
  ALLOWED at both engines for that same request — the first request to a host
  through the L7 proxy can stall past curl's timeout. Retry before editing
  policy (`verify-sandbox-ready.sh` retries its clone-route probe once for
  exactly this reason).

## Lifecycle pitfalls (each caused real breakage)

- **`docker restart` is safe ONLY inside the bootstrap-token window.** The
  container boots from a static bootstrap JWT (~1-hour TTL, written once at
  create to `/etc/openshell/auth/sandbox.jwt` and never refreshed on disk).
  Within the window a restart recovers cleanly and boots dormant
  `filesystem_policy` grants (verified on OpenShell v0.0.96: Ready in ~10 s);
  past it the supervisor re-reads the stale token and crash-loops
  (`ExpiredSignature`), sticking the sandbox in `Provisioning` (verified on
  v0.0.53 and v0.0.96) — recovery then needs a recreate. Use the Phase 1b
  age guard; never restart an aged sandbox.
- **Gateway upgrades restart sandbox containers.** An upgraded gateway
  resumes sandboxes by restarting their containers, so every sandbox older
  than its token window bricks exactly as above (observed live during the
  0.0.53 → 0.0.96 upgrade). Plan sandbox recreates around gateway upgrades.
- **A container restart does NOT relaunch the agent stack** (`nemoclaw-start`:
  agent, relay, bridges — and JupyterLab). Relaunch the stack per
  references/access-and-lifecycle.md § Recovering lost create-time env, then
  have the agent re-run `start-jupyter.sh`.
- **A sandbox recreate wipes the container filesystem** (venv, shim,
  `secrets.env`, the server), and the sanctioned recreate path is the
  deployment's own machinery (its `scripts/bring-up.sh` /
  `scripts/03-sandbox.sh`) — it re-renders the STOCK template, so every workshop grant
  (network AND filesystem) reverts by design. Afterwards re-run Phase 1, the
  Phase 1b restart (fresh sandbox — inside the token window), and Phase 2 if
  a key was pre-seeded, then have the agent re-run `setup.sh` +
  `start-jupyter.sh` (all idempotent). Verify the create-time authorization
  env reached the relaunched gateway (Phase 1b check) — a Slack bot that
  answers everyone with pairing codes plus a missing `outlook-bridge.py`
  process means it didn't; fix per references/access-and-lifecycle.md, no
  re-recreate needed.
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
- [ ] (only if a key was pre-seeded) `docker exec "$C" ls -l /sandbox/workshop-build-an-agent/secrets.env` → present, mode 600.
- [ ] Sandbox agent reports JupyterLab up; `docker exec "$C" cat /sandbox/workshop-url.txt` → URL.
- [ ] Forward running; host `curl …:8888/lab` → 302.
- [ ] Laptop tunnel up; browser shows 11 launcher tiles; a module-2 rerank cell returns 200.
- [ ] Terminal tile opens a shell (`POST /api/terminals` with token → 200) —
      needs the `/dev/pts` grant BOOTED. An auto-hidden tile means the Phase
      1b restart was skipped; on a fresh sandbox run it before setup.
- [ ] (if a Slack/Outlook channel is configured) a DM to the deployment's bot
      with a workshop question routes to the tutor skills — surface this
      option to the user alongside the JupyterLab URL (Phase 4).
