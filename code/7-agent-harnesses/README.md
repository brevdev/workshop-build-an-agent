# Module 7 — Hermes, a glass-box agent harness

Hermes is a small, zero-framework agent harness you build by hand to answer the
module's question: **if the model is the same, what makes the agent different?**
It talks to the same NVIDIA endpoint as Module 1, but over raw `urllib` HTTP so
every byte is visible — and so the exact same code runs inside Module 6's
sandbox, where only Python's standard library is guaranteed.

Work through the exercises in `../.devx/7-agent-harnesses` (the launcher tile
**"7. Agent Harnesses"**). This README is the quick reference.

## Layout

```
hermes/            the package you complete (TODOs marked # TODO: Exercise N)
  client.py        Ex1  raw HTTP to the model (the "wire")
  harness.py       Ex1+3  the loop, the REPL, tool dispatch
  context.py       Ex2  system-prompt assembly, token budget, compaction
  state.py         Ex2  MEMORY.md persistence
  tools.py         Ex3  tool registry, schemas, dispatch
  gates.py         Ex3  human-in-the-loop permission gate
  config.py        all the knobs (provided)
  HERMES.md        the soul file (provided; edit it to change Hermes' persona)
answer_key/        a complete, runnable copy — peek if you get stuck
faceoff.py         Ex4  same probes vs bare model / Hermes / OpenClaw
policies/          Ex5  hermes-sandbox.yaml (OpenShell policy)
sandbox/           Ex5  upload_hermes.sh helper
```

## Running it

| What | Command (run from `code/7-agent-harnesses/`) |
|------|----------------------------------------------|
| Chat (REPL) | `python3 -m hermes` |
| One message | `python3 -m hermes --once "hello"` |
| Skip the y/N gate | `python3 -m hermes --auto-approve` |
| Watch compaction | `HERMES_BUDGET=500 python3 -m hermes` then chat a few turns |
| Run the completed version | `cd answer_key && python3 -m hermes` |
| The face-off | `python3 faceoff.py` |

REPL commands: `/quit` `/remember <text>` `/memory` `/context` `/history`.

Environment variables (all optional): `HERMES_BASE_URL`, `HERMES_MODEL`,
`HERMES_BUDGET`, `HERMES_AUTO_APPROVE=1`, `HERMES_TLS_INSECURE=1` (sandbox-only
fallback if the gateway CA is missing — see Exercise 5).

## Exercise 5 — into the sandbox

```bash
# 1. apply the policy (revokes Module 6's httpbin rule — that's the demo)
openshell policy set my-assistant --policy code/7-agent-harnesses/policies/hermes-sandbox.yaml --wait
# 2. upload Hermes (+ keyless smoke test)
bash code/7-agent-harnesses/sandbox/upload_hermes.sh            # or --answers
# 3. interactive REPL inside the sandbox
openshell sandbox connect my-assistant     # or: nemoclaw my-assistant connect
#    then: cd /sandbox/hermes && export HERMES_BASE_URL=https://inference.local/v1 && python3 -m hermes
```

Inside the sandbox there is no `NVIDIA_API_KEY` — the Privacy Router gateway
injects the operator's credentials. Ask Hermes to `fetch_url https://httpbin.org/ip`
and approve the gate: the kernel still refuses the egress. The harness asks; the
kernel enforces.

## Stretch goal

Add a `run_shell` tool (dangerous, gated). For a safe pattern, study Module 4's
allowlisted executor at `code/4-agent-customization/bash_agent/bash.py`.
