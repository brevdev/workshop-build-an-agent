# Policy blocks — exact YAML, apply semantics, verification

Everything here was verified live against OpenShell v0.0.53, with
lifecycle-sensitive items re-verified on v0.0.96 where noted (gateway as a
user systemd unit `openshell-gateway.service`; L7 proxy + OCSF audit log via
`docker logs <container>`). Adjust the repo slug / sandbox name if yours
differ.

## Apply semantics (read first)

- `openshell policy set <sandbox> --policy <file> --wait` **replaces the whole
  policy document**. The file must contain the FULL desired state — every
  block the sandbox needs, not just the additions. A partial/stale file
  silently revokes whatever it omits. Real incident: a news-sources update
  applied from a stale template clobbered a `github_repo_readwrite` grant.
- Success output: `✓ Policy version N submitted (hash: …)` then
  `✓ Policy version N loaded (active version: N)`. The hash from
  `openshell policy get <sandbox>` changing is your confirmation it landed.
- The deployment's `policy.yaml` template (in the NemoClaw community repo:
  the agentic-ai-learning-path example's root) is NOT edited by this flow; the sandbox's LIVE policy is the source of
  truth for workshop grants. Captures are scratch artifacts — regenerate via
  the workflow below, do not track them. Consequence: a recreate through the
  deployment's own machinery re-renders the stock template and silently reverts
  every workshop grant — re-run SKILL.md Phase 1 + 1b afterwards.
- OpenShell ≥ 0.0.53 also ships `openshell policy update` for incremental
  changes — prefer it for one-block additions if available.

## Minimal-delta workflow (what an agent should stage for the human)

```bash
# `--full` prepends a metadata header (Version/Hash/Status/Active/Created +
# a `---` separator). Strip it — the raw output is NOT valid apply input:
openshell policy get "$SANDBOX" --full | sed '1,/^---$/d' > /tmp/live.yaml
# 0. If the blocks below are ALREADY in /tmp/live.yaml (e.g. Phase 1 ran
#    before), apply nothing — the live policy is the source of truth and no
#    repo file needs syncing.
# 1+2. Compose + structural self-verify in one step (idempotent):
#    python3 <operator skill>/scripts/build-workshop-policy.py /tmp/live.yaml /tmp/apply.yaml
# 3. Hand the human:  openshell policy set "$SANDBOX" --policy /tmp/apply.yaml --wait
#    with a one-line statement of exactly what it opens.
```

This matters because an agent-run `policy set` is usually (correctly) blocked
by the operator's permission layer, and because building from the LIVE policy
avoids re-applying unrelated grants the human didn't ask to restore.

## The blocks

Add under `network_policies:`. Copies of the blocks running in the NemoClaw
community example; adjust the repo slug if the workshop repo differs. Verify
against the LIVE policy first (step 0 above): the running deployment may
already carry them — then there is nothing to apply (the live policy is the
source of truth; no files to sync).

```yaml
  # Git smart-HTTP (clone/fetch) for the scoped workshop repo. git clone
  # talks to github.com (NOT api.github.com):
  #   GET  /<repo>[.git]/info/refs   POST /<repo>[.git]/git-upload-pack
  # Read-only: git-receive-pack (push) deliberately absent. Anonymous (public
  # repo; no credential covers github.com).
  github_git_clone:
    name: github-git-clone
    endpoints:
    - host: github.com
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: GET, path: /brevdev/workshop-build-an-agent/info/refs }
      - allow: { method: POST, path: /brevdev/workshop-build-an-agent/git-upload-pack }
      - allow: { method: GET, path: /brevdev/workshop-build-an-agent.git/info/refs }
      - allow: { method: POST, path: /brevdev/workshop-build-an-agent.git/git-upload-pack }
    binaries:
    # Enforcement resolves symlinks: git-remote-https is a symlink to
    # git-remote-http, so list BOTH (the connecting process is the target).
    - path: /usr/bin/git
    - path: /usr/lib/git-core/git-remote-https
    - path: /usr/lib/git-core/git-remote-http
    - path: /usr/bin/curl
  # OPTIONAL module-7 extension: `scripts/install_nvidia_skill.sh` clones the
  # public NVIDIA/skills catalog to demo signature-verified skill installs.
  # Without these rules the clone is policy-DENIED and that one exercise is
  # unavailable (everything else in module 7 works). Append INSIDE the
  # github_git_clone endpoint's rules if the operator wants it enabled:
  #   - allow: { method: GET, path: /NVIDIA/skills/info/refs }
  #   - allow: { method: POST, path: /NVIDIA/skills/git-upload-pack }
  #   - allow: { method: GET, path: /NVIDIA/skills.git/info/refs }
  #   - allow: { method: POST, path: /NVIDIA/skills.git/git-upload-pack }
  # Python package index: read-only GET so the agent can uv-install the
  # workshop deps. uv venv pythons are symlinks to /usr/bin/python3.13, so
  # these binaries entries cover venv processes too.
  pypi_install:
    name: pypi-install
    endpoints:
    - host: pypi.org
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: GET, path: /** }
    - host: files.pythonhosted.org
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: GET, path: /** }
    binaries:
    - path: /usr/local/bin/uv
    - path: /usr/bin/python3
    - path: /usr/bin/python3.13
    - path: /opt/hermes/.venv/bin/python
    - path: /usr/bin/curl
```

