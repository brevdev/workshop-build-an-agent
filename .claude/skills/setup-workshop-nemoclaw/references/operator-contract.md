# Operator contract — what the host side provides, and how to ask for it

You (the in-sandbox agent) cannot change egress policy, write secrets safely,
or open the inbound path. The **operator** (a human, or an agent on the
sandbox host following the `setup-workshop-nemoclaw-operator` skill) does.
This file is the contract between the two sides: what must be true before
setup, how to verify it from inside, and the exact messages to send when
something is missing. Never guess at policy state — probe, then ask precisely.

## What the operator must provide (verify each from inside)

| # | Requirement | In-sandbox probe | Expected |
|---|---|---|---|
| 1 | PyPI egress (`GET pypi.org` + `files.pythonhosted.org`) | `curl -sS -m 15 -o /dev/null -w '%{http_code}' https://pypi.org/simple/` | `200` (403/000 = blocked) |
| 2 | NIM chat/embeddings routes | `curl -sS -m 15 -o /dev/null -w '%{http_code}' https://integrate.api.nvidia.com/v1/models` | `200` |
| 2b | Reranker route (modules 2/3) — `POST /v1/retrieval/**` on `ai.api.nvidia.com` (⚠️ NOT the legacy `/v1/ranking`) | authed rerank POST (see preflight.sh 5b) | `200` |
| 2c | Integrations: `api.tavily.com` (mods 1/2/5), `api.smith.langchain.com` (mod 3 + tracing), `openaipublic.blob.core.windows.net` (mod 7 tiktoken) | preflight.sh 5b probes | `200` each |
| 3 | ~~NVIDIA key staged~~ — **NOT a prerequisite.** Expected absent; the learner sets it in the Secrets Manager tile after launch (preflight only WARNs) | `grep -q '^NVIDIA_API_KEY=' /sandbox/workshop-build-an-agent/secrets.env` | either result is fine |
| 4 | (only if repo missing) git smart-HTTP for the scoped repo | `curl -sS -m 20 -o /dev/null -w '%{http_code}' 'https://github.com/brevdev/workshop-build-an-agent.git/info/refs?service=git-upload-pack'` | `200` |
| 5 | (optional — Terminal tile) rw `/dev/pts` in `filesystem_policy` | `python3 -c 'import os; os.openpty()'` | exit 0 (`EACCES` = grant missing) |
| 6 | Inbound path (per session, AFTER launch) | n/a — operator runs the forward | HTTP 302 on host `127.0.0.1:8888/lab` |

`scripts/preflight.sh` runs probes 1–5 (5 is non-blocking: setup proceeds
with the Terminal tile disabled) and prints the matching asks below.
Curl inside the sandbox already trusts the proxy CA; only uv/pip need
`SSL_CERT_FILE=/etc/openshell-tls/ca-bundle.pem` exported.

`build.nvidia.com` is **not** needed — it appears only in notebook prose. All
model calls (`ChatNVIDIA`/`NVIDIAEmbeddings`/`NVIDIARerank`) go to
`integrate.api.nvidia.com`.

## Message templates (send verbatim, then STOP and wait)

Keep asks specific: the operator's own tooling (e.g. Claude Code's permission
layer) will only let an agent apply egress changes the human explicitly named,
so name hosts and paths exactly.

**PyPI / ranking policy missing (probes 1–2 fail):**

> Setup is blocked on sandbox egress policy. Please apply (or have your
> host-side agent stage via the `setup-workshop-nemoclaw-operator` skill) a
> policy adding: read-only `GET` to `pypi.org` and `files.pythonhosted.org`
> for uv/python binaries, and `POST /v1/ranking` on the NIM hosts
> (`integrate.api.nvidia.com` + mirror). ⚠️ `openshell policy set` REPLACES
> the whole policy document — apply a full-union file, never a fragment.
> Signal it worked: my `curl https://pypi.org/simple/` returns 200. Ping me
> "try now" and I'll re-verify and continue automatically.

**secrets.env has no NVIDIA_API_KEY (probe 3 warns):**

Do **not** send an ask for this — it is the expected default. Tell the *user*
instead: open the **Secrets Manager** tile in the JupyterLab launcher, set
`NVIDIA API Key` to a `nvapi-…` key from build.nvidia.com, then re-run the
notebook cells. No JupyterLab restart is needed, because the variable was
absent from the server env at launch and `load_dotenv()` therefore reads the
file fresh on every cell run.

