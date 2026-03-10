> **NOTE:** For GTC 2026, this repository is being configured for CPU-only Brev instances to support a GTC Training Workshop [DLIT82062]. This is a temporary change and the launchable will return to default compute settings after GTC 2026. 

# Build An Agent Workshop [![ Click here to deploy.](https://brev-assets.s3.us-west-1.amazonaws.com/nv-lb-dark.svg)](https://brev.nvidia.com/launchable/deploy?launchableID=env-32kC34ErT9wsqTcJyaKMxBEuhr2)

The Build An Agent Workshop is a comprehensive, hands-on learning experience that teaches you how to create, deploy, and evaluate AI agents using NVIDIA technology. Through five progressive modules, you'll build intelligent systems that can perform complex tasks, learn to implement Retrieval Augmented Generation (RAG), and master the art of evaluating and improving agent performance.

This workshop provides everything you need to become proficient in agentic AI development:

* **Module 1 - Build an Agent**: Create a Report Generation Agent that researches topics and writes comprehensive reports
* **Module 2 - Agentic RAG**: Build an IT Help Desk agent using RAG with NVIDIA NeMo Retriever
* **Module 3 - Agent Evaluation**: Learn to measure and improve agent quality using RAGAS metrics and LLM-as-a-judge techniques
* **Module 4 - Agent Customization**: Customize your agent beyond prompt engineering and tools with agent skills and reinforcement learning (RL).
* **Module 5 - Deep Agents**: Build deep agents that autonomously handle complex, multi-step tasks—and learn to run them safely and securely in production with sandboxing and isolation. 

At the end of this workshop, you will take home:

* Deep understanding of agent architecture and design patterns
* Five working agents demonstrating different capabilities
* Knowledge of NVIDIA NIM, NeMo models, and evaluation tools
* Comprehensive evaluation framework for production agents
* A turn-key, portable development environment
* Best practices for continuous agent improvement

The entire workshop can take anywhere from 10 to 15 hours to complete, depending on depth of exploration.

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

## Learning Objectives

By the end of this workshop, you'll know how to:
- **Build agents** that use tools, maintain context, and make intelligent decisions
- **Implement RAG systems** that dynamically retrieve and use information
- **Evaluate agent quality** using quantitative metrics and qualitative assessment
- **Use NVIDIA technology** including NIM, Nemotron models, and NeMo Retriever
- **Customize agents** through synthetic data generation and reinforcement learning
- **Build deep agents** with planning, delegation, and sandboxed execution
- **Deploy and monitor** agents in production environments
- **Continuously improve** agent performance through systematic evaluation


