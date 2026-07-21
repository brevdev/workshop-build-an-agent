# Policy blocks — exact YAML, apply semantics, verification

Everything here was verified live against OpenShell v0.0.53 (gateway as a user
systemd unit `openshell-gateway.service`; L7 proxy + OCSF audit log via
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
- In the NemoClaw community example, keep **both** files in sync with any
  change: `policy.yaml` (template — re-rendered at sandbox recreate) and
  `policy.hermes-direct.yaml` (live capture). Template drift = silent
  reversion at the next recreate.
- OpenShell ≥ 0.0.53 also ships `openshell policy update` for incremental
  changes — prefer it for one-block additions if available.

## Minimal-delta workflow (what an agent should stage for the human)

```bash
openshell policy get "$SANDBOX" --full > /tmp/live.yaml
# 1. Copy /tmp/live.yaml -> /tmp/apply.yaml; append ONLY the new blocks below.
# 2. Structural check (e.g. python+yaml): block names in apply.yaml ==
#    block names in live.yaml + the additions; nothing else differs.
# 3. Hand the human:  openshell policy set "$SANDBOX" --policy /tmp/apply.yaml --wait
#    with a one-line statement of exactly what it opens.
```

This matters because an agent-run `policy set` is usually (correctly) blocked
by the operator's permission layer, and because building from the LIVE policy
avoids re-applying unrelated grants the human didn't ask to restore.

## The blocks

Add under `network_policies:`. Copies of the blocks running in the NemoClaw
community example; adjust the repo slug if the workshop repo differs.

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
sandboxes should carry all four (they ship in the community example's
`policy.yaml` template). Binaries: same python/curl set as `pypi_install`
minus uv.

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
lines: the rw count won't change on a live apply). Put `/dev/pts` in the
TEMPLATE and recreate the sandbox; after the recreate, `start-jupyter.sh`
auto-detects working PTYs and enables the Terminal tile. No restart shortcut
exists (`docker restart` = stale-bootstrap-JWT crash loop).

## What NOT to open

- `build.nvidia.com` — not needed; it appears only in notebook prose. Chat/
  completions/embeddings hit `integrate.api.nvidia.com`; reranking hits
  `ai.api.nvidia.com` (block above).
- `registry.npmjs.org` + `mcp.tavily.com` — module-2's shipped remote-MCP
  `web_search` path (`npx -y mcp-remote …`). Use the module's LOCAL MCP
  server instead (PART 2B in `rag_agent.py`; deps already pinned) — only
  `api.tavily.com` is needed, and npm's retry backoff otherwise hangs agent
  tool calls for minutes.
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
