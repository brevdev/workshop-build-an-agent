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
- **Routing** — the control logic orchestrating the loop (hand-rolled in M1; framework-handled by `create_*_agent`).

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

## NVIDIA platform (all modules)
- **NIM (NVIDIA Inference Microservices)** — the serving layer; hosted at `integrate.api.nvidia.com`, or run locally as a container.
- **NGC (NVIDIA GPU Cloud)** — registry + where API keys live.
- **Nemotron** — NVIDIA's model family: **Super (120B)** for reasoning/judge; **Nano (4B/9B/30B)** for local/SDG/training.
- **NVIDIA AI Workbench** — the platform hosting DevX-Lab (see `nvwb` / `setup-workshop`).
