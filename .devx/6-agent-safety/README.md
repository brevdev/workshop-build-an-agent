# Agent Safety with NemoClaw

<img src="_static/robots/supervisor.png" alt="Workshop Robot Character" style="float:right;max-width:300px;margin:25px;" />

Your agent runs 24/7, evolves its own behavior, and processes sensitive data. How do you make it safer when you're not watching?

In this module, you'll learn about **NVIDIA NemoClaw** — a reference stack for strengthening the security of autonomous agents — to build a defense system that adds safety enforcement at the kernel level, classifies data before it leaves the machine, and continuously verifies the agent hasn't drifted. NemoClaw combines OpenClaw (agent), OpenShell (enforcement), Nemotron (local inference), and Privacy Router (data routing) into one deployable system.

This learning module can take around 2 to 2.5 hours to complete.

## Learning Objectives

At the end of this module, you will take home:

- Understanding of **kernel-level enforcement** with Landlock LSM and OpenShell policies
- Hands-on experience building a **data classification and routing pipeline** that separates PII from public data
- Practical skills in **red-teaming autonomous agents** with adversarial probes
- Familiarity with **LLM-as-judge safety evaluation**, mirroring Module 3's quality approach
- Knowledge of the **NemoClaw stack** and how OpenClaw, OpenShell, and Nemotron integrate into a complete safety architecture

> Head over to [Setting up Secrets](secrets) to get started!