And inside the **existing** NIM/inference block (both `integrate.api.nvidia.com`
and any mirror host), alongside the chat/completions/embeddings rules:

```yaml
      # NIM reranking (langchain NVIDIARerank, workshop module 2 agentic-RAG).
      - allow:
          method: POST
          path: /v1/ranking
```

## Workshop integration blocks (audited 2026-07-21)

Four more routes the module content actually exercises. Full-coverage
sandboxes should carry all four (a SKILL.md Phase 1b restart boots from the
live policy, so they survive it; a stock-template recreate reverts them —
re-run Phase 1). Binaries: same python/curl set as `pypi_install` minus uv.

```yaml
  # tavily-python REST (module-1 docgen tool, module-2 LOCAL MCP server,
  # module-5 search). NOT mcp.tavily.com — that is the remote-MCP host, which
  # also needs npm and is deliberately not opened (see What NOT to open).
  tavily_search:
    name: tavily-search
    endpoints:
    - host: api.tavily.com
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: POST, path: /search }
      - allow: { method: POST, path: /extract }
  # variables.env sets LANGSMITH_TRACING=true for every notebook; module-3
  # eval flows create datasets/experiments/runs/feedback — hence all methods.
  langsmith_api:
    name: langsmith-api
    endpoints:
    - host: api.smith.langchain.com
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: GET, path: /** }
      - allow: { method: POST, path: /** }
      - allow: { method: PATCH, path: /** }
      - allow: { method: PUT, path: /** }
      - allow: { method: DELETE, path: /** }
  # ⚠️ NVIDIARerank for nvidia/llama-nemotron-rerank-1b-v2 (modules 2/3) posts
  # to ai.api.nvidia.com/v1/retrieval/<model>/reranking — the
  # integrate.api.nvidia.com /v1/ranking rule does NOT cover it.
  nvidia_retrieval:
    name: nvidia-retrieval
    endpoints:
    - host: ai.api.nvidia.com
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: POST, path: /v1/retrieval/** }
  # npm registry — module-5 "Deep Agents Client" tile. demo/ is a Vite+React
  # app; without node_modules the tile only ever serves its "setup required"
  # page. All 333 `resolved` URLs in demo/package-lock.json point at
  # registry.npmjs.org and NOTHING else (verified from the lockfile), including
  # the Node binary itself: demo/package.json declares a spurious
  # `"node": "^25.6.1"` dep whose node-bin-setup postinstall pulls
  # `node-linux-x64-<ver>.tgz` from the REGISTRY, not from nodejs.org — so this
  # one host is sufficient. GET-only: npm publish/login (PUT/POST) stay denied.
  # `npm audit` POSTs /-/npm/v1/security/advisories/bulk and is denied; that is
  # non-fatal (install still exits 0) — pass --no-audit to silence it.
  # Binary is the node interpreter: npm and npx are JS scripts run by it.
  npm_install:
    name: npm-install
    endpoints:
    - host: registry.npmjs.org
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: GET, path: /** }
    binaries:
    - path: /usr/local/bin/node
  # Tavily REMOTE MCP host — module-2 PART 2A, the shipped default that every
  # non-sandboxed pathway uses. Needs the npm_install block too (npx fetches the
  # mcp-remote transport at call time). mcp-remote 0.1.38 speaks MCP
  # streamable-HTTP: POST for JSON-RPC, GET for the SSE stream and for OAuth
  # discovery under /.well-known/**, DELETE to end the session. Observed live:
  #   GET  /mcp/                                       GET /.well-known/oauth-authorization-server
  #   GET  /.well-known/oauth-protected-resource/mcp   POST /mcp/
  # ⚠️ Policy alone is NOT sufficient — the MCP stdio transport drops the proxy
  # env vars, so the in-sandbox skill's tune_remote_mcp_env.py is also required.
  mcp_tavily:
    name: mcp-tavily
    endpoints:
    - host: mcp.tavily.com
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: GET, path: /** }
      - allow: { method: POST, path: /** }
      - allow: { method: DELETE, path: /** }
    binaries:
    - path: /usr/local/bin/node
  # tiktoken downloads BPE encodings at first get_encoding() (module 7).
  tiktoken_encodings:
    name: tiktoken-encodings
    endpoints:
    - host: openaipublic.blob.core.windows.net
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: GET, path: /encodings/** }
```

