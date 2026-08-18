<div class="dx-hero" data-eyebrow="MODULE 08 / AGENT ROUTING" data-title="The right model for every call." data-sub="Put a meter on every model call, then route each one to the model that should answer it - frontier where it's needed, open where it isn't. Use both, efficiently." data-meta="DURATION::2-3 hrs|EXERCISES::5 + a live client|MODEL::Nemotron pool (hosted)|GPU::optional (Exercise 4b)"></div>

<img src="_static/robots/controls.png" alt="Workshop Robot Character" style="float:right;max-width:240px;margin:20px;" />

Seven modules of agents, and every one of them pinned a single model for *every* call — the Module 1 report writer, the Module 2 help desk, even the Module 7 harness you built by hand. But inside a single task, calls aren't equal: "reformat this JSON" and "plan a five-step investigation" got billed and delayed like the same job. That gap is **tokenomics** — the unit economics of running agents on tokens — and it's the debate every team adopting agents is having right now, usually framed as a false binary: frontier models *or* open models.

This module's answer is a portfolio, not a pick. You'll put a meter on every call, write a routing classifier by hand, then hand the decision to **NVIDIA NeMo Switchyard** — in-process with `switchyard.libsy`, and at a gateway your application code never reads — closing on a scoreboard of accuracy, cost, frontier share, and the router's own tax, measured, not marketed. Then you take it for a drive: the **Routing Client**, a live switchyard tile that renders your finished lab file, routes any prompt you throw at it, and prices every answer against the frontier-only counterfactual.

<div class="dx-bento">
  <div class="dx-cell is-wide is-tall dx-reveal" style="--i:1">
    <h4>YOU WILL TAKE HOME</h4>
    <ul>
      <li>A working definition of <b>tokenomics</b> and why "frontier vs open" is a false binary</li>
      <li>The routing taxonomy: <b>static splits, content classifiers, stage signals, escalation, and learned routers</b> - and what evidence each one pays for</li>
      <li>A <b>hand-rolled routing classifier</b> you wrote yourself, and the fail-up discipline that keeps misroutes cheap</li>
      <li>Hands-on <b>NeMo Switchyard</b> - the in-process library and the <code>routes.toml</code> gateway, with the two config traps every team hits</li>
      <li>The <b>router tax</b>, measured on your own runs - and where it hides when a gateway pays it</li>
      <li>A <b>scoreboard habit</b>: no routing claim without accuracy, cost, mix, and tax on one line</li>
    </ul>
  </div>
  <div class="dx-cell dx-reveal" style="--i:2"><h4>DURATION</h4><span class="dx-big">2-3 h</span>self-paced</div>
  <div class="dx-cell dx-reveal" style="--i:3"><h4>THE LAB</h4>5 exercises, then the Routing Client - a live switchyard playground for the router you built</div>
  <div class="dx-cell dx-reveal" style="--i:4"><h4>MODELS ROUTED</h4>Nemotron Super 120B (the frontier stand-in) and Nemotron 3.5 Lightning 30B - one hosted key, no new secrets</div>
  <div class="dx-cell dx-reveal" style="--i:5"><h4>YOUR GPU, OPTIONALLY</h4>Exercise 4b routes the easy tier to a local NIM on your own silicon</div>
  <div class="dx-cell dx-reveal" style="--i:6"><h4>SWITCHYARD</h4><a href="https://github.com/NVIDIA-NeMo/Switchyard">github.com/NVIDIA-NeMo/Switchyard</a> - open source, Apache-2.0</div>
</div>

<div class="dx-island dx-tutor">
  <p class="dx-island-title">WORK ALONGSIDE AN AI TUTOR</p>

This workshop ships its own tutor as **Agent Skills**. It explains this module's concepts in the workshop's own framing, gives graduated hints **without ever completing your exercises**, and helps you troubleshoot when something breaks. Open one and leave it running beside these pages:

<button onclick="launch('Claude Code', 'Workshop Assistants');"><i class="fa-solid fa-robot"></i> Claude Code</button> <button onclick="launch('Codex CLI', 'Workshop Assistants');"><i class="fa-solid fa-robot"></i> Codex CLI</button>

Ask for this module by name — `/module-8` in Claude Code, `$module-8` in Codex — or just describe what you're stuck on and the right skill loads on its own.

```text
/module-8 why route between models instead of picking one?
```

</div>

> Head over to [Setting up Secrets](secrets) to get started!
