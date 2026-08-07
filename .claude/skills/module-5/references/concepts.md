# Module 5 Concepts — tutor reference

Answer conceptual questions accurately and in the workshop's voice. For the
authoritative narrative, read the teaching pages in `.devx/5-deep-agents/`. Explaining
concepts is teaching — do it freely.

## Deep agents: the idea (`deep_agents.md`)
A **deep agent** is the same LLM-in-a-loop as a ReAct agent, wrapped in a **middleware
pipeline** that adds planning, filesystem, shell, sub-agents, and context management.
Result: reliable operation across 10–100+ steps and long time horizons (minutes–hours),
where a shallow agent would lose focus or overflow its context. Deep agents *extend*
shallow agents — a deep agent's sub-agents are themselves shallow agents.

## The four pillars
- **Pillar 1 — Explicit Planning.** Shallow agents plan implicitly (in chain-of-thought);
  deep agents keep an external **plan document** (markdown to-dos, status
  pending/in_progress/completed) they review and update between steps. Benefits:
  persistence (survives context pressure), visibility (humans can inspect), adaptability
  (revise on failure instead of looping). Built-in tool: `write_todos`.
- **Pillar 2 — Hierarchical Delegation.** An **orchestrator** decomposes a task and spawns
  **sub-agents** (researcher, coder, analyst…), each with its *own clean context window*;
  only synthesized results return. Solves context overflow + enables specialization.
  Built-in tool: `task`.
- **Pillar 3 — Persistent Memory.** Treat the context window as a *workspace*, not a
  warehouse. State lives in **files** (read/write/edit/ls/glob/grep) and a **checkpointer**;
  **auto-summarization** compresses old messages. The agent "knows where to find
  information" instead of holding it all in context.
- **Pillar 4 — Agent Skills.** Detailed (thousands-of-tokens) markdown **operating
  procedures** injected into the prompt — decision thresholds, tool-usage patterns, error
  recovery, output formats. (Module 4's Superpowers were a taste.) Skills add *expertise*,
  not new tools.

## Shallow vs deep (when to use which)
| | Shallow | Deep |
|---|---|---|
| Planning | implicit | explicit plan docs |
| Delegation | one agent | orchestrator + sub-agents |
| Memory | context window | files + external stores |
| Horizon | 5–15 steps | 10–100+ steps |
| Best for | focused short tasks | complex long-horizon workflows |
Costs of going deep: **latency** (min–hrs), **cost** (more tokens), **complexity**
(harder to test/debug), **coordination** (multi-agent output can be disjointed). Rule of
thumb: *"Could one person do this in one sitting without taking notes?"* If no → deep.
Real-world: deep research (scoping→supervisor→sub-agents→compression→report), coding
agents (Claude Code, Cursor).

## The deepagents library
`create_deep_agent(model, tools, system_prompt, backend, checkpointer, subagents, skills,
interrupt_on)` returns a compiled **LangGraph** graph with a **middleware stack** —
"batteries included." Built-in capabilities: **planning** (`write_todos`), **filesystem**
(`ls/glob/grep/read_file/write_file/edit_file`), **shell** (`execute`), **sub-agents**
(`task`), **context management** (auto-summarization). Extend with **MCP tools**
(`MultiServerMCPClient`) and **skills** (`.md` files via the `skills=` arg). In this module:
- **Models** (`MODEL_MAP` → `ChatNVIDIA`, temp 0.3): `nemotron`→nemotron-3-super-120b-a12b,
  `llama`→llama-3.3-70b-instruct, `deepseek`→deepseek-r1-0528, `claude`→llama fallback.
- **HITL:** `interrupt_on=INTERRUPT_TOOLS` = `{write_file, edit_file, execute}` — those
  tools pause for human approve/edit/reject.
- **Workspace:** `/tmp/deepagent_workspace` locally (seeded with fake demo secrets),
  `/workspace` inside a Docker sandbox. File tools require **absolute** paths.

## Backends (the execution boundary)
The **backend** decides where file ops and shell commands run — and is the sandboxing
lever:
- `FilesystemBackend(root_dir=...)` — file ops only (read/write/edit/ls/glob/grep).
- `LocalShellBackend(root_dir=..., timeout, max_output_bytes, inherit_env)` — files **plus**
  shell `execute` on the **host** workspace (extends FilesystemBackend).
- `DockerSandboxBackend()` — everything runs inside an isolated Docker container
  (python:3.11-slim, **no host mounts**, 512 MB, 1 CPU, auto-cleanup). Implements
  `SandboxBackendProtocol` so all tools work transparently.

## Why security matters more here (`sandboxing_security.md`)
Three amplifiers vs shallow agents: **extended autonomy** (runs for minutes–hours
unattended), **code execution** (shell/files/installs/subprocesses), **cascading effects**
(one sub-agent's error propagates). **Key principle:** *once an agent passes control to a
subprocess, only OS-level enforcement can ensure containment* — prompt rules ("don't
delete files") are bypassed by subprocesses and hallucinated past. The no-sandbox demo:
the agent runs `ls /tmp/deepagent_workspace` and reads `passwords.txt`; sandboxed, the
container is empty (no host mounts). What can go wrong: destructive commands, supply-chain
(hallucinated malicious package), data exfiltration, resource exhaustion.

## The security spectrum & patterns
Isolation strength: **prompt-only** (dev only) → **Deno** → **Bubblewrap/Seatbelt** (Claude
Code local) → **Docker + seccomp** (most production) → **gVisor** → **Firecracker VM**
(max). Sandbox **patterns**: *Agent IN Sandbox* (agent runs inside; keys live inside — risky)
vs ***Sandbox-as-Tool*** (agent runs locally, delegates execution to a remote/Docker
sandbox; keys stay out; instant updates; parallel; failures isolated). **deepagents uses
Sandbox-as-Tool with Docker.** Choose isolation by **threat model**: who controls inputs,
what data is reachable, does it execute code, what's the blast radius.

## Defense in depth & principles
Six overlapping layers (assume any one fails): **HITL** → **permission allowlists** →
**application sandboxing** → **container/VM isolation** → **network controls** (default-deny
egress) → **audit logging**. Security principles: **trust the sandbox, not the model**
(deepagents follows a "trust the LLM" model — enforce at the tool/sandbox level), **least
privilege**, **credential isolation** (keys never reachable by the agent), **audit
everything** (LangSmith), **rate limiting** (recursion/timeout caps), **adversarial
testing** (probe before deploy), **environment separation**.

## Source map
- Concepts → `intro_deep_agents.md`, `deep_agents.md`
- Build → `build_deep_agents.md` + `code/5-deep-agents/deep_agent.py` (mirror: `demo/backend/agent.py`)
- Security → `sandboxing_security.md`
