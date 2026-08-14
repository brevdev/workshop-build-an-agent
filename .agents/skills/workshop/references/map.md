# Workshop Module Map — tutor reference

The detailed map for routing and orientation. Each entry: what the learner builds, the key
concepts, where the code lives, the dedicated skill, prerequisites, time, and hardware.
Teaching narrative for module N is in `.devx/<N>-<slug>/`; code in `code/<N>-<slug>/`.

## Module 1 — Build an Agent  (`$module-1`, `1-build-an-agent`)
- **Build:** a ReAct Report-Generation agent (researches a topic, writes a cited report).
- **Concepts:** the four components (model/tools/memory/routing), the agentic loop, ReAct,
  system prompts, "tool calling = menu not kitchen."
- **Code:** `intro_to_agents.ipynb` (from scratch), `docgen_client.ipynb`, `docgen_agent.py`, `tools.py`.
- **Prereq:** none — **start here.**  **Time:** 1–2 h.  **Hardware:** none (hosted Nemotron + Tavily).

## Module 2 — Agentic RAG  (`$module-2`, `2-agentic-rag`)
- **Build:** an IT Help-Desk agentic-RAG agent; add web search via MCP and dynamically loaded Skills.
- **Concepts:** chunk/embed/insert, FAISS, reranking, retrieval-as-a-tool, MCP, Agent Skills, local-NIM migration.
- **Code:** `rag_agent.py` (+ `.answers.py`), `mcp_server.py`, `simple_client.py`; run with `langgraph dev`.
- **Prereq:** M1 concepts (ReAct).  **Time:** 2–3 h.  **Hardware:** none for the main path; the optional "Migrate to Local NIM" step needs Docker + a GPU.

## Module 3 — Agent Evaluation  (`$module-3`, `3-agent-evaluation`)
- **Build:** an evaluation pipeline for the M1 + M2 agents (RAGAS + LLM-as-judge + custom metrics + a continuous suite).
- **Concepts:** retrieval-vs-generation 2×2, RAGAS metrics + score bands, the judge problem + calibration, dataset design (SDG), the improvement cycle.
- **Code:** `evaluation_framework.py`, `evaluate_{rag,report}_agent.ipynb`, `generate_*_eval_dataset.ipynb`.
- **Prereq:** **M1 + M2 agents must be built** (it evaluates them).  **Time:** 2–3 h.  **Hardware:** none (all hosted; some steps are slow but CPU/network-bound).

## Module 4 — Agent Customization  (`$module-4`, `4-agent-customization`)
- **Build:** customize a bash agent into a LangGraph-CLI expert via SDG → reward → GRPO training.
- **Concepts:** train-vs-prompt-vs-tools, SFT vs GRPO, SDG (NeMo Data Designer), RLVR (NeMo Gym), reward engineering, HITL.
- **Code:** `bash_agent.ipynb`, `01_synthetic_data_generation.ipynb`, `02_grpo_training.ipynb`, `03_run_agent.ipynb` (+ `answer_key/`).
- **Prereq:** M1–M3 concepts.  **Time:** 3–4 h.  **Hardware:** **GPU required** (A100/H100 80 GB ideal; GB10 works but slow); Docker + CUDA build. SDG is GPU-free.

## Module 5 — Deep Agents  (`$module-5`, `5-deep-agents`)
- **Build:** a production deep agent (planning, delegation, memory, skills) with Docker sandboxing.
- **Concepts:** the four pillars, shallow vs deep, the deepagents middleware, backends, the security spectrum + patterns, defense in depth.
- **Code:** `deep_agent.py` (+ `.answers.py`); runs via the demo backend + Deep Agents Client.
- **Prereq:** M1–M2 concepts.  **Time:** 1–2 h.  **Hardware:** Docker (for the sandbox backend); no GPU (hosted inference).

