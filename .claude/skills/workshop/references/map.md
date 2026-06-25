# Workshop Module Map — tutor reference

The detailed map for routing and orientation. Each entry: what the learner builds, the key
concepts, where the code lives, the dedicated skill, prerequisites, time, and hardware.
Teaching narrative for module N is in `.devx/<N>-<slug>/`; code in `code/<N>-<slug>/`.

## Module 1 — Build an Agent  (`/module-1`, `1-build-an-agent`)
- **Build:** a ReAct Report-Generation agent (researches a topic, writes a cited report).
- **Concepts:** the four components (model/tools/memory/routing), the agentic loop, ReAct,
  system prompts, "tool calling = menu not kitchen."
- **Code:** `intro_to_agents.ipynb` (from scratch), `docgen_client.ipynb`, `docgen_agent.py`, `tools.py`.
- **Prereq:** none — **start here.**  **Time:** 1–2 h.  **Hardware:** none (hosted Nemotron + Tavily).

## Module 2 — Agentic RAG  (`/module-2`, `2-agentic-rag`)
- **Build:** an IT Help-Desk agentic-RAG agent; add web search via MCP and dynamically loaded Skills.
- **Concepts:** chunk/embed/insert, FAISS, reranking, retrieval-as-a-tool, MCP, Agent Skills, local-NIM migration.
- **Code:** `rag_agent.py` (+ `.answers.py`), `mcp_server.py`, `simple_client.py`; run with `langgraph dev`.
- **Prereq:** M1 concepts (ReAct).  **Time:** 2–3 h.  **Hardware:** none for the main path; the optional "Migrate to Local NIM" step needs Docker + a GPU.

## Module 3 — Agent Evaluation  (`/module-3`, `3-agent-evaluation`)
- **Build:** an evaluation pipeline for the M1 + M2 agents (RAGAS + LLM-as-judge + custom metrics + a continuous suite).
- **Concepts:** retrieval-vs-generation 2×2, RAGAS metrics + score bands, the judge problem + calibration, dataset design (SDG), the improvement cycle.
- **Code:** `evaluation_framework.py`, `evaluate_{rag,report}_agent.ipynb`, `generate_*_eval_dataset.ipynb`.
- **Prereq:** **M1 + M2 agents must be built** (it evaluates them).  **Time:** 2–3 h.  **Hardware:** none (all hosted; some steps are slow but CPU/network-bound).

## Module 4 — Agent Customization  (`/module-4`, `4-agent-customization`)
- **Build:** customize a bash agent into a LangGraph-CLI expert via SDG → reward → GRPO training.
- **Concepts:** train-vs-prompt-vs-tools, SFT vs GRPO, SDG (NeMo Data Designer), RLVR (NeMo Gym), reward engineering, HITL.
- **Code:** `bash_agent.ipynb`, `01_synthetic_data_generation.ipynb`, `02_grpo_training.ipynb`, `03_run_agent.ipynb` (+ `answer_key/`).
- **Prereq:** M1–M3 concepts.  **Time:** 3–4 h.  **Hardware:** **GPU required** (A100/H100 80 GB ideal; GB10 works but slow); Docker + CUDA build. SDG is GPU-free.

## Module 5 — Deep Agents  (`/module-5`, `5-deep-agents`)
- **Build:** a production deep agent (planning, delegation, memory, skills) with Docker sandboxing.
- **Concepts:** the four pillars, shallow vs deep, the deepagents middleware, backends, the security spectrum + patterns, defense in depth.
- **Code:** `deep_agent.py` (+ `.answers.py`); runs via the demo backend + Deep Agents Client.
- **Prereq:** M1–M2 concepts.  **Time:** 1–2 h.  **Hardware:** Docker (for the sandbox backend); no GPU (hosted inference).

## Module 6 — Agent Safety  (`/module-6`, `6-agent-safety`)
- **Build:** harden an OpenClaw agent with NVIDIA NemoClaw — kernel enforcement (Landlock/seccomp/network proxy), operator-controlled inference routing, and a red-team + LLM-judge safety suite.
- **Concepts:** why app/container controls aren't enough for autonomous agents, the four enforcement layers, the operator role, the Privacy Router (operator routing + credential injection, **not** content classification), defense in depth, safety evaluation.
- **Code:** `agent_safety.py` / `.ipynb`, `safety_eval_framework.py`, the NemoClaw wrappers, `policies/*.yaml`, `scripts/`.
- **Prereq:** M4 (HITL) + M5 (sandboxing) concepts; extends M3's eval framework.  **Time:** 2–2.5 h.  **Hardware:** Docker + Linux kernel ≥ 5.13 for the live stack; no GPU on the main path (the Python eval sidekicks run on the mock agent even if the live control plane is down).

## Module 7 — Agent Harnesses & Skills  (*pending — not yet built*)
- **Build (planned):** a minimal pi-style harness from scratch, a context-tax measurement suite, and a portable Agent Skill that runs unchanged across harnesses; a GPU-accelerated NVIDIA Verified Skill.
- **Concepts (planned):** harness vs LLM separation, the context tax + lazy skill loading, the open Agent Skills spec, NVIDIA Verified Skills.
- **Note:** the `/module-7` skill is not built yet — say so and point to the module's `.devx/7-agent-harnesses/` content if asked.

## Routing shorthand
RAG → M2 · evaluation/metrics → M3 · training/GRPO/GPU → M4 · deep agents/planning/sandbox → M5 ·
safety/NemoClaw/kernel → M6 · install/launch → setup-workshop · overview/order/connections → this skill.
