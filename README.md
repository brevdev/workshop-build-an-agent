# Build An Agent Workshop  [![ Click here to deploy.](https://brev-assets.s3.us-west-1.amazonaws.com/nv-lb-dark.svg)](https://brev.nvidia.com/launchable/deploy?launchableID=env-32kC34ErT9wsqTcJyaKMxBEuhr2) [![Open In AI Workbench](https://img.shields.io/badge/Open_In-AI_Workbench-76B900)](https://ngc.nvidia.com/open-ai-workbench/aHR0cHM6Ly9naXRodWIuY29tL2JyZXZkZXYvd29ya3Nob3AtYnVpbGQtYW4tYWdlbnQ=)

The Build An Agent Workshop is a comprehensive, hands-on learning experience that teaches you how to create, deploy, and evaluate AI agents using NVIDIA technology. Through eight progressive modules, you'll build intelligent systems that can perform complex tasks, learn to implement Retrieval Augmented Generation (RAG), and master the art of evaluating, improving, and securing agent performance.

This workshop provides everything you need to become proficient in agentic AI development:

* **Module 1 - Build an Agent**: Create a Report Generation Agent that researches topics and writes comprehensive reports
* **Module 2 - Agentic RAG**: Build an IT Help Desk agent using RAG with NVIDIA NeMo Retriever
* **Module 3 - Agent Evaluation**: Learn to measure and improve agent quality using RAGAS metrics and LLM-as-a-judge techniques
* **Module 4 - Agent Customization**: Customize your agent beyond prompt engineering and tools with agent skills and reinforcement learning (RL).
* **Module 5 - Deep Agents**: Build deep agents that autonomously handle complex, multi-step tasks—and learn to run them safely and securely in production with sandboxing and isolation.
* **Module 6 - Agent Safety**: Secure autonomous agents with kernel-level enforcement (via OpenShell) and privacy routing using NVIDIA's NemoClaw stack.
* **Module 7 - Agent Harnesses & Skills**: Separate the harness layer from the LLM, survey harness architectures from OpenClaw to pi to Claude Code, and supercharge any of them with portable, GPU-accelerated NVIDIA Verified Skills.
* **Module 8 - Agent Routing**: Tame agent tokenomics with NVIDIA NeMo Switchyard — route every call to the right model (frontier or open), visualized live in the Routing Client.

At the end of this workshop, you will take home:

* Deep understanding of agent architecture and design patterns
* Eight working agents demonstrating different capabilities
* Knowledge of NVIDIA NIM, NeMo models, and evaluation tools
* Comprehensive evaluation framework for production agents
* A turn-key, portable development environment
* Best practices for continuous agent improvement

The entire workshop can take anywhere from 16 to 24 hours to complete, depending on depth of exploration.

## 🤖 Learn with an AI tutor (optional)

This repo ships a set of **Agent Skills** that turn a coding agent into a hands-on workshop tutor. It explains each module's concepts in the workshop's own framing, gives **graduated hints — without ever completing your exercises or revealing answer keys** — interprets agent behavior, and troubleshoots the environment. It's an optional companion to the notebooks; you stay in the driver's seat.

The skills work in **either harness** — use whichever you prefer. Same content; the Agent Skills format is cross-harness. Only the way you *invoke* a skill differs:

- **Claude Code** reads them from `.claude/skills/` — invoke with a slash, e.g. `/workshop`, `/module-3`.
- **Codex** reads them from `.agents/skills/` — invoke with a dollar sign, e.g. `$workshop`, `$module-3` (or run `/skills` to pick from a menu).

In **both**, you can also just describe what you need (e.g. "help me with Module 3") and the matching skill loads automatically.

**Available skills:** `workshop` (overview + router), `module-1` … `module-8` (one per module), and `setup-workshop` (local install helper) — prefix with `/` in Claude Code or `$` in Codex.

**Two ways to use it — pick whichever fits how you're running the workshop:**