## Module 6 — Agent Safety  (`$module-6`, `6-agent-safety`)
- **Build:** harden an OpenClaw agent with NVIDIA NemoClaw — kernel enforcement (Landlock/seccomp/network proxy), operator-controlled inference routing, and a red-team + LLM-judge safety suite.
- **Concepts:** why app/container controls aren't enough for autonomous agents, the four enforcement layers, the operator role, the Privacy Router (operator routing + credential injection, **not** content classification), defense in depth, safety evaluation.
- **Code:** `agent_safety.py` / `.ipynb`, `safety_eval_framework.py`, the NemoClaw wrappers, `policies/*.yaml`, `scripts/`.
- **Prereq:** M4 (HITL) + M5 (sandboxing) concepts; extends M3's eval framework.  **Time:** 2–2.5 h.  **Hardware:** Docker + Linux kernel ≥ 5.13 for the live stack; no GPU on the main path (the Python eval sidekicks run on the mock agent even if the live control plane is down).

## Module 7 — Agent Harnesses & Skills  (`$module-7`, `7-agent-harnesses`)
- **Build:** a minimal pi-style harness (4 tools + a loop) around Nemotron, a context-tax meter, a hand-authored portable Agent Skill, a GPU-accelerated NVIDIA Verified Skill (cuDF), and a self-evolving harness.
- **Concepts:** harness vs LLM (engine/car), the five harness responsibilities, the context tax + lazy skill loading, the seven-harness landscape, the open Agent Skills spec, NVIDIA Verified Skills, GPU skills.
- **Code:** `harness_lab.py` / `.ipynb` (5 exercises — `build_bare_agent`, `harness_overhead`, `load_skills_lazily`, `self_evolve_skill`, + author a `SKILL.md`) (+ `.answers.*`); `scripts/install_nvidia_skill.sh`.
- **Prereq:** M1–M6 concepts — the **capstone**; it names the harness layer used in every prior module.  **Time:** 2–3 h.  **Hardware:** none for the main path (hosted Nemotron + `tiktoken`, CPU); **Exercise 4's GPU speedup needs an NVIDIA GPU** (cuDF) — clean fallback + skip message without one.

## Module 8 — Agent Routing  (`$module-8`, `8-agent-routing`)
- **Build:** a metered, routed agent — a bill meter on every call, a hand-written classifier router, Switchyard's in-process `stage_router`, a `routes.toml` gateway the app never reads, and a scoreboard — plus the **Routing Client** tile that comes alive panel by panel (`systems online: 0/5 → 5/5`).
- **Concepts:** **tokenomics** (price vs M7's cost), the frontier-vs-open false binary → *use both, efficiently*, the model **portfolio**, the routing taxonomy (`passthrough`/`random`/`llm_classifier`/`stage_router`/escalation mode/learned), the **router tax**, capability vs escalation mode, session affinity, policy-vs-performance routing (M6's Privacy Router is **not** content classification), NeMo Switchyard's three nouns + three surfaces, the Pareto/cost-accuracy trade.
- **Code:** `routing_lab.py` / `.ipynb` (7 blanks across 5 exercises — `build_model_pool` 1a, `bill_call` 1b, `classify_difficulty` 2a, `route_call` 2b, `make_lab_router` 3a, `switchyard_call` 3b, `routing_verdict` 5) (+ `.answers.*`); `constants.py`, `switchyard_shim.py` (the **only** SDK import), `routes.toml.template` (+ `.answers`), `test_data/routing_tasks.jsonl`, `scripts/{install_switchyard,serve_gateway,serve_local_nim,smoke_switchyard}.sh`, `routing_client/`.
- **Prereq:** M1 + M7 concepts (the four components; the harness/loop that emits the tool signals a stage router reads); M2's local-NIM runbook only for the optional Ex4b. **Time:** 2–3 h (the lab itself ~95 min).  **Hardware:** none for the main path (hosted Nemotron, CPU, `NVIDIA_API_KEY` only — Ex4's gateway is a localhost process); **Ex4b optional: Docker + an NVIDIA GPU** (skip it — 4a is the full exercise). Spends real money: ~150 live calls, cents.

## Routing shorthand
RAG → M2 · evaluation/metrics → M3 · training/GRPO/GPU → M4 · deep agents/planning/sandbox → M5 ·
safety/NemoClaw/kernel → M6 · harnesses/skills/context-tax/Verified-Skills → M7 ·
model routing/switchyard/tokenomics/cost → M8 · install/launch → setup-workshop · overview/order/connections → this skill.
