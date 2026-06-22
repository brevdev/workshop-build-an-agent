<div class="m7-hero" data-eyebrow="MODULE 07 / AGENT HARNESSES" data-title="Same model. Different harness." data-sub="Name the layer wrapped around the LLM, take it apart, and learn why agents are increasingly won or lost in the harness - not the model." data-meta="DURATION::2-3 hrs|EXERCISES::5|MODEL::Nemotron + any harness|GPU::yours, any harness"></div>

<img src="_static/robots/wings.png" alt="Workshop Robot Character" style="float:right;max-width:240px;margin:20px;" />

Throughout this workshop you've built agents with LangGraph, run them with deepagents, and hardened an always-on OpenClaw assistant. Every one of those agents had two distinct layers: the **LLM** (stateless next-token prediction) and the **harness** (everything wrapped around it). In this module, you'll finally name that second layer, take it apart, and learn why the harness — not the model — is increasingly where agents are won or lost.

You'll survey the harness landscape from maximal (Claude Code, OpenClaw) to minimal (pi), measure the **context tax** each design pays, and then meet the layer that makes them all interoperable: **Agent Skills**. You'll author your own skill, install an **NVIDIA Verified Skill** from [github.com/NVIDIA/skills](https://github.com/NVIDIA/skills), and put your GPU to work from inside any harness — open source or closed.

<div class="m7-bento">
  <div class="m7-cell is-wide is-tall m7-reveal" style="--i:1">
    <h4>YOU WILL TAKE HOME</h4>
    <ul>
      <li>A clear mental model of the <b>harness vs. LLM separation</b> and the five things harnesses own: memory, self-evolution, skills, tool calling, and token efficiency</li>
      <li>A working map of the <b>harness landscape</b> and a framework for choosing between them</li>
      <li>Hands-on experience <b>measuring the context tax</b> of harness designs and implementing lazy skill loading</li>
      <li>The ability to <b>author a portable skill</b> that runs unchanged across multiple harnesses</li>
      <li>Practical experience with <b>NVIDIA Verified Skills</b> — installing, verifying signatures, and driving your GPU with CUDA-X libraries from inside an agent</li>
    </ul>
  </div>
  <div class="m7-cell m7-reveal" style="--i:2"><h4>DURATION</h4><span class="m7-big">2-3 h</span>self-paced</div>
  <div class="m7-cell m7-reveal" style="--i:3"><h4>THE LAB</h4>5 exercises — from a minimal harness to self-evolving skills</div>
  <div class="m7-cell m7-reveal" style="--i:4"><h4>HARNESSES COVERED</h4>OpenClaw, Hermes, OpenCode, Deep Agents, pi, Claude Code, Codex</div>
  <div class="m7-cell m7-reveal" style="--i:5"><h4>YOUR GPU WORKS</h4>Drive it from any harness with a verified cuDF skill + nvidia-smi</div>
  <div class="m7-cell m7-reveal" style="--i:6"><h4>VERIFIED SKILLS</h4><a href="https://github.com/NVIDIA/skills">github.com/NVIDIA/skills</a> — signed + scanned</div>
</div>

> Head over to [Setting up Secrets](secrets) to get started!
