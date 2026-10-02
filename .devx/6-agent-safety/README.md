<div class="dx-hero" data-eyebrow="MODULE 06 / AGENT SAFETY" data-title="Agent Safety with NemoClaw" data-meta="DURATION::2-2.5 hrs|MODEL::Hosted Nemotron|GPU::Optional local inference"></div>

Your agent runs 24/7, evolves its own behavior, and processes sensitive data. How do you make it safer when you're not watching?

In this module, you'll use **NVIDIA NemoClaw** to add runtime boundaries to an OpenClaw agent. You'll test network, filesystem, and process restrictions, explore operator-controlled inference routing, and build a safety evaluation suite. A separate content-classifier exercise shows how an application can decide which data needs a local route.

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide is-tall"><h4>YOU WILL BUILD</h4><span class="dx-big">A hardened autonomous agent</span>Runtime boundaries, operator-controlled inference, and a red-team evaluation suite.</div>
  <div class="dx-cell"><h4>DURATION</h4><span class="dx-big">2-2.5 h</span>self-paced</div>
  <div class="dx-cell"><h4>BUILT WITH</h4>OpenClaw - OpenShell - Nemotron - Privacy Router</div>
  <div class="dx-cell"><h4>YOU'LL TAKE HOME</h4>Kernel-level enforcement, operator-controlled routing, and continuous safety evaluation.</div>
</div>

## Learning Objectives

<img src="_static/robots/supervisor.png" alt="Workshop Robot Character" style="float:right;max-width:300px;margin:25px;" />

At the end of this module, you will take home:

- Understanding of **kernel-level enforcement** with Landlock LSM and OpenShell policies
- Hands-on experience building a **content classifier** that proposes local or cloud routes
- Practical skills in **red-teaming autonomous agents** with adversarial probes
- Familiarity with **LLM-as-judge safety evaluation**, mirroring Module 3's quality approach
- Knowledge of the **NemoClaw stack** and how OpenClaw, OpenShell, and Nemotron integrate into a complete safety architecture

<div class="dx-island dx-tutor">
  <p class="dx-island-title">WORK ALONGSIDE AN AI TUTOR</p>

This workshop ships its own tutor as **Agent Skills**. It explains this module's concepts in the workshop's own framing, gives graduated hints **without ever completing your exercises**, and helps you troubleshoot when something breaks. Open one and leave it running beside these pages:

<button onclick="launch('Claude Code', 'Workshop Utilities');"><i class="fa-solid fa-robot"></i> Claude Code</button> <button onclick="launch('Codex CLI', 'Workshop Utilities');"><i class="fa-solid fa-robot"></i> Codex CLI</button>

Ask for this module by name — `/module-6` in Claude Code, `$module-6` in Codex — or just describe what you're stuck on and the right skill loads on its own.

```text
/module-6 what does the Privacy Router actually do?
```

</div>

> Head over to [Setting up Secrets](secrets) to get started!
