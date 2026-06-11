# Agent Harnesses: The Invisible Machine

<img src="_static/robots/assembly.png" alt="Workshop Robot Character" style="float:right;max-width:300px;margin:25px;" />

Across six modules you built six different agents — a report writer, a help desk, a bash expert, a deep researcher, an autonomous assistant. Here's the twist: in nearly every one, the model was the same — `nvidia/nemotron-3-super-120b-a12b`. Same weights, same API. What changed was everything *around* the model: the loop, the context, the tools, the gates, the memory. That invisible machine has a name — the **agent harness** — and in this module you'll build one from scratch.

You'll build **Hermes**: a glass-box, zero-framework Python harness, small enough to read end to end, driven from a terminal REPL. It makes raw HTTP calls to the same NVIDIA endpoint you used in Module 1 — and at the end you'll carry it into Module 6's NemoClaw sandbox to run under kernel policy.

This learning module can take around 2.5 to 3 hours to complete.

> 💡 **Note:** the final exercise reuses the Module 6 NemoClaw sandbox. Completing Module 6 first is strongly recommended (budget extra time for its setup pages if you skipped it).

## Learning Objectives

At the end of this module, you will take home:

- The **agent stack** — one mental model that places every concept from Modules 1–6 (NIMs, tools, ReAct, RAG, MCP, skills, evaluation, fine-tuning, planning, sandboxing) into three layers: model, harness, environment
- How to build a **from-scratch agent harness** — message loop, context assembly, token budgeting and compaction, persistent memory, tool registry, and human-in-the-loop permission gates — with no frameworks, just Python and HTTP
- What each harness subsystem actually contributes, proven by a **three-way face-off**: the same probes against a bare model call, your Hermes harness, and OpenClaw
- How a harness and a sandbox **divide responsibility** — running your own harness under OpenShell's kernel-level policy, including keyless inference through the Privacy Router's credential injection
- A working **vocabulary for the harness landscape**: framework vs harness vs application, and where Claude Code, OpenClaw, deepagents, and Hermes each sit

> Head over to [Setting up Secrets](secrets) to get started!
