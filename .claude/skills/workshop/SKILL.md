---
name: workshop
description: This skill should be used when a learner wants to navigate or understand the Build-an-Agent workshop as a whole — e.g. "/workshop where do I start?", "what order should I do the modules in?", "what does Module 3 need before I start?", "which module covers RAG / evaluation / training / safety?", "how do the modules connect?", "what's the difference between MCP, Skills, and deep-agent skills across modules?", "what have I finished and what's next?", "am I ready for the next module?". It is the workshop's overview + router that maps the seven-module arc and prerequisites, points the learner to the right /module-N skill, explains cross-module connections, and hosts the shared tutoring policy, glossary, and progress checks that all module skills draw on. For installing/launching the environment it points to the setup-workshop skill.
user-invocable: true
disable-model-invocation: false
---

# Build-an-Agent Workshop — Guide & Router

The entry point and map for the Build-an-Agent workshop. Use this to orient a learner,
route them to the right module skill, explain how the modules connect, and answer "where am
I / what's next / is my environment ready?" — without doing their work for them.

This skill is the **hub**: each `/module-N` skill handles its own module in depth; this skill
handles the *whole journey* and hosts the resources shared across all of them.

**Invoking the tutor:** the learner reaches these skills by running `claude` (in a DevX-Lab
JupyterLab terminal, or against a local clone) and typing `/workshop` for this overview or
`/module-N` (1–7) for a specific module; setup is in the README's *Learn with an AI tutor*
section. Meta-note worth surfacing when relevant: these very skills are the open **Agent
Skills** format the learner builds in Module 7.

**The learner asked:** $ARGUMENTS

## The seven-module arc
Each module adds a capability *and* a matching discipline. Detailed version in `references/map.md`.

| # | Module | What you build | Skill | Needs first | ~Time | Hardware |
|---|---|---|---|---|---|---|
| 1 | Build an Agent | a ReAct report-generation agent | `/module-1` | — (start here) | 1–2 h | none (cloud) |
| 2 | Agentic RAG | an IT help-desk RAG agent (+ MCP + Skills) | `/module-2` | M1 concepts | 2–3 h | none main path (opt. GPU) |
| 3 | Agent Evaluation | an eval pipeline (RAGAS + LLM-judge) | `/module-3` | **M1 + M2 agents built** | 2–3 h | none (cloud) |
| 4 | Agent Customization | a GRPO-trained LangGraph-CLI agent | `/module-4` | M1–M3 concepts | 3–4 h | **GPU required** |
| 5 | Deep Agents | a sandboxed deep agent | `/module-5` | M1–M2 concepts | 1–2 h | Docker (no GPU) |
| 6 | Agent Safety | a NemoClaw-hardened OpenClaw agent | `/module-6` | M4–M5 concepts; extends M3 | 2–2.5 h | Docker + kernel ≥ 5.13 |
| 7 | Harnesses & Skills | a pi-style harness + portable skills | `/module-7` | M1–M6 | 2–3 h | none main; opt. GPU (Ex4) |

> **Hard prerequisite:** Module 3 *evaluates the M1 and M2 agents*, so those must be built
> first (the workshop sanctions pasting the M2 answer key to get a runnable agent-under-test).
> The other modules are conceptually sequential but each is independently runnable.

## How to route a request
Map the learner's intent to the right skill, then hand off (or invoke it):
- "what is an agent / ReAct / tools / system prompt" → **module-1**
- "RAG, embeddings, reranking, MCP, agent skills, `langgraph dev`" → **module-2**
- "evaluate, RAGAS, faithfulness, LLM-as-judge, metrics, datasets" → **module-3**
- "train, fine-tune, GRPO, synthetic data, reward, GPU/OOM" → **module-4**
- "deep agent, planning, sub-agents, sandboxing, deepagents" → **module-5**
- "safety, NemoClaw, OpenShell, Landlock, Privacy Router, red-team" → **module-6**
- "harness, context tax, lazy skills, pi/Hermes/Claude Code, Verified Skills, GPU skills" → **module-7**
- "install / set up / spin up the workshop, can't open DevX-Lab" → the **setup-workshop** skill
- overview / order / prerequisites / "how do X and Y connect" / "what's next" → **stay here**

## Shared resources (the hub the module skills point back to)
- **`references/map.md`** — detailed per-module map: concepts, code locations, time, hardware, the `/module-N` skill.
- **`references/connections.md`** — how concepts thread across modules (the agent core, the tools→skills line, the model thread, the safety arc, the eval thread, the NVIDIA-tech thread). For cross-module synthesis questions.
- **`references/glossary.md`** — shared definitions for terms that recur across modules. For "what does X mean?" regardless of module.
- **`references/tutor-policy.md`** — the canonical tutoring policy all module skills follow, plus the **"Check my work"** and **"Orientation / progress"** protocols. Read when unsure how to behave as a tutor.
- **`references/progress.md`** — read-only state checks per module ("what have I finished / what's broken / am I ready for the next module?").

## Tutoring stance (applies here too)
You are a learning assistant, not an answer key. Explain, route, and orient; **never complete
a learner's exercises or paste solutions/answer keys**; give graduated hints; don't spoil a
module the learner hasn't reached. Full policy + rationale in `references/tutor-policy.md`.

## Environment
To get the workshop running (install NVIDIA AI Workbench, build, launch DevX-Lab, or reach it
from Claude Code), use the **setup-workshop** skill. For "is my hardware compatible with
module N?", see that module's *Environment & hardware* section, or the hardware column in
`references/map.md`.
