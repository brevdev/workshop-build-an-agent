# Agent Harnesses & Skills

<img src="_static/robots/wings.png" alt="Workshop Robot Character" style="float:right;max-width:300px;margin:25px;" />

Same model, different harness — a completely different agent. Why?

Throughout this workshop you've built agents with LangGraph, run them with deepagents, and hardened an always-on OpenClaw assistant. Every one of those agents had two distinct layers: the **LLM** (stateless next-token prediction) and the **harness** (everything wrapped around it). In this module, you'll finally name that second layer, take it apart, and learn why the harness — not the model — is increasingly where agents are won or lost.

You'll survey the harness landscape from maximal (Claude Code, OpenClaw) to minimal (pi), measure the **context tax** each design pays, and then meet the layer that makes them all interoperable: **Agent Skills**. You'll author your own skill, install an **NVIDIA Verified Skill** from [github.com/NVIDIA/skills](https://github.com/NVIDIA/skills), and put your GPU to work from inside any harness — open source or closed.

This learning module can take around 2 to 3 hours to complete.

## Learning Objectives

At the end of this module, you will take home:

- A clear mental model of the **harness vs. LLM separation** and the five things harnesses own: memory, self-evolution, skills, tool calling, and token efficiency
- A working map of the **harness landscape** — OpenClaw, Hermes, OpenCode, LangChain Deep Agents, pi, Claude Code, and Codex — and a framework for choosing between them
- Hands-on experience **measuring the context tax** of harness designs and implementing lazy skill loading
- The ability to **author a portable skill** that runs unchanged across multiple harnesses
- Practical experience with **NVIDIA Verified Skills** — installing, verifying signatures, and driving your GPU with CUDA-X libraries from inside an agent

> Head over to [Setting up Secrets](secrets) to get started!
