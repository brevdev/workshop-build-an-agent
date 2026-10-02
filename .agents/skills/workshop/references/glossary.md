# Workshop Glossary — tutor reference

Shared definitions for terms that recur across modules. Use for "what does X mean?"
regardless of which module the learner is in. Each entry is a 1–2 line working definition +
where it's central; for depth, see that module's `concepts.md`.

## Agent fundamentals (M1)
- **Agent** — an LLM in a loop that *chooses* what to do (which tool, or to answer), vs a fixed chain.
- **ReAct** — Reason→Act→Observe loop; a common agent pattern. Central M1; recurs everywhere.
- **Agentic loop** — give the model input + tools → it responds or requests a tool → run the tool, append result, repeat.
- **Tool / tool calling** — a function the model *requests* (name + args); **your code runs it** ("the menu, not the kitchen"). The model never executes code.
- **System prompt** — the message defining the agent's role, constraints, and when to use tools.
- **Memory / state** — short-term = conversation state; longer-term = external stores (DBs/files). Persistence depends on storage and lifecycle.
- **Routing** — the control logic orchestrating the loop (hand-rolled in M1; framework-handled by `create_*_agent`).

## RAG & retrieval (M2)
- **RAG** — Retrieval-Augmented Generation: fetch relevant docs, then generate with them as context.
- **Agentic RAG** — retrieval exposed as a *tool* the model calls *when needed* (vs traditional RAG's always-retrieve fixed path).
- **Chunking** — splitting docs into overlapping pieces (`RecursiveCharacterTextSplitter`, size 800 / overlap 120).
- **Embedding** — text → vector; similar meaning → nearby vectors. NVIDIAEmbeddings.
- **Vector DB / FAISS** — stores vectors for similarity search (FAISS = Meta's in-memory lib).
- **Reranking** — uses a model to rescore retrieved candidates by estimated relevance. NVIDIARerank.
- **NeMo Retriever** — NVIDIA's retrieval models and tools; current embedding/reranking choices are in `code/workshop_support/models.json`.
- **MCP (Model Context Protocol)** — an open protocol connecting applications to servers that expose tools, resources and prompts.
- **Agent Skill** — a folder/`.md` of *instructions* (know-how) loaded on demand; complements MCP (tools).

## Evaluation (M3)
- **LLM-as-a-judge** — using an LLM (Nemotron, temp 0) to score outputs against a rubric.
- **Faithfulness** — are the answer's claims grounded in the retrieved context (no hallucination)? (generation)
- **Answer Relevancy** — does the answer address the question (regardless of grounding)? (generation)
- **Context Precision / Recall** — are retrieved chunks relevant & well-ranked / was everything needed retrieved? (retrieval)
- **RAGAS** — open-source RAG evaluation framework. These metrics are mostly 0–1; cosine-based answer relevance can be negative.
- **Calibration** — checking that the judge agrees with human ratings on a sample.
- **SDG (Synthetic Data Generation)** — generating test/training data programmatically (NeMo Data Designer).

## Customization & training (M4)
- **SFT** — Supervised Fine-Tuning: train on input→output examples to learn desired behavior.
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
- **Backend** — where file/shell ops run: `FilesystemBackend` (files) / `LocalShellBackend` (host shell) / `DockerSandboxBackend` (container).
- **Sandbox** — a restricted execution environment; here, Docker with no host mounts or network.

## Safety (M6)
- **Operator** — the human with host access to the OpenShell gateway: configures providers, sets the backend, applies policies. (vs the **agent** in the sandbox, vs the **end user**.)
- **NemoClaw** — NVIDIA's reference stack (OpenClaw + OpenShell + Nemotron + Privacy Router).
- **OpenClaw** — the open, config-first autonomous agent framework NemoClaw wraps (not NVIDIA).
- **OpenShell** — NVIDIA's runtime combining kernel restrictions, network policy and inference routing.
- **Landlock LSM** — Linux security module for filesystem rules a running process cannot relax.
- **seccomp BPF** — Linux kernel syscall filtering; drops dangerous syscalls.
- **Privacy Router** — OpenShell's inference gateway: enforces the **operator's chosen backend** + injects credentials. **Not** content classification.
- **Defense in depth** — complementary controls that limit different attack paths; each attack may reach different layers.
- **Red-team probe** — an adversarial input crafted to trigger unsafe behavior.

## Harnesses & skills (M7)
- **Harness** — the layer *around* the LLM: memory, tool execution, planning, the loop, the token budget. The model is stateless; the harness is everything else. Every M1–M6 agent ran in one (named retroactively in M7).
- **Context tax** — tokens used by harness instructions, tool schemas and skill descriptions. The lab measures its own configurations, not vendor rankings.
- **Lazy skill loading** — show skill names and descriptions first; load full instructions only when needed, reducing context used up front.
- **Agent Skills spec** — the open format ([agentskills.io](https://agentskills.io)): a shared `SKILL.md` format; tools, permissions and runtime support vary across harnesses. See also **Agent Skill** (M2).
- **NVIDIA Verified Skills** — signed, security-scanned skills (`github.com/NVIDIA/skills`) teaching agents to use NVIDIA software (cuDF, cuOpt, NeMo…); capability governance via SkillSpector, skill cards, and OpenSSF Model Signing.
- **The harness landscape** — pi · OpenCode · LangChain Deep Agents · Hermes (optional M7 comparison) · OpenClaw (M6) · Claude Code / Codex.

## NVIDIA platform (all modules)
- **NIM (NVIDIA Inference Microservices)** — model-serving software. The workshop uses NVIDIA hosted APIs and optional local NIM containers.
- **NGC (NVIDIA GPU Cloud)** — NVIDIA's registry and software catalog.
- **Nemotron** — NVIDIA's model family. Shared roles select Super/Lightning for hosted calls; M4 trains Nano 9B v2.
- **NVIDIA AI Workbench** — the platform hosting DevX-Lab (see `nvwb` / `setup-workshop`).
