<div class="dx-hero" data-eyebrow="MODULE 07 / 06 - WRAP UP" data-title="You know what was running your agents." data-sub="You leave with a framework for choosing harnesses - not a favorite." data-meta="TAKEAWAY::context-tax framework|NEXT::Module 08 - Routing"></div>

You came into this module having built six agents. You leave knowing what was actually running them.

<!-- fold:break -->

## What Your Exercises Map To

Just like Module 6 mapped its exercises to the production NemoClaw stack, here's where each lab exercise lives in the real ecosystem:

| Lab exercise | Production counterpart |
|---|---|
| **1. Minimal harness** | pi's core design; the agentic loop inside every harness from OpenClaw to Claude Code |
| **2. Context tax + lazy loading** | pi's lazy skills; skill indexes and deferred tool loading in modern maximal harnesses |
| **3. Portable skill** | The open Agent Skills spec ([agentskills.io](https://agentskills.io)) powering every major skill hub |
| **4. Verified skill + GPU** | [NVIDIA Verified Skills](https://github.com/NVIDIA/skills): SkillSpector scans, skill cards, OpenSSF Model Signing |
| **5. Self-evolving skill** | pi self-extension; Hermes's self-authored skills in `~/.hermes/skills/`; OpenClaw memory evolution — and the write-policies NemoClaw puts around them |

<!-- fold:break -->

## The Decision Framework, One Last Time

When someone asks you "which harness should we use?", you now have a real answer:

- **Need model flexibility, on-prem, or Nemotron?** → open source.
- **Always-on assistant with community momentum?** → OpenClaw; curated defaults → Hermes.
- **Task-shaped workflow, or an agent embedded in your product?** → LangChain Deep Agents.
- **An open, any-model coding agent in your terminal?** → OpenCode.
- **Every token is precious, or you lean on the model?** → pi.
- **Maximum out-of-box capability, cost secondary?** → Claude Code; on OpenAI models with cloud-delegated runs → Codex.

And in every single case: **install the NVIDIA skills for the libraries you use.** The harness may change; the skills come with you, and your GPU works either way.

<!-- fold:break -->

## The Bigger Picture

<img src="_static/robots/finish.png" alt="Finish Robot" style="float:right;max-width:240px;margin:20px;" />

This module's through-line is worth saying plainly. The harness layer is where the agent industry is innovating fastest, and NVIDIA's position is not to pick the winner — it's to **drive the technology forward together with the ecosystem**:

- **NemoClaw** makes open harnesses safer (Module 6)
- **Nemotron** gives every open harness a frontier-class engine (Modules 1–5)
- **Verified Skills** make every harness — open or closed — a first-class way to put NVIDIA GPUs and CUDA-X libraries to work (this module)

Open, portable, verifiable. Capability that travels.

<!-- fold:break -->

## The Full Workshop Arc

<div class="dx-bento dx-reveal">
  <div class="dx-cell"><h4>MODULE 1</h4><span class="dx-big">Report agent</span>Tool selection and scoping</div>
  <div class="dx-cell"><h4>MODULE 2</h4><span class="dx-big">RAG help desk</span>Data access boundaries</div>
  <div class="dx-cell"><h4>MODULE 3</h4><span class="dx-big">Evaluation</span>Adversarial test cases</div>
  <div class="dx-cell"><h4>MODULE 4</h4><span class="dx-big">Custom CLI agent</span>HITL + command allowlists</div>
  <div class="dx-cell"><h4>MODULE 5</h4><span class="dx-big">Deep agent</span>Container isolation + resource limits</div>
  <div class="dx-cell"><h4>MODULE 6</h4><span class="dx-big">Hardened agent</span>Kernel enforcement + continuous evaluation</div>
  <div class="dx-cell"><h4>MODULE 7</h4><span class="dx-big">The harness layer</span>Context tax + portable, verified skills</div>
  <div class="dx-cell is-wide"><h4>MODULE 8 - UP NEXT</h4><span class="dx-big">Agent routing</span>The right model for every call - tokenomics + NeMo Switchyard</div>
</div>

<!-- fold:break -->

## More Resources

- 📦 [NVIDIA Agent Skills repo](https://github.com/NVIDIA/skills) — the verified catalog; new skills sync daily
- 📖 [NVIDIA Skills documentation](https://docs.nvidia.com/skills) — verification pipeline, skill cards, signing
- 📝 [NVIDIA Verified Agent Skills blog](https://developer.nvidia.com/blog/nvidia-verified-agent-skills-provide-capability-governance-for-ai-agents/) — capability governance deep dive
- 🧩 [Agent Skills specification](https://agentskills.io) — the open spec behind the portability
- 🥧 [pi](https://github.com/badlogic/pi-mono) — the minimal harness that inspired Exercises 2 and 5
- 📜 [Hermes](https://hermes-agent.nousresearch.com) — the self-improving harness you drove in the lab; see the [NemoClaw-for-Hermes blueprint](https://build.nvidia.com/nvidia/nemoclaw-for-hermes-agent)
- 🦞 [OpenClaw docs](https://docs.openclaw.ai) — your Module 6 harness
- ⚡ [RAPIDS cuDF docs](https://docs.rapids.ai/api/cudf/stable/) — the library behind your Exercise 4 speedup
- 🚀 Keep an eye on [build.nvidia.com](https://build.nvidia.com) — agent demos built on these skills (including cuOpt) are landing soon
- 🛤️ [NeMo Switchyard](https://github.com/NVIDIA-NeMo/Switchyard) — route every call to the right model; the subject of Module 8

> **Module 7 complete!** Your agents have engines, cars, and a garage full of verified parts. One thing is still welded in place: every call uses the same engine. **Module 8 - Agent Routing** hands your harness a switchyard — the right model for every call.