1. **Inside DevX-Lab (nothing to install).** Both `claude` and `codex` are preinstalled in the workshop container. Open a **Terminal** in JupyterLab — or, on desktop AI Workbench, the bundled **VS Code** app — and run **either** harness:
   - `claude` — on first launch paste an **Anthropic API key** (get one at <https://console.anthropic.com>), or
   - `codex` — on first launch sign in with `codex login` (ChatGPT account) or set `OPENAI_API_KEY`.

   This harness credential is separate from your NVIDIA key. Then start the tutor — in **Claude Code** type `/workshop` to get oriented (or `/module-3`); in **Codex** type `$workshop` (or `$module-3`, or run `/skills` to pick from a menu). The skills load automatically because you're running inside the project. *(If a CLI isn't found — e.g. an older build — run `sudo npm install -g @anthropic-ai/claude-code` or `sudo npm install -g @openai/codex` once.)*
2. **Against a local clone.** Prefer your own machine/editor? Install your harness (`npm install -g @anthropic-ai/claude-code` **or** `npm install -g @openai/codex`), clone this repo, and run `claude` or `codex` from the repo root — the skills load automatically.

> **What the tutor will and won't do:** it's *guide-only* by design — it won't run GPU training, drive the live agent/sandbox/red-team, or fill in exercise blanks for you. Genuine setup/environment problems (keys, Docker, a broken control plane, OOM) it *will* help you fix directly.
>
> *Persistence:* the container persists each harness's settings and memory across rebuilds. Claude Code keeps credentials outside its volume, so you'll re-enter the Anthropic API key after a rebuild; Codex stores auth inside `~/.codex/`, so a single `codex login` persists across rebuilds.

## Workshop Modules

### Module 1: Build an Agent (1-2 hours)

Learn the fundamentals of AI agents by building a Report Generation Agent from scratch.

**What you'll build**: An intelligent system that researches any topic, creates outlines, writes detailed sections, and compiles professional reports automatically.

**Key concepts**:
- The four core components of any AI agent (Model, Tools, Memory, Routing)
- ReAct architecture for tool-calling agents
- Building agents from scratch and with LangChain
- Using NVIDIA Nemotron models

### Module 2: Agentic RAG (2-3 hours)

Evolve from basic RAG to intelligent agentic RAG systems.

**What you'll build**: An IT Help Desk agent that dynamically decides when and how to search knowledge bases to answer user queries.

**Key concepts**:
- Traditional RAG limitations and how agents solve them
- NVIDIA NeMo Retriever (embeddings and reranking)
- Vector databases with FAISS
- ReAct agents with retrieval tools

### Module 3: Agent Evaluation (2-3 hours)

Master the art of measuring and improving agent performance.

**What you'll learn**: How to systematically evaluate agents using industry-standard metrics, LLM-as-a-judge techniques, and NVIDIA models.

**Key concepts**:
- RAGAS metrics for RAG evaluation (faithfulness, relevancy, context precision/recall)
- LLM-as-a-judge with NVIDIA models
- Building automated evaluation pipelines
- Continuous improvement strategies
- Production monitoring best practices

### Module 4: Agent Customization (3-4 hours)

Specialize agents for specific domains using synthetic data and reinforcement learning.

**What you'll build**: A bash agent customized into a LangGraph CLI expert using NVIDIA NeMo Data Designer for synthetic data generation and GRPO (Group Relative Policy Optimization) for training.

**Key concepts**:
- When to use training vs. prompt engineering vs. tools
- Synthetic data generation with NeMo Data Designer
- Verifiable reward functions with NeMo Gym
- GRPO training for exploration-based learning
- Human-in-the-loop safety for command execution agents

### Module 5: Deep Agents (1-2 hours)

Build autonomous agents that handle complex, multi-step tasks with planning and delegation.

**What you'll build**: A production-grade deep agent with explicit planning, hierarchical sub-agent delegation, persistent memory, and sandboxed execution using Docker.