## Optional — module-6 OpenClaw (`openclaw_inference`)

Only needed if you want module 6's **OpenClaw agent** to actually run, rather
than the module falling back to its built-in mock agent. Two separate facts,
verified live 2026-07-27:

1. **Installing OpenClaw needs NO new egress.** `npm i -g openclaw@latest`
   resolves entirely from `registry.npmjs.org`, already open via `npm_install`.
   `openclaw` is **unscoped**, so it sidesteps the proxy rule that rejects
   request-targets containing an encoded `/` — that rule is what blocks scoped
   metadata like `@anthropic-ai/claude-code` (`/@scope%2Fname`). Confirmed:
   `npm view openclaw version` → `2026.7.1-2`, install → 309 packages in 15s,
   `openclaw --version` → `OpenClaw 2026.7.1-2`. The installer's other hosts
   (`openclaw.ai`, nodesource, `nodejs.org`, `github.com` for `gum`,
   `raw.githubusercontent.com` for Homebrew) are only used by the convenience
   `install.sh` wrapper; on Linux with Node ≥ 22 already present (sandbox ships
   v24.16.0) none are required.
2. **Running it does need this block.** `setup_openclaw.md` configures a Custom
   Provider at `https://integrate.api.nvidia.com/v1`, but OpenClaw is a node
   process and the `nvidia` block's `binaries` lists only hermes/python — so
   node gets `ERR_PROXY_TUNNEL` (control: node → `registry.npmjs.org` = PONG).

```yaml
  # Module-6 OpenClaw. Deliberately a SEPARATE narrow block instead of adding
  # /usr/local/bin/node to the `nvidia` block: this grants node chat inference
  # ONLY — not embeddings, not /v1/ranking, not inference-api.nvidia.com.
  # GET /v1/models is what the onboarding wizard's connection test calls.
  openclaw_inference:
    name: openclaw-inference
    endpoints:
    - host: integrate.api.nvidia.com
      port: 443
      protocol: rest
      enforcement: enforce
      rules:
      - allow: { method: POST, path: /v1/chat/completions }
      - allow: { method: GET, path: /v1/models }
    binaries:
    - path: /usr/local/bin/node
```

⚠️ **Pedagogical caveat — state this to the learner.** Module 6 contrasts three
tiers: mock (no defenses) → *host* OpenClaw (**unsandboxed**, prompt-level
refusals) → NemoClaw (**sandboxed**, kernel enforcement). OpenClaw installed
*inside* this sandbox is NOT the unsandboxed tier — it inherits the same
Landlock/seccomp/proxy enforcement as NemoClaw, so tier 2 and tier 3 stop being
a clean comparison. It is still strictly more than the mock-only default. If you
want the true three-way contrast, run OpenClaw on the host, outside the sandbox.

Matching keys (`TAVILY_API_KEY`, `LANGSMITH_API_KEY`) go into the same
`secrets.env` via `stage-nvidia-key.sh --env-file` or exported env vars.

## Filesystem grant — /dev/pts (JupyterLab Terminal tile)

Goes under `filesystem_policy` in the same document (NOT `network_policies`):

```yaml
filesystem_policy:
  read_only:
  # ... existing entries ...
  - /sys/fs/cgroup   # duckdb (via data-designer, modules 3/4) probes memory.max/cpu.max at connect
  read_write:
  # ... existing entries ...
  - /dev/pts   # PTY master+slaves; /dev/ptmx is a symlink to pts/ptmx
```

