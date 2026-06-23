<div class="dx-hero" data-eyebrow="MODULE 07 / 06 - WRAP UP" data-title="You know what was running your agents." data-sub="You leave with a framework for choosing harnesses - not a favorite." data-meta="TAKEAWAY::context-tax framework|NEXT::keep skills with you"></div>

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
- **Embedding an agent in a product you must fully control?** → OpenCode or LangChain Deep Agents.
- **Every token is precious, or you bet on the model?** → pi.
- **Maximum out-of-box capability, cost secondary?** → Claude Code; computer-use heavy → Codex.

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

Congratulations — you've completed the Agentic AI Learning Path's harness module. Your agents have engines, cars, *and* a garage full of verified parts.
