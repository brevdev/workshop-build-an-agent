<div class="dx-hero" data-eyebrow="MODULE 04 / AGENT CUSTOMIZATION" data-title="Agent Customization Workshop" data-meta="DURATION::3-4 hrs|MODEL::Nemotron Nano 9B (GRPO-trained)|GPU::A100-80GB+ recommended"></div>

The Agent Customization Workshop teaches you how to **customize AI agents for specific domains** using NVIDIA technology. You'll transform a generic bash agent into a **LangGraph CLI expert** using Synthetic Data Generation (SDG) and Reinforcement Learning with Verifiable Rewards (RLVR).

> While a DGX Spark (GB10) is supported, running this module on an A100-80GB or larger instance is highly recommended for faster training due to memory bandwidth constraints.

This workshop demonstrates a **generalizable pattern** that applies to customizing any AI agent. Here's what you're in for:

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide is-tall"><h4>YOU WILL BUILD</h4>A <b>customized bash agent</b> that turns a generic model into a LangGraph CLI expert - via synthetic data, verifiable rewards, and GRPO training.</div>
  <div class="dx-cell"><h4>DURATION</h4><span class="dx-big">3-4 h</span>self-paced</div>
  <div class="dx-cell"><h4>BUILT WITH</h4>NeMo Data Designer + NeMo Gym + GRPO</div>
  <div class="dx-cell is-wide"><h4>YOU'LL TAKE HOME</h4>An SDG pipeline, a verifiable reward function, the GRPO training workflow, and a reusable pattern for customizing any agent.</div>
</div>

## Learning Objectives

<img src="_static/robots/magician.png" alt="Workshop Robot Character" style="float:right;max-width:300px;margin:25px;" />

By the end of this workshop, you'll know how to:
- **WHY** we need to customize agents (domain expertise vs general-purpose)
- **WHAT** customization looks like (SDG → RLVR → Deployment)
- **HOW** to do it (NeMo Data Designer, NeMo Gym, GRPO)
- How to implement **safe execution** of agents by keeping the human in the loop

<div class="dx-island dx-tutor">
  <p class="dx-island-title">WORK ALONGSIDE AN AI TUTOR</p>

This workshop ships its own tutor as **Agent Skills**. It explains this module's concepts in the workshop's own framing, gives graduated hints **without ever completing your exercises**, and helps you troubleshoot when something breaks. Open one and leave it running beside these pages:

<button onclick="launch('Claude Code', 'Workshop Assistants');"><i class="fa-solid fa-robot"></i> Claude Code</button> <button onclick="launch('Codex CLI', 'Workshop Assistants');"><i class="fa-solid fa-robot"></i> Codex CLI</button>

Ask for this module by name — `/module-4` in Claude Code, `$module-4` in Codex — or just describe what you're stuck on and the right skill loads on its own.

```text
/module-4 should I train my agent, or just prompt it better?
```

</div>

> Head over to [Setting up Secrets](secrets) to get started!
