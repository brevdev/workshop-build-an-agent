<div class="dx-hero" data-eyebrow="MODULE 08 / 05 - WRAP UP" data-title="You know what every call costs. And who should answer it." data-sub="You leave with a portfolio and a way to defend it - not a favorite model." data-meta="TAKEAWAY::use both, efficiently|NEXT::go build"></div>

You came into this module with seven agents and one hardwired brain. You leave with a model pool, a meter, and a number you generated yourself.

<!-- fold:break -->

## What Your Exercises Map To

Every module here ends the same way — by pointing at where the lab lives in the real ecosystem:

| Lab exercise | Production counterpart |
|---|---|
| **1. The bill meter** | Cost observability: per-call token accounting, priced and attributed by model, next to latency |
| **2. Hand-rolled classifier** | The internals of Switchyard's `llm_classifier` — judge model, verdict parsing, fail-up defaults, session affinity |
| **3. libsy stage router** | In-process routing inside an agent framework: the middleware surfaces LangChain and LiteLLM named at launch, and the shape your own loop takes today |
| **4. `routes.toml` gateway** | The deployed pattern — Kong AI Gateway serving it natively, Cognition running a Switchyard router inside Devin Desktop, Nous wiring it into Hermes |
| **5. The scoreboard** | LangChain's 145-task benchmark method: matched configurations, one workload, cost and accuracy reported together |

<!-- fold:break -->

## The Decision Framework, One Last Time

When someone asks "should we route?", you now have a real answer — and it's usually a smaller one than they expect:

- **No router?** → `passthrough`. A router that doesn't route is still a nameable configuration, and it's your control row.
- **Need a baseline?** → `random`. A weighted split is an A/B test, and you can't credit the router if you never ran it.
- **Content decides?** → `llm_classifier`. Pay the judge, and put its cost on the receipt.
- **Tool signals suffice?** → `stage_router`. Free evidence, zero tax, and it wants long tool-heavy sessions.
- **Cheap-first policy?** → escalation mode. Start every session weak, escalate on sustained trouble, never de-escalate.
- **Tuning-free plateaus?** → a learned router — and you already know how to train (Module 4).

And in every case: **the router is a choice, so measure it like one.**

<!-- fold:break -->

## Honest Limits

<img src="_static/robots/party.png" alt="Celebration Robot" style="float:right;max-width:240px;margin:20px;" />

Four things this module can't promise you, said plainly.

<!-- CALIBRATE: every benchmark figure below is LangChain's published 145-task deep-agent routing
     run (measured Aug 2026), re-verified at the calibration pass alongside the intro page's copies:
     93/7 is a share of CALLS; 21% is the judge's share of the ROUTED run's own spend; ~700 ms is
     per turn; the 6-point giveback is 86.0% -> 80.0% ABSOLUTE accuracy, not a fraction of the
     baseline. The lab ranges (83/17 to 92/8 mix, a few percent tax) are this module's own measured
     runs - see the lab page's Exercise 2 and 5 notes. -->

**Routing quality is workload-specific.** Your split, your savings, and your accuracy giveback are properties of *your* task mix. The 93/7 call share in LangChain's benchmark is their agent on their 145 tasks; your lab suite landed somewhere near 83/17 to 92/8 and moved between runs.

**Saturated benchmarks flatter routers.** When every strategy scores 12/12, the cheap one wins on cost by default — and that's exactly what your Exercise 5 table showed. A suite that can't separate two models can't price accuracy either, and the first thing to harden is the suite.

**The judge is spend and latency.** Content routing buys its decision with a model call: a few percent of the routed bill in your lab, 21% of the routed spend and roughly 700 ms per turn in LangChain's published run, and at the gateway it hides in the yard's books rather than on your receipt. Stage routing avoids it entirely — when your workload gives it something to read.

**A six-point accuracy giveback is a *choice*.** That's the benchmark's headline trade, and it's obviously right for bulk summarization and obviously wrong for clinical coding. Nothing in the router tells you which one you're building; your eval suite does.

And one about the software itself: **NeMo Switchyard is young.** Upstream describes it as pre-alpha, "evolving rapidly", with the API and algorithms "expected to change significantly before we reach v1.0", under a plain banner: *"Experimental software. Not for production use."* This module pins a tested version so everything runs as printed. The routing concepts are older and steadier than the package — but read the release notes before you take this to production.

<!-- fold:break -->

## The Portfolio Answer

Tokenomics forced a debate — frontier **or** open — and this module's answer is *both, efficiently*. Open models where they're efficient, which is most calls. Frontier where it's genuinely necessary, which is few. Rebalanced as models improve, because open models improve monthly and a rebalance is a `routes.toml` edit plus an eval run. Always under a suite.

The honest coda: sometimes the right mix **is** 100% frontier. The point was never that routing wins — it's that the router and the suite let you *know*, instead of guessing and calling it strategy.

<!-- fold:break -->

## The Bigger Picture

NVIDIA's position across this whole workshop has been one bet, restated at every layer: keep it open, and make capability travel.

- **Nemotron** gives the portfolio's efficient side a frontier-class floor (Modules 1-5)
- **NIM** serves those weights anywhere — hosted, your DGX, your laptop (Module 2)
- **NemoClaw** makes open agents safe to run at all (Module 6)
- **Verified Skills** make any harness a first-class way to drive NVIDIA GPUs (Module 7)
- **NeMo Switchyard** makes the mix rational — per call, per session, per config file (this module)

Capability that travels, now with a dispatcher.

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
  <div class="dx-cell is-wide"><h4>MODULE 8 - YOU ARE HERE</h4><span class="dx-big">The model portfolio</span>Every call routed to the model that should answer it - measured, not guessed</div>
</div>

<!-- fold:break -->

## More Resources

- 🛤️ [NeMo Switchyard on GitHub](https://github.com/NVIDIA-NeMo/Switchyard) — Apache-2.0, the source of truth; start with [Getting started](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/getting_started.md)
- 🧭 [Core concepts](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/core_concepts.md) — clients, targets, routes, in the library's own words
- 🔀 [Routing algorithms overview](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/routing_algorithms/overview.md) — every family from the taxonomy page, with their knobs
- 📄 [TOML schema reference](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/reference/toml_schema.md) — every key you filled in during Exercise 4, and the ones you didn't
- 📝 [Route AI agent workloads across models](https://developer.nvidia.com/blog/route-ai-agent-workloads-across-models-with-nvidia-nemo-switchyard/) — NVIDIA's technical launch post
- 📰 [Nemotron 3.5 Lightning and NeMo Switchyard](https://blogs.nvidia.com/blog/nemotron-lightning-switchyard-rtx-dgx/) — the launch story, RTX through DGX
- 📊 [LangChain's agent-routing benchmark](https://www.langchain.com/blog/switchyard-agent-routing-benchmark) — the 145-task run behind every headline number in this module
- 🏭 [Boomi: Why Open Model Routing Matters](https://boomi.com/blog/why-open-model-routing-matters/) — routing to a fine-tuned specialist, in production
- ⚡ [Nemotron 3.5 Lightning on build.nvidia.com](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b) — your efficient tier's model card, with the deploy tab for running it yourself

> **Congratulations!** You've completed the Build-an-Agent workshop — all eight modules, from your first ReAct loop to the dispatcher that decides which brain answers each call. Your agents have engines, cars, a garage full of verified parts, *and* a switchyard. Go build.