Only if the operator explicitly wants a key baked into an unattended image:

> Please pre-seed the key from the host (never through chat) with the operator
> skill's `stage-nvidia-key.sh` — pass a genuine `nvapi-…` key. ⚠️ Do NOT reuse
> `COMPATIBLE_API_KEY`/`OPENAI_API_KEY` from the NemoClaw project `.env`: that
> is the agent's own `sk-…` host-proxy credential, and staging it yields a
> `secrets.env` that looks populated while every notebook fails with
> `AuthenticationError: 401` against `integrate.api.nvidia.com`. After
> pre-seeding, re-run `start-jupyter.sh` so kernels pick it up.

**Repo missing and clone blocked (probe 4 fails):**

> The workshop repo isn't at `/sandbox/workshop-build-an-agent` and github.com
> git smart-HTTP is blocked. Please add the `github_git_clone` policy block
> (GET `/brevdev/workshop-build-an-agent{,.git}/info/refs` + POST
> `…/git-upload-pack` on github.com:443, binaries `/usr/bin/git` +
> `/usr/lib/git-core/git-remote-http{,s}`), then ping me — I'll run
> `git clone --branch edwli-dev https://github.com/brevdev/workshop-build-an-agent /sandbox/workshop-build-an-agent`.

**Terminal tile wanted but PTY denied (probe 5 fails):**

> JupyterLab's Terminal needs PTY devices, which the sandbox Landlock policy
> currently denies. Please make sure `/dev/pts` is in
> `filesystem_policy.read_write` of the APPLIED live policy (the operator
> skill's Phase 1 includes it), then run that skill's Phase 1b
> recreate-from-live — do not edit the deployment recipe's template.
> Note it only takes effect at a sandbox
> **recreate** — filesystem policy is parsed at container boot; a live
> `policy set` won't activate it even for new processes (network rules
> hot-reload, fs rules don't). After the recreate I'll re-run setup and
> terminals come up enabled automatically. Signal it worked:
> `python3 -c 'import os; os.openpty()'` exits 0 in the new sandbox.

**After a failed install / NIM call despite policy supposedly applied:**

> Still blocked (had: `<exact error line>`). Please check the audit log on the
> host — `docker logs <container> | grep -E 'DENIED|NET:FAIL' | tail` — and
> tell me the process path + rule it names; I'll adjust my approach or you may
> need one more policy rule.

Common causes worth suggesting: the apply wasn't run / not `--wait`ed; a
different container/profile was targeted (host check:
`docker exec <c> ls /sandbox/workshop-build-an-agent/secrets.env`); the policy
file applied was stale and silently reverted other blocks.

## Integrations (Tavily / LangSmith) — standard for full module coverage

The operator appends `TAVILY_API_KEY=` / `LANGSMITH_API_KEY=` lines to the
same `secrets.env` **and** ensures the `tavily_search` (`api.tavily.com` —
NOT `mcp.tavily.com`, which is the remote-MCP host and would also need npm)
and `langsmith_api` (`api.smith.langchain.com`) policy blocks are live (see
the operator skill's policy-blocks.md; both ship in the community example's
template). Without the Tavily key/route, agents still run but silently write
no-search reports; without the LangSmith route, every notebook spams tracing
retry errors because `variables.env` enables tracing globally.

Module-2 note: use the module's LOCAL MCP server (`rag_agent.py` PART 2B +
`uvicorn mcp_server:app --port 8000`) — the shipped PART 2A remote-MCP path
needs `npx` to download `mcp-remote` from the blocked npm registry, and its
retry backoff hangs agent tool calls for minutes.

## What to report when setup completes

1. The token URL location: `/sandbox/workshop-url.txt` (the token itself is
   redacted in your chat output — that's why the file exists). Host-side read:
   `docker exec <container> cat /sandbox/workshop-url.txt`.
2. The two access commands (see SKILL.md "Report back to the user").
3. State restrictions honestly: modules 1–3 + clients work; modules 4 & 6
   need a GPU and do not run here; Tavily/LangSmith optional and off unless
   staged.

## If the operator relays wrong guidance

It has happened: an early relay said to use
`SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`, which broke uv. Trust
your own probes over relayed environment claims — verify, correct politely,
and report the correction back so the operator's notes get fixed too.