Why: terminado (`pty.fork` behind the launcher's Terminal tile) opens
`/dev/ptmx` and the slave under `/dev/pts/`; Landlock denies both without the
grant. Symptom without it: Terminal tile → "Launcher Error: Unhandled error";
jupyter log ends `OSError: out of pty devices` — a CPython red herring, the
real EACCES from `os.openpty()` is swallowed (full story in the sandbox
skill's `references/sandbox-internals.md`).

Verify (Landlock-real):

```bash
openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc 'python3 -c "import os; os.openpty()" && echo PTY-OK'
```

⚠️ `filesystem_policy` is parsed ONCE at container boot — a live `policy set`
does NOT activate new fs grants, even for freshly spawned processes (network
blocks DO hot-reload; watch the supervisor's `Landlock ruleset built` log
lines: the rw count won't change on a live apply; no-hot-reload verified on
both v0.0.53 and v0.0.96). Apply the grants with the rest of Phase 1 (they
ride along dormant), then boot them via the SKILL.md Phase 1b
token-TTL-guarded restart — a within-window `docker restart` boots the
grants cleanly (verified on v0.0.96), while a restart past the ~1 h token
window bricks the sandbox (`ExpiredSignature` crash loop). After the boot,
`start-jupyter.sh` auto-detects working PTYs and enables the Terminal tile.

## What NOT to open

- `build.nvidia.com` — not needed; it appears only in notebook prose. Chat/
  completions/embeddings hit `integrate.api.nvidia.com`; reranking hits
  `ai.api.nvidia.com` (block above).
- (`mcp.tavily.com` used to be listed here. It is now OPENED — see the
  `mcp_tavily` block above — so module-2 PART 2A has parity with the
  non-sandboxed pathways. PART 2B still works and remains a valid teaching
  contrast: the local server exposes 1 tool, the remote MCP exposes 5.)
- `t.explodinggradients.com` — ragas telemetry; the sandbox skill exports
  `RAGAS_DO_NOT_TRACK=true` instead.
- npm registry for tooling, conda/pytorch mirrors,
  `workbench.download.nvidia.com` — the sandbox path needs none of them (the
  in-sandbox skill ships a prebuilt labextension and compiles its shim with
  the ziglang wheel).
- GitHub push (`git-receive-pack`) — deliberately absent above.

## Verification (Landlock-real, not docker exec)

```bash
openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc 'curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/simple/'                      # 200
openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc 'curl -s -o /dev/null -w "%{http_code}\n" https://integrate.api.nvidia.com/v1/models'    # 200
# Scoping negative tests (should FAIL with 403 / CONNECT 403):
openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc 'git ls-remote https://github.com/torvalds/linux 2>&1 | tail -1'
```

Notes: `openshell sandbox exec` takes single-line commands only (it rejects
multi-line args). `docker exec` is NOT a valid probe — exec'd processes carry
only Docker's container-level seccomp (1 filter vs the agent's 4) and no
Landlock, so they can reach hosts and syscalls the agent cannot.

A successful clone shows in the audit log as:

```
OCSF NET:OPEN [INFO] ALLOWED /usr/lib/git-core/git-remote-http(…) -> github.com:443 [policy:github_git_clone engine:opa]
OCSF HTTP:GET  [INFO] ALLOWED GET  http://github.com:443/brevdev/workshop-build-an-agent/info/refs      [policy:github_git_clone engine:l7]
OCSF HTTP:POST [INFO] ALLOWED POST http://github.com:443/brevdev/workshop-build-an-agent/git-upload-pack [policy:github_git_clone engine:l7]
```

Denials:

```bash
docker logs "$C" | grep -E "DENIED|NET:FAIL" | tail
```

Each line names the process path and the rule engine — that tells you whether
to add a host rule, a path rule, or a `binaries:` entry (remember symlink
resolution).

Two expected patterns that look like breakage but are not: a boot-time
`python3.13 → github.com:443` DENIED ("binary not allowed in policy
'github_git_clone'") is agent-startup noise — python is deliberately absent
from that block's `binaries`; and curl `000` paired with ALLOWED audit lines
for the same probe is a first-touch proxy flake — retry once before touching
policy.