**Key concepts**:
- The four pillars of deep agents (planning, delegation, memory, skills)
- Shallow vs. deep agent architectures
- Sandboxing and security for autonomous agents
- Using NVIDIA NIM models with the deepagents library
- Production isolation patterns (Docker, resource limits)

### Module 6: Agent Safety (2-2.5 hours)

Secure autonomous agents with kernel-level enforcement, data routing, and continuous safety evaluation.

**What you'll build**: An OpenClaw personal assistant agent that executes inside and outside of an Openshell sandbox, complete with network and filesystem policies that demonstrate how the NVIDIA NemoClaw reference stack improves agent security.

**Key concepts**:
- Why application-level controls (M4) and container isolation (M5) are insufficient for always-on agents
- Setting up and running an OpenClaw autonomous agent
- Kernel-level enforcement with OpenShell (Landlock LSM, seccomp BPF, OPA proxy)
- Improved security for routing inference via a privacy router
- Red-team testing with adversarial probes
- Safety evaluation using LLM-as-judge (extending M3's evaluation framework)
- The NemoClaw reference architecture (OpenClaw + OpenShell + Nemotron + Privacy Router)

### Module 7: Agent Harnesses & Skills (2-3 hours)

Understand the harness layer that turns a stateless LLM into a capable agent — and the open skills format that makes capability portable across every harness.

**What you'll build**: A minimal pi-style harness from scratch (four tools, sub-1k-token prompt), a context-tax measurement suite with lazy skill loading, a portable skill that runs unchanged in your harness and OpenClaw, and a GPU-accelerated agent powered by the NVIDIA-verified cuDF skill.

**Key concepts**:
- The harness vs. LLM separation, and the five things harnesses own (memory, self-evolution, skills, tool calling, token efficiency)
- The harness landscape and philosophies: OpenClaw, Hermes, OpenCode, LangChain Deep Agents, pi, Claude Code, and Codex
- The context tax, and lazy skill loading as token efficiency in action
- The open Agent Skills specification and skill authoring
- NVIDIA Verified Skills (github.com/NVIDIA/skills): signature verification, skill cards, and capability governance
- Driving your local GPU from inside any harness — open source or closed

### Module 8: Agent Routing (2-3 hours)

Tame agent tokenomics — send every call to the model that should answer it, and prove the savings.

**What you'll build**: A routing policy for your agent using NVIDIA NeMo Switchyard — a classifier router you write yourself first, then Switchyard in-process, then the gateway (a `routes.toml` policy your application code never reads) — all visualized live in the Routing Client.

**Key concepts**:
- Agent tokenomics, and why frontier vs. open is a false binary — use both, efficiently
- The routing-algorithm families, on the evidence-vs-cost-of-deciding axis
- NVIDIA NeMo Switchyard (Apache-2.0): targets, routes, and its library and gateway surfaces
- Router tax, escalation, and the misroute asymmetry (fail up, never down)
- Routing the easy tier to a local NIM on your own GPU
- Proving the policy with an eval suite: accuracy vs. cost, and the at-scale receipt

## Learning Objectives

By the end of this workshop, you'll know how to:
- **Build agents** that use tools, maintain context, and make intelligent decisions
- **Implement RAG systems** that dynamically retrieve and use information
- **Evaluate agent quality** using quantitative metrics and qualitative assessment
- **Use NVIDIA technology** including NIM, Nemotron models, and NeMo Retriever
- **Customize agents** through synthetic data generation and reinforcement learning
- **Build deep agents** with planning, delegation, and sandboxed execution
- **Secure agents** with kernel-level enforcement, data classification, and red-team evaluation
- **Choose and extend agent harnesses** using the context-tax framework and portable, NVIDIA-verified skills
- **Route agent traffic** across a model portfolio with NeMo Switchyard, and defend the cost/quality trade with an eval suite
- **Deploy and monitor** agents in production environments
- **Continuously improve** agent performance through systematic evaluation


