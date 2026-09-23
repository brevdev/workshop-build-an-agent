# Workshop Glossary — tutor reference

Shared definitions for terms that recur across modules. Use for "what does X mean?"
regardless of which module the learner is in. Each entry is a 1–2 line working definition +
where it's central; for depth, see that module's `concepts.md`.

## Agent fundamentals (M1)
- **Agent** — an LLM in a loop that *chooses* what to do (which tool, or to answer), vs a fixed chain.
- **ReAct** — Reason→Act→Observe loop; the most common agent architecture. Central M1; recurs everywhere.
- **Agentic loop** — give the model input + tools → it responds or requests a tool → run the tool, append result, repeat.
- **Tool / tool calling** — a function the model *requests* (name + args); **your code runs it** ("the menu, not the kitchen"). The model never executes code.
- **System prompt** — the message defining the agent's role, constraints, and when to use tools.
- **Memory / state** — short-term = the conversation log; long-term = external stores (DBs/files). M1 uses short-term; M5 adds files.
- **Routing** — the control logic orchestrating the loop (written by hand in M1; framework-handled by `create_*_agent`).

## RAG & retrieval (M2)
- **RAG** — Retrieval-Augmented Generation: fetch relevant docs, then generate with them as context.
- **Agentic RAG** — retrieval exposed as a *tool* the model calls *when needed* (vs traditional RAG's always-retrieve fixed path).
- **Chunking** — splitting docs into overlapping pieces (`RecursiveCharacterTextSplitter`, size 800 / overlap 120).
- **Embedding** — text → vector; similar meaning → nearby vectors. NVIDIAEmbeddings.
- **Vector DB / FAISS** — stores vectors for similarity search (FAISS = Meta's in-memory lib).
- **Reranking** — reorders retrieved candidates by true relevance (embeddings get you *close*; rerank gets the *order* right). NVIDIARerank.
- **NeMo Retriever** — NVIDIA's embedding + reranking model family (`llama-nemotron-embed/rerank-1b-v2`).
- **MCP (Model Context Protocol)** — an open standard (Anthropic) for connecting agents to external tool *servers*; tools run on the server.
- **Agent Skill** — a folder/`.md` of *instructions* (know-how) loaded on demand; complements MCP (tools).

## Evaluation (M3)
- **LLM-as-a-judge** — using an LLM (Nemotron, temp 0) to score outputs against a rubric.
- **Faithfulness** — are the answer's claims grounded in the retrieved context (no hallucination)? (generation)
- **Answer Relevancy** — does the answer address the question (regardless of grounding)? (generation)
- **Context Precision / Recall** — are retrieved chunks relevant & well-ranked / was everything needed retrieved? (retrieval)
- **RAGAS** — open-source RAG-eval framework providing those four metrics (scored 0–1).
- **Calibration** — checking that the judge agrees with human ratings on a sample.
- **SDG (Synthetic Data Generation)** — generating test/training data programmatically (NeMo Data Designer).

## Customization & training (M4)
- **SFT** — Supervised Fine-Tuning: memorize given input→output pairs.
- **GRPO** — Group Relative Policy Optimization: generate several candidates, score each, reinforce the above-average ones (RL).
- **RLVR** — Reinforcement Learning with Verifiable Rewards: rewards from *code* checks, not an LLM judge.
- **NeMo Gym** — NVIDIA's reward/environment framework; here the `/verify` reward server.
- **NeMo Data Designer** — NVIDIA's schema-first SDG tool.
- **Reward hacking** — the model maximizes the reward via a shortcut without doing the task (e.g. empty `{}` scoring 1.0).
- **LoRA / PEFT** — parameter-efficient fine-tuning (train small adapters, not all weights).
- **HITL (human-in-the-loop)** — a human approves an action before it executes.

## Deep agents (M5)
- **Deep agent** — a ReAct agent + a middleware pipeline (planning, delegation, memory, skills) for long-horizon tasks.
- **The four pillars** — Planning (`write_todos`), Delegation (sub-agents via `task`), Memory (filesystem + checkpointer), Skills (`.md` procedures).
- **Orchestrator / sub-agent** — the planner delegates sub-tasks to specialized sub-agents with isolated context.
- **Backend** — where file/shell ops run: `FilesystemBackend` (files) / `LocalShellBackend` (+ shell) / `DockerSandboxBackend` (isolated).
- **Sandbox** — an isolated environment (here a Docker container, no host mounts) where agent code can't harm the host.

## Safety (M6)
- **Operator** — the human with host access to the OpenShell gateway: configures providers, sets the backend, applies policies. (vs the **agent** in the sandbox, vs the **end user**.)
- **NemoClaw** — NVIDIA's reference stack (OpenClaw + OpenShell + Nemotron + Privacy Router).
- **OpenClaw** — the open, config-first autonomous agent framework NemoClaw wraps (not NVIDIA).
- **OpenShell** — NVIDIA's kernel-level sandbox runtime (enforces the four layers).
- **Landlock LSM** — Linux kernel module (≥5.13) for per-path filesystem rules; irrevocable by design.
- **seccomp BPF** — Linux kernel syscall filtering; drops dangerous syscalls.
- **Privacy Router** — OpenShell's inference gateway: enforces the **operator's chosen backend** + injects credentials. **Not** content classification.
- **Defense in depth** — multiple independent layers so an attacker must defeat all of them.
- **Red-team probe** — an adversarial input crafted to trigger unsafe behavior.

## Harnesses & skills (M7)
- **Harness** — the layer *around* the LLM: memory, tool execution, planning, the loop, the token budget. The model is stateless; the harness is everything else. Every M1–M6 agent ran in one (named retroactively in M7).
- **Context tax** — the recurring per-turn token overhead (system prompt + tool schemas + skill descriptions) paid on *every* model call; the axis that sorts harnesses (minimal <1k → maximal 7–10k).
- **Lazy skill loading** — keeping each skill as a one-line `name: description` until invoked, loading the full body only on demand (pi's design; the main context-tax cut).
- **Agent Skills spec** — the open format ([agentskills.io](https://agentskills.io)): one `SKILL.md` that runs unchanged across harnesses (OpenClaw, Hermes, Claude Code, Codex, Cursor…). See also **Agent Skill** (M2).
- **NVIDIA Verified Skills** — signed, security-scanned skills (`github.com/NVIDIA/skills`) teaching agents to use NVIDIA software (cuDF, cuOpt, NeMo…); capability governance via SkillSpector, skill cards, and OpenSSF Model Signing.
- **The harness landscape** — pi (minimal) · OpenCode · LangChain Deep Agents · Hermes (curated, the M7 lab harness) · OpenClaw (maximal, M6) · Claude Code / Codex (subscription, maximal).

## Model routing & economics (M8)
- **Tokenomics** — the unit economics of LLM work: dollars and seconds per call, per task, per user, per month. M7 taught every token has a *cost* (the context tax); M8 that every token has a *price*, set by **who generates it**.
- **Model portfolio / model mix** — treating models as a portfolio rather than a pick: commodity calls to open models (most), genuinely hard calls to a frontier model (few). The workshop's answer to the frontier-vs-open false binary: *use both, efficiently.* Rebalancing = a config edit + an eval run.
- **Model routing (performance routing)** — choosing *which model answers this call* on difficulty and cost. Distinct from M1's control-flow routing (which step) and M6's policy routing (which backend the operator permits).
- **Route / target / `llm_client`** — Switchyard's three nouns, in dependency order: an **`llm_client`** is *where requests go* (endpoint + wire format + the **name** of the key's env var); a **target** is *which model* (an upstream model id on a client, under a short name); a **route** is *what your app asks for* (a public model id + the algorithm that picks among targets). Only the route id is visible to your application.
- **Capability mode vs escalation mode** (`llm_classifier`) — **capability**: a judge scores each request for *how likely the efficient model is to succeed*; **above `base_threshold`** rides efficient, **below** escalates (raising the dial escalates *more*). **Escalation**: no threshold — every session starts on the weak target and moves up after N consecutive escalate verdicts (`confirmations`), **one-way**, never back down.
- **Session affinity** — pinning a session to the tier it started on so the agent doesn't flap between brains mid-conversation. At the gateway, sessions are grouped by the `x-switchyard-session-id` header; `message_hash_fallback` is the backstop for clients that send none (and requires session affinity).
- **Router tax** — the permanent per-turn cost of *deciding* (a judge call's tokens + latency). Real, and measured as a **ratio of the routed run's own spend**: in the M8 lab ~4–6% in its own measured runs (the taxonomy page's bar prints the same band), and 21% with ~700 ms/turn in LangChain's benchmark. `stage_router` has none (its evidence was free); at the gateway it lives in `/v1/stats`, not on your receipt.
- **Pareto frontier (cost vs accuracy)** — the set of routing configurations where you can't get cheaper without getting worse. Sweeping `base_threshold` traces it on *your* workload; the Routing Client's race plots accuracy against cost so the learner can see it.
- **Frontier stand-in** — in the M8 lab, Nemotron Super 120B *plays* the expensive tier so the module runs on one free key. Not literally a frontier model.
- **NeMo Switchyard** — NVIDIA's open-source (Apache-2.0) router: an in-process library (`switchyard.libsy`), an OpenAI-compatible gateway embedded in the pip wheel (`routes.toml`), and a launcher for M7's harnesses. Pre-alpha; the module pins `nemo-switchyard[cli]==0.2.0`.

## NVIDIA platform (all modules)
- **NIM (NVIDIA Inference Microservices)** — the serving layer; hosted at `integrate.api.nvidia.com`, or run locally as a container.
- **NGC (NVIDIA GPU Cloud)** — registry + where API keys live.
- **Nemotron** — NVIDIA's model family: **Super (120B)** for reasoning/judge; **Nano (4B/9B/30B)** for local/SDG/training.
- **NVIDIA AI Workbench** — the platform hosting DevX-Lab (see `nvwb` / `setup-workshop`).
