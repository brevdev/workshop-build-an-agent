# Agent Customization Workshop

<img src="_static/robots/magician.png" alt="Workshop Robot Character" style="float:right;max-width:300px;margin:25px;" />

The Agent Customization Workshop teaches you how to **customize AI agents for specific domains** using NVIDIA technology. You'll transform a generic bash agent into a **LangGraph CLI expert** using Synthetic Data Generation (SDG) and Reinforcement Learning with Verifiable Rewards (RLVR).

This workshop demonstrates a **generalizable pattern** that applies to any CLI tool—kubectl, terraform, docker, or your own internal tools.

## Learning Objectives

By the end of this workshop, you'll know how to:
- **WHY** to customize agents (domain expertise vs general-purpose)
- **WHAT** customization looks like (SDG → RLVR → Deployment)
- **HOW** to do it (NeMo Data Designer, NeMo Gym, GRPO)
- How to implement **safe execution** with allowlists and sandboxing

## Workshop Structure

| Part | What You'll Do | Time |
|------|----------------|------|
| **Part 1** | Build and explore the base bash agent | 20 min |
| **Part 2a** | Generate synthetic training data | 15 min |
| **Part 2b** | Train with GRPO using NeMo Gym | 60-70 min |
| **Part 2c** | Test the customized agent | 15 min |
| **Extension** | Explore safe execution & sandboxing | Optional |> Head over to [Setting up Secrets](secrets.md) to get started!