# Module 8 — Agent Routing (NeMo Switchyard): Design & Scaffolding

**Workshop:** NVIDIA Build-an-Agent (DevX Learning Path)
**Status:** Design proposal — pre-implementation (no repo changes made)
**Date:** 2026-08-11 · **Rev 2:** 2026-08-13 — tokenomics framing strengthened per review · **Rev 3:** 2026-08-13 — churn-mitigation strategy added (§8b) · **Rev 4:** 2026-08-13 — Super-as-frontier-stand-in note (required Ex1 dx-aside) · **Rev 5:** 2026-08-13 — lab unified around the **Routing Client** app tile (dormant-client unlock arc, §4c spec)
**Drafted by:** Claude Code brainstorming session with edwli@nvidia.com

---

## 0. What was verified first (grounding)

**NeMo Switchyard is real and launched essentially today** (2026-08-11, alongside Nemotron 3.5 Lightning — everything below is grounded in the sources at the end, not model memory). The facts that shape the module:

- **What it is:** an Apache-2.0, open-source **model-routing library for AI agents** at [github.com/NVIDIA-NeMo/Switchyard](https://github.com/NVIDIA-NeMo/Switchyard). It routes each step of an agent workflow to the most capable-and-efficient model based on content, agent progress, cost, and infra signals.
- **Three runtime surfaces:** `libsy` (embeddable SDK — construct targets + algorithms in-process), **Switchyard Server** (a standalone OpenAI-compatible LLM gateway configured by `routes.toml`, speaking OpenAI Chat / Anthropic Messages / OpenAI Responses to backends incl. **NIM, vLLM, Ollama**), and a **launcher** (`switchyard launch claude --model switchyard`) that starts a harness pointed at an embedded router. Install: `uv tool install --python 3.12 "nemo-switchyard[cli]"`.
- **Core vocabulary:** `llm_clients` (endpoint + wire format + credential env) → `targets` (upstream model id + client) → `routes` (a *client-visible model id* + the algorithm that picks targets). An agent selects a route the way it would select a model — which means **existing agent code becomes multi-model by changing only `base_url` and `model`**. That's a gift for a workshop.
- **Routing algorithms (tuning-free):** `passthrough`, `random` (weighted A/B), `llm_classifier` (small judge picks weak/strong; `mode="capability"` with `base_threshold`, or `mode="escalation"` with `escalation.confirmations`, session affinity options), `stage_router` (routes on tool-result/progress signals with `confidence_threshold`, no extra LLM call). **Tunable:** a *prefill router* trained on the model's residual stream to predict per-model success — conceptually rich, too heavy for this lab (teach it, don't run it).
- **Killer numbers to motivate with:** LangChain's Deep Agents benchmark (145 multi-step tasks, ~6.3 model calls each): frontier-only 86.0% accuracy at $11.45/run; **routed 80.0% at $3.00 with only 7% of calls hitting the frontier model — a 74% cost cut**; efficient-only 77.7% at $0.72. Honest caveats: ~6-point accuracy tradeoff, judge adds ~700ms/turn and 21% of routed spend. Boomi hit 100% domain-routing accuracy sending 59% of traffic to a 5× faster **fine-tuned** model; Cognition cut mean cost ~28% on FrontierCode.
- **Nemotron 3.5 Lightning** (30B MoE, A3B) launched with it — on build.nvidia.com as a NIM, Hugging Face, OpenRouter; runs locally on RTX / **DGX Spark** / DGX Station / Jetson. It's the natural "efficient" target for the lab and keeps the whole model pool inside the learner's existing `NVIDIA_API_KEY`.

**Repo conventions to match** (from `.devx/7-agent-harnesses/`, the workshop module map, and the M2 NIM migration): ~7 doc pages per module (`secrets` → intro → 2 concept pages → lab → wrap-up), ~8–10k words total, dx- widgets (hero/bento/island/quiz/bet/term/peek), hand-authored dark SVGs (no mermaid — ARM64 constraint), a two-track lab (`routing_lab.py` with `# TODO: Exercise Na` blanks + notebook twin with 💡 accordions + `.answers.*`), `--exercise N` runner, per-blank 🆘 peeks, "Run it" terminal buttons, a closing 🧾 receipt, GPU-optional with explicit CPU fallback, and a `/module-8` tutor skill + hub-skill updates.

One structural fact that matters: **Module 7's wrap-up currently declares the workshop finished** ("Congratulations! You've completed… all seven modules") and renders a 7-cell arc bento. Module 8 requires touching that page — edits scoped in §7.

---

## 1. Three candidate framings (with a recommendation)

**Option A — "The Fourth Component, Completed" (recommended spine).** Module 1 taught the four agent components: model, tools, memory, **routing** — where routing meant *control flow* (which step next). Every module since assumed the **model** slot holds exactly one model, hardwired (`MODEL_NAME = "nvidia/nemotron-3-super-120b-a12b"` appears in every lab). Module 8 reveals the last upgrade: the model slot becomes a *pool*, and routing grows a second meaning — not just *what to do next* but ***which brain does it***. This is a full-circle callback that makes the whole path feel designed from the start, and it extends M7's engine/car metaphor perfectly: *M7 taught you the car is not the engine; M8 stops welding the engine in.* The rail-switchyard metaphor (requests as trains, models as locomotives, the classifier as dispatcher) is native to the product name and extremely teachable for newcomers.

**Option B — "Agent Economics."** Lead with cost/latency as first-class engineering: agents make ~6 model calls per task, most calls are easy, frontier pricing makes every turn expensive — then routing is the lever, verified by measurement. *Trade-off:* the strongest motivation numbers live here, but as a spine it reads like a pricing lesson, dates quickly as prices shift, and undersells the capability story (local/private/faster, specialists). Better as the module's *measurement thread* than its identity.

**Option C — "One Agent, Many Brains" (heterogeneous model systems).** Architecture-first: gateways, fleets of specialists + generalists, local + cloud hybrids, Switchyard-as-infrastructure beside NIM/Dynamo. *Trade-off:* most production-real, but abstract for developers new to agents — it jumps to infra before the per-call intuition lands. Better as the *closing production mapping* (every module ends with one).

**Recommendation (Rev 2): A remains the structural spine; B is promoted from instrument to the module's motivation layer.** Tokenomics — the unit economics of running agents on tokens — is the debate every adopting company is actually having, and it is being litigated as a binary: frontier models *or* open models. The module's stated thesis, in NVIDIA's voice: **that binary is false — use both, efficiently.** The module now opens on the bill (worked math, not vibes), names the frontier-vs-open debate fairly, and dissolves it with the observation the whole lab then proves: the debate silently assumes every call is equally hard, and your own agent transcripts show it isn't. Option A still supplies the pedagogy skeleton (the fourth component completed, the M1 full-circle) because a components arc survives price changes; Option C still closes as the production mapping. Practically: **motivation = tokenomics (B) · mechanics = the fourth component (A) · destination = the model portfolio in production (C).** The lab's recurring artifact is the **model-bill meter** (the sequel to M7's context-tax meter), and every receipt now extrapolates to at-scale dollars.

---

## 2. Module identity

| | |
|---|---|
| **Title** | **Module 8 — Agent Routing** ("Frontier quality, open-model economics — the right model for every call") |
| **Thesis** | Tokenomics is the forcing function. Frontier vs open is a false binary — **use both, efficiently**; routing is how. |
| **Directories** | `.devx/8-agent-routing/` · `code/8-agent-routing/` |
| **Time** | 2–3 h total; lab ~95 min: Ex0 client launch + 5 exercises that progressively unlock the Routing Client |
| **Final artifact** | The **Routing Client** — a JupyterLab app tile (per the Simple Agents / NemoClaw / Deep Agents Client precedent): a live, dx-themed switchyard UI where queries visibly route between models and the savings counter runs; ships dormant, unlocked exercise by exercise (§4c) |
| **Model pool** | Strong: `nvidia/nemotron-3-super-120b-a12b` (the workshop's default since M1, **playing the frontier role as an explicit, stated stand-in** — required Ex1 dx-aside) · Efficient: `nvidia/nemotron-3.5-lightning-30b-a3b` (new, thematic) · Classifier: the efficient target itself (no third model, no added cost surprise) |
| **Secrets** | `NVIDIA_API_KEY` only — no new keys (Anthropic-in-the-pool offered as an optional dx-peek since Switchyard speaks `anthropic_messages`, never required) |
| **Hardware** | Main path: CPU-only (hosted endpoints). GPU (A100/Spark): optional local-NIM target in Exercise 4. Sandbox: hosted-only + config `--dry-run` path (details in §6) |
| **Prereqs** | M1 (components, ReAct), M7 (harness lab agent is reused); M2/M3/M4/M5 concepts are called back but not required to run |

---

## 3. Page-by-page outline (`.devx/8-agent-routing/`)

Seven files, mirroring M7's shape and word budget (~8.5k words total).

### `_sidebar.md`

```
* [Setting up Secrets](secrets.md)
* [The Tokenomics Problem](intro_agent_routing.md)
* [How Routers Decide](routing_decisions.md)
* [Meet NeMo Switchyard](meet_switchyard.md)
* [The Routing Lab](routing_lab.md)
* [Wrapping Up](evaluating_routing.md)
```

### `secrets.md` (~280 words)

Standard module secrets page: reuse `NVIDIA_API_KEY`, verify with the usual curl against `integrate.api.nvidia.com`. One new note: the lab's gateway exercise reads the key via `api_key_env` from the environment, so export it in the terminal you run `switchyard-server` from — worth one dx-aside because it's the #1 predictable failure.

### `intro_agent_routing.md` — "The Tokenomics Problem" (~1,100 words)

- **dx-hero:** eyebrow `MODULE 08 / 01 - THE TOKENOMICS PROBLEM`; title "Your agent runs on tokens. Someone pays for every one."; sub "Seven modules, seven agents, one hardwired brain — paying frontier prices for commodity work."; meta `TAKEAWAY::use both, efficiently|NEXT::how routers decide`.
- **Cold open — the bill:** agents are token machines (~6.3 model calls per task in LangChain's agent suite), and every one of this workshop's agents since M1 pinned `MODEL_NAME` to a single model for *every* call. Define **tokenomics** for newcomers in one plain sentence: the unit economics of LLM work — cost and latency per call, per task, per user, per month — the number that decides whether an agent feature ships or dies in review. Then the M7 continuity line: *"Module 7 taught you every token has a **cost** (the context tax). Module 8 teaches you every token has a **price** — and the price depends on who generates it."*
- **dx-island "TOKENOMICS, CONCRETELY":** the worked math, from the real benchmark and labeled as such: $11.45/task frontier-only vs $3.00 routed → at 1,000 tasks/day, ~$4.2M/yr vs ~$1.1M/yr — with the accuracy giveback (86.0% → 80.0%) stated in the same breath. Measuring, not marketing.
- **The frontier-vs-open debate** (its own section — name the industry moment, state both cases fairly): *Team Frontier* — maximum capability, zero infra, but per-token pricing, data leaves your walls, single-vendor dependency (the role Nemotron Super 120B will play in your lab — see the "stand-in" aside in Exercise 1). *Team Open* — Nemotron-class weights you run anywhere: cheap, private, customizable (your M4 specialist is exactly this), but a capability ceiling on the hardest calls. Companies are litigating this **as a binary**. The pivot sentence the whole module hangs on: **the debate silently assumes every call is equally hard — and your own agent transcripts prove it isn't** ("summarize this tool output" vs. "plan a five-step investigation").
- **NVIDIA's answer — use both, efficiently:** a *portfolio*, not a pick. Commodity calls go to open models (most calls), frontier calls go to frontier models (few calls); 93/7 is what that split actually measured in practice. The switchyard metaphor lands here, introduced once and reused everywhere: a rail switchyard doesn't make locomotives faster — it stops you hauling mail with your heaviest engine. Requests = trains, models = locomotives, dispatcher = the routing algorithm. Extends M7's engine/car: *you learned the car is not the engine; now stop welding the engine in.*
- **The M1 full-circle moment** (kept, its own section): the four components diagram returns; routing in M1 = which *step* next (control flow); routing in M8 = which *model* answers (model routing). Explicit disambiguation — deliberately, because the workshop has now used "routing" three ways (M1 control flow, M6 policy, M8 performance). A **dx-quiz** here: "Module 1 also had 'routing.' What did it decide?" (options: which model / which tool or step ✓ / which user / which GPU).
- **dx-bet** (kept): "An agent benchmark routed between a 30B open model and a frontier model. What fraction of calls actually needed the frontier?" — 75% / 40% / 20% / **7%** ✓.
- **Diagram 1** (`one_model_vs_routed.svg`): same agent loop twice — left, every call → 120B at frontier prices; right, calls fanning through a dispatcher to 30B (most) / 120B (few), with % *and* $ labels.
- Close with the module promise list — measure the bill → route by hand → route with libsy → route at the gateway → prove the savings — and the forward link.

### `routing_decisions.md` — "How Routers Decide" (~1,600 words; the conceptual core)

A taxonomy page structured like M7's harness landscape, organized around one question: **what evidence does the router look at, and when?**

1. **Static splits** (`random` + weights): no evidence at all — but the honest baseline and the A/B instrument. Callback to M3: you can't credit the router if you never ran the split.
2. **Content-based** (`llm_classifier`, capability mode): a small LLM reads the request and scores difficulty against `base_threshold`. Teach the **router-tax** concept immediately (the M7 context-tax reflex): the classifier is itself an LLM call — ~700ms and real spend (21% of the routed bill in LangChain's run). Sub-concepts: session affinity (don't flap mid-conversation), `message_hash_fallback`, threshold as a *policy dial* not a magic number.
3. **Signal-based** (`stage_router`): no extra LLM call — reads recent tool activity to infer the agent's *stage* (exploration vs. implementation) and picks efficient vs. capable. Connects directly to the agentic loop the learner built in M7 Ex1: the signals are the `ToolMessage`s already flowing through it.
4. **Escalation** (`llm_classifier`, escalation mode): start cheap, escalate on *sustained difficulty* (`confirmations=2`), never de-escalate mid-task. The "junior engineer with a senior on call" analogy. Note the constraint from the benchmark: escalation needs multi-turn trajectories to read.
5. **Learned routers** (prefill/tunable): train a small head on the model's residual stream to predict each target's success likelihood. Taught as the frontier, not exercised — with the **M4 callback**: same decision as prompt-vs-train, one level up ("when tuning-free routing plateaus on your workload, you train — and your M4 GRPO experience is exactly the muscle").

- **The M6 contrast section (load-bearing):** Module 6's Privacy Router routes on *policy* — the operator decides who **may** answer, and injects credentials; Module 8 routes on *performance* — the system decides who **should** answer. They compose (operator policy outside, Switchyard inside), and conflating them is the most likely learner confusion in this workshop's universe. (This also keeps consistency with the M6 "Privacy Router ≠ content classification" framing — M8's `llm_classifier` *is* content classification, which is exactly why the contrast is worth a section.)
- **Specialists change the game** (M4 callback): the portfolio isn't only weak/strong generalists — Boomi sent 59% of traffic to a 5× faster *fine-tuned* model with 100% domain accuracy. "Customize small (M4), then route to it" is the economic argument for fine-tuning, completed — and it's open models that make owning a specialist possible at all.
- **Diagram 2** (`routing_signals.svg`): the four decision families laid on an axis of "what evidence, at what cost."
- **dx-quiz** (scenario-picker, mirroring M7's harness-picker): "Your agent does long tool-heavy sessions and you can't afford an extra LLM call per turn — which algorithm?" (llm_classifier / **stage_router** ✓ / random / passthrough, each with feedback lines).

### `meet_switchyard.md` — "Meet NeMo Switchyard" (~1,000 words; the "Why NemoClaw"-style product page)

- What ships: **libsy** (embed routing in your process), **Switchyard Server** (an OpenAI-compatible gateway — your agent asks for model `"switchyard"` and the yard picks the locomotive), **launcher** (`switchyard launch claude --model switchyard` — the M7 callback writes itself: *it launches the harnesses you toured*).
- **The three nouns** with a worked `routes.toml` teardown, annotated line by line: `llm_clients` (endpoint + wire format + `api_key_env`) → `targets` (upstream model id + client) → `routes` (public model id + algorithm). Emphasize the architectural point the docs make: routing logic is separated from providers, so you can swap model endpoints without rebuilding the app — the same "decouple the layer" lesson as M7, one layer down. This is what makes the frontier/open portfolio *governable*: open models improve monthly, so "should we rebalance the mix?" becomes a `routes.toml` edit plus an eval run — not a migration.
- Wire-format conversion (OpenAI Chat ⇄ Anthropic Messages ⇄ Responses) and backends (NIM, vLLM, Ollama, any OpenAI-compatible) — one dx-island: "the gateway is also an adapter."
- **Where it sits in the NVIDIA stack:** Nemotron models to route *to*, NIM to serve them, Dynamo/NeMo Relay adjacency, and the partner ecosystem (LangChain middleware, LiteLLM plugin, Kong gateway, Cognition's Devin Desktop, **Nous Hermes — the harness from your M7 lab — routes with it**).
- **Version-stamp dx-aside** (churn honesty — workshop brand): "This module was built and tested against Switchyard vX.Y, pinned in the lab, so everything here runs as printed. Switchyard is young and moving fast: the concepts on this page are stable, but exact imports and flags may differ in the latest release — the docs link is the source of truth." Framed the M7 way: the routing layer moving fast is *evidence of the thesis*, not a caveat to hide.
- **Diagram 3** (`switchyard_architecture.svg`): client → route(algorithm) → targets → llm_clients → [build.nvidia.com | local NIM | any OpenAI-compatible], with the in-process (libsy) vs. gateway (server) placement shown as two brackets around the same core.
- **dx-bet:** "What did routing cost Cognition in accuracy-per-dollar on FrontierCode?" — leads into the honest-numbers island (Cognition ~28% cheaper than the Opus 5 baseline at 50.6%).

### `routing_lab.md` — the hands-on page (~2,600 words; full design in §4)

Restructured (Rev 5) around the Routing Client unlock arc: the page opens with the dormant client (Ex0), each exercise section ends with an **"Unlock it"** beat (what just came alive in the UI) alongside the CLI **"Run it"** verifier, and the page's dx-term mockups are complemented by annotated client screenshots.

### `evaluating_routing.md` — "Wrapping Up" (~800 words)

- **"What your exercises map to"** table (the M6/M7 convention): Ex1 meter → production cost observability; Ex2 hand-rolled classifier → `llm_classifier` internals; Ex3 libsy → LangChain `SwitchyardRoutingMiddleware` / LiteLLM plugin; Ex4 gateway → Kong/Devin Desktop/Hermes deployments; Ex5 scoreboard → LangChain's 145-task benchmark method.
- **The decision framework** (M7 tradition): *No router → passthrough. Need a baseline → random. Content decides → llm_classifier. Tool signals suffice → stage_router. Cheap-first policy → escalation. Tuning-free plateaus → learned router (and you know how to train).*
- **Honest limits** (M3 voice): routing quality is workload-specific; saturated benchmarks flatter routers; the judge is spend and latency; a 6-point accuracy giveback is a *choice*, and your eval suite — not the router — is what makes it an informed one.
- **The portfolio answer** (the thesis, restated as the takeaway): tokenomics forced a debate — frontier or open — and the module's answer is *both, efficiently*: open models where they're efficient (most calls), frontier where it's necessary (few calls), rebalanced as models improve, always under an eval suite. Honest coda: sometimes the right mix **is** 100% frontier — the point is that the router and the suite let you *know*, instead of guessing.
- **The bigger picture:** NVIDIA's position restated — open models (Nemotron) give the portfolio's efficient side a frontier-class floor, open serving (NIM) runs them anywhere, open safety (NemoClaw), open skills (Verified Skills), and now open routing (Switchyard) makes the mix rational: *capability that travels, now with a dispatcher.*
- **The updated 8-cell workshop-arc bento** with Module 8 as "YOU ARE HERE," and the corrected congratulations block ("all eight modules").
- **Resources:** Switchyard GitHub + docs, the two NVIDIA blogs, LangChain benchmark post, Boomi post, Nemotron 3.5 Lightning model card on build.nvidia.com.

---

## 4. The Routing Lab — one product, five unlocks

**The unifying frame (Rev 5, per review):** the lab is no longer five standalone demos — the learner is **shipping the brain of the Routing Client**, a JupyterLab app tile (§4c) that opens a live, dx-themed switchyard: type a query, watch it get dispatched down a track to a model, watch the bill and the savings counter run. The client ships complete but **dormant** — every panel is locked and labeled with the exercise that powers it, and a status strip tracks `systems online: N/5`. Each exercise therefore ends not with console output but with a capability visibly coming alive in the UI; the UI itself is the syllabus. The CLI runner (`python routing_lab.py --exercise N`) remains as the per-exercise verifier and the headless/sandbox fallback.

**Design rule (non-negotiable): the client is a window, not a wizard.** Every routing decision is computed by learner-edited code in `routing_lab.py`; the provided UI contains zero routing logic and only renders events that code emits.

**Files:** `code/8-agent-routing/routing_lab.py` (+ `.ipynb` twin, + `.answers.py` / `.answers.ipynb`), `routing_client/` (the provided UI — §4c), `routes.toml` (Ex4's blank, shipped as commented skeleton `routes.toml.template`), `test_data/routing_tasks.jsonl`, `scripts/serve_local_nim.sh`, `scripts/install_switchyard.sh`, `README.md`. Two-track discipline as M7 (page follows the `.py`; notebook has the same blanks with 💡 accordions plus a final launch-the-client cell; sub-exercise labels match `# TODO: Exercise …` markers exactly).

### Exercise 0 — "Open the yard" (~5 min, no blank)

Click the **Routing Client** tile. The yard renders dormant: strategy chips greyed out (each naming the exercise that unlocks it), the bill meter dark, `systems online: 0/5`. The learner sees the whole build before writing a line. The client doubles as the env check: it verifies `NVIDIA_API_KEY` and shows a red banner with the exact fix if it's missing — failures surface here, in minute five, not mid-exercise.

**The shared harness:** the lab ships a ~60-line `build_lab_agent()` — a pared copy of the M7 minimal harness (ChatNVIDIA + 4 tools + the loop), *provided, not blanked* (they built it last module; the page says exactly that). All exercises route *this* agent, so the module stands alone while feeling like a direct sequel.

**The shared workload:** `routing_tasks.jsonl` — 12 tasks: 6 "commodity" (extraction, reformatting, single-tool lookups — **verifiably checkable** with exact/contains assertions) and 6 "frontier" (multi-step tool use, synthesis, tricky reasoning — checked by rubric). Verifiable checks are a deliberate **M4 callback** (RLVR: "verifiable rewards, now verifiable routing") and keep Ex5 fast, cheap, and mostly deterministic.

### Exercise 1 — "Two engines, one bill" (~15 min)

Baseline instrumentation; the model-bill meter is this module's context-tax meter.

- **dx-aside "A stand-in for the frontier" (required copy, per review):** in this lab, Nemotron Super 120B *plays the frontier role* — the expensive-but-intelligent tier relative to Lightning — so every learner can run both tiers with the one free `NVIDIA_API_KEY` and no closed-model account. In the real world, the strong slot is often a closed-source frontier model — OpenAI's or Anthropic's — at materially steeper per-token prices: the routing logic and the economics are identical, the price gap just widens (which makes routing pay off *more*, not less). Switchyard doesn't care either way — `anthropic_messages` is a first-class client format, so swapping the strong target for a Claude model is a two-line `targets` edit (shown in the optional dx-peek on the Meet Switchyard page) with zero changes to the rest of the module.
- **1a** — construct the two model clients from a `MODEL_POOL` dict (strong = Super 120B, efficient = Lightning 30B) with the same ChatNVIDIA settings discipline M7 taught (`max_completion_tokens`, `timeout`). 🆘 shows the two-liner + the gotcha (forgetting per-model pricing metadata breaks 1b).
- **1b** — `bill_call()`: pull `usage_metadata` off each response, price it against a `PRICING` table, accumulate per-model tallies + wall-clock latency. 🆘 explains why measuring *both* halves (tokens and latency) matters — Lightning's headline is 4× output speed, and the meter is what turns that from marketing into your own number.
- **Run it:** `--exercise 1` runs the 12-task suite twice (strong-only, efficient-only) and prints a dx-term-style scoreboard: accuracy / cost / p50 latency per config. Expected shape (numbers illustrative — **calibrate real ones during implementation**, the M7 convention of printing exact expected output): strong ~11–12/12 but slowest and priciest; efficient ~9–10/12, ~5–10× cheaper, visibly faster. A dx-island then frames the gap (*"the whole module lives between those two rows"*), and a second island annualizes it — the same two rows extrapolated to 1,000 tasks/day and a year: the learner's first tokenomics table, the kind a platform team actually presents.
- **Client unlock (1/5):** the **Strong-only** and **Efficient-only** passthrough strategies go live, along with the bill ticker, per-query receipts, and the counterfactual line ("if this had gone frontier-only: $X"). The learner chats with either tier immediately and watches the gap accrue in real time.

### Exercise 2 — "Route by hand" (~20 min)

Demystify before the SDK — the M7 "build the loop yourself first" move.

- **2a** — `classify_difficulty()`: prompt the efficient model with a strict one-token contract (`COMMODITY`/`FRONTIER`), parse defensively (the M7 lesson: malformed output is normal; default to FRONTIER on parse failure — fail *up*, never down). 🆘 discusses the misroute asymmetry: a hard task sent weak fails the task; an easy task sent strong only wastes money.
- **2b** — `route_call()`: dispatch on the verdict, bill the classifier call too. The receipt now shows a third line — **router tax** — and the page connects it to M7's context tax by name.
- **Run it:** routed suite lands between the Ex1 baselines: most of strong's accuracy near efficient's cost, with the classifier's own cost printed honestly. A dx-quiz asks which single change most reduces router tax (a smaller classifier / caching by session ✓ / a longer prompt / lower temperature).
- **Client unlock (2/5):** the **Manual Classifier** strategy chip lights up and the yard animation starts actually switching tracks — query card pauses at the dispatcher, the verdict appears, the card rides the chosen track. Receipts gain the verdict + **router tax** lines, and "commodity" vs "frontier" example chips let the learner trigger divergent routing on purpose.

### Exercise 3 — "Routing as a library: libsy" (~20 min)

The same decision, production-grade and in-process.

- **3a** — build the Switchyard router: `LlmTarget("capable", …)` / `LlmTarget("efficient", …)` + `algorithms.stage_router(...)` (per the published LangChain integration shape; exact Python surface **pinned at implementation** — see §8 risks). The page contrasts it with Ex2: stage routing reads *tool signals you already produce* instead of paying for a classifier call.
- **3b** — wire the router into the lab agent's loop: one `router.select(...)`-style call per turn choosing which bound model invokes, plus a `[route → efficient]` trace print per turn (the lab's signature 🛠️-style visibility).
- **Churn armor (see §8b):** the SDK touches exactly one provided seam — a ~20-line `switchyard_shim.py` exposing `make_router()` / `pick_target()` — so the learner blanks call lab-owned names while the real SDK calls stay visible inside the shim and the 🆘 solutions; an upstream rename is a one-file fix with zero doc-page edits. If the pinned import breaks anyway, the runner falls back to a deterministic lab-owned mock router with a loud banner (the M6 audit lesson: the degraded path must still teach).
- **Run it:** a multi-turn tool-heavy task where early exploration turns route efficient and the synthesis turn routes capable — the trace makes the stage transition *visible*. dx-peek: the one-liner `SwitchyardRoutingMiddleware(router)` form for `create_deep_agent` — "your Module 5 deep agent takes this middleware verbatim; that's exactly the configuration LangChain benchmarked."
- **Client unlock (3/5):** the **Switchyard: Stage Router** strategy chip lights up, and agent mode (multi-turn, tool-using) joins the chat: the learner watches exploration turns ride the efficient track and the synthesis turn escalate, live, with the stage signals shown at the dispatcher.

### Exercise 4 — "The gateway: zero code changes" (~20 min + optional GPU sub-path)

Like M7 Ex3, **the blank is a file, not Python**: complete `routes.toml` from the shipped skeleton.

- **4a (everyone, CPU-safe):** fill in `[llm_clients.nvidia]` (openai_chat, `https://integrate.api.nvidia.com/v1`, `api_key_env="NVIDIA_API_KEY"`), `[targets.weak/strong]`, and `[routes.switchyard]` (`type="llm_classifier"`, `mode="escalation"`, `escalation.confirmations=2`). **Validate before serving** — `switchyard-server --config routes.toml --dry-run` — an explicit callback to M7 Ex5's validate-before-saving lesson. Then serve on `:4000`, `curl /v1/models`, and re-run the lab agent with only two changed values: `base_url="http://localhost:4000/v1"`, `model="switchyard"`. The page's headline moment: *the agent code didn't change; the model became a policy.* Escalation behavior is demonstrated with a scripted two-phase task (starts weak; watch the yard escalate after two confirmations).
- **4b (GPU path, optional):** add a second client + target pointing at a **local NIM** and make *it* the weak target — easy turns run on your own silicon (private, free, fast), hard turns escalate to the hosted 120B. Reuses M2's exact NIM runbook (`docker login nvcr.io`, `nim-cache` volume, the known-good `nemotron-3-nano-30b-a3b` NIM on the A100; Lightning's NIM noted as the newer alternative once verified on SM80). `watch -n 0.5 nvidia-smi` in a side terminal, the M7 Ex4 ritual: easy prompts light up *your* GPU, hard prompts don't. 🆘 covers the fallback explicitly: **no Docker/GPU → skip 4b entirely; 4a is the full exercise** — same shape as M7's "no GPU? pandas fallback" note.
- **Client unlock (4/5):** the **Gateway** toggle goes live — the client repoints its OpenAI client at `:4000` and the *same UI* now visualizes decisions made by the external `switchyard-server` (upstream-model attribution via the response `model` field; verify at impl, §8). On the 4b path, a **"YOUR GPU"** locomotive joins the yard with a live utilization badge (server-side `nvidia-smi --query-gpu` poll) — the in-UI version of the M7 watch ritual.

### Exercise 5 — "Prove it" (~15 min)

The M3 callback and the module's receipt.

- **5** — one blank: `routing_verdict()` — aggregate the suite results across the three configs (strong-only / efficient-only / routed) into the final scoreboard: accuracy, cost, frontier-call %, router tax, and the cost-per-point-of-accuracy line. Optional stretch inside the same blank's dx-peek: sweep `base_threshold` over {0.3, 0.5, 0.7} and print the three routed points — the threshold *is* the policy dial, and the learner watches the Pareto curve move.
- **Run it:** the closing 🧾 receipt, now with the portfolio and at-scale lines, e.g. `routed: mix 78/22 open/frontier · $0.41 vs $1.55 (−74%) · at 1k tasks/day: ~$12k vs ~$47k/mo · accuracy −1 task · router tax 9% of spend` (targets to calibrate at implementation). The closing paragraph lands the thesis in one line — *frontier quality where it's needed, open-model prices where it isn't: use both, efficiently* — followed by the honesty beat: *the router didn't earn that claim — your eval suite did.* Wrap-up page link.
- **Client unlock (5/5):** **Race mode** — the finale panel. The 12-task suite runs under the selected strategies; a leaderboard fills in live (accuracy · cost · frontier-% · router tax per strategy), the accuracy-vs-cost Pareto scatter renders point by point, and the final 🧾 receipt with the at-scale extrapolation caps it: `systems online: 5/5`. This screen is the module's closing artifact — the thing a learner screenshots.

**Timing:** 5+15+20+20+20+15 = 95 min (vs M7's 90 — the extra 5 is Ex0's client launch).

---

## 4c. The Routing Client — UX & architecture spec

**Precedent:** the workshop already ships three client tiles — Simple Agents Client (M2, Streamlit), NemoClaw Client (M6, Streamlit), Deep Agents Client (M5, React/Vite in `demo/`) — all `local-server` launcher tiles with `chatbot.svg`. The Routing Client is the fourth, registered identically.

**Layout:**

- **Center stage — the animated switchyard:** hand-authored dx-dark SVG yard. A query card enters, pauses at the **dispatcher** node (verdict / stage signals / threshold displayed), travels down a track to a **locomotive** (Efficient 30B · Strong 120B · Your GPU), and the response streams back along the return rail. This is the module's rail metaphor made literal, and the "clearly and visually shows routing" moment.
- **Header strip:** strategy picker chips (locked = greyed + "unlocks in Exercise N"), Gateway toggle (Ex4), session bill, and the headline counter: **"saved vs frontier-only: $X.XX (NN%)"**.
- **Left rail:** chat input + example query chips grouped **commodity** / **frontier** (so learners can trigger both tracks deliberately), plus agent-mode toggle (Ex3+).
- **Right rail:** per-query receipt log — model chosen, *why* (verdict/signals), tokens, latency, cost, counterfactual delta vs strong-only.
- **Bottom drawer:** Race mode (Ex5) — strategy leaderboard + accuracy-vs-cost Pareto scatter, rendered live as the suite runs.
- **Status strip:** `systems online: N/5` + health panel (endpoint reachability, switchyard install state, gateway liveness) — the M5-client "won't connect" lesson, productized.

**Architecture:**

- **Backend:** FastAPI + **SSE** (same-origin, no WebSockets — proxy-friendly on Brev/JupyterLab). Endpoints: `POST /query` (runs the learner's routing path, streams `route_decision` / `token` / `receipt` events), `GET /status` (unlock probe results + health), `POST /race` (Ex5 suite runner, streams leaderboard rows). Serves the static frontend from the same origin.
- **Frontend:** hand-authored vanilla JS/HTML/CSS **reusing `devx-theme.css`** — visually continuous with the doc pages, zero build step, no node_modules (deliberately *not* the M5 Vite pattern; ARM64 + postBuild-fragility lessons). **Descope option if implementation time gets tight:** Streamlit per the M2/M6 clients — loses the yard animation, keeps meters/receipts/race table.
- **Live unlocks:** the backend `importlib.reload`s `routing_lab.py` on each request and probes which `TODO`s are implemented (unfilled blanks raise a sentinel `NotImplementedError`); filling a blank updates the UI on the next interaction — **no client restart**. This is what makes the dormant→alive arc feel immediate.
- **The window-not-wizard contract, enforced structurally:** the client imports and calls only `routing_lab.py` functions (`bill_call`, `classify_difficulty`, `route_call`, `make_router`/`pick_target` via the shim, `routing_verdict`) and renders the event dicts they return. All 🆘 solutions therefore remain exactly as scoped in §4 — the UI adds zero new learner-facing API.
- **Gateway mode (Ex4):** the client swaps its in-process path for an OpenAI client pointed at `http://localhost:4000/v1`, `model="switchyard"`; upstream-model attribution read from the response `model` field (**verify at impl**; fallback: tail the server's route trace). Yard animation then labels the dispatcher "switchyard-server (external)" — teaching in-process vs gateway placement visually.
- **GPU badge (Ex4b):** server-side `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv` poll → utilization meter on the "YOUR GPU" locomotive.
- **Counterfactual math:** per query, re-price the same token counts at the strong tier's rates; label as an estimate (output length varies by model) — honesty convention.
- **Mock mode:** the §8b mock router surfaces in the UI as a "Demo (mock)" strategy — the client stays demo-able even with no key / broken SDK / no egress (sandbox story).

**Registration (`jp_app_launcher.yaml`):**

```yaml
- title: "Routing Client"
  source: http://localhost:$PORT/
  cwd: /project/code/8-agent-routing
  type: local-server
  args: [bash, -c, "bash routing_client/start_client.sh $PORT"]
  icon: /project/.devx/_static/img/chatbot.svg
  catalog: NVIDIA DevX Learning Path
```

**Scope guardrails:** the client is provided code, never learner-authored; it must degrade gracefully at every unlock level (locked ≠ broken); and its polish never gates the exercises — the CLI verifier is always sufficient to complete the module.

---

## 5. Code scaffolding tree

```
code/8-agent-routing/
├── README.md                      # module code readme (M7 pattern)
├── routing_lab.py                 # 5 exercises; TODO blanks 1a,1b,2a,2b,3a,3b,5
├── routing_lab.ipynb              # cell-per-exercise twin, 💡 accordions
├── routing_lab.answers.py         # answer keys (both tracks)
├── routing_lab.answers.ipynb
├── routes.toml.template           # Ex4's blank (commented skeleton)
├── routes.toml.answers            # completed reference config (incl. 4b local-NIM variant, commented)
├── switchyard_shim.py             # the ONLY file that imports the SDK (provided, ~20 lines — see §8b)
├── routing_client/                # the provided UI (§4c) — window, not wizard
│   ├── server.py                  # FastAPI + SSE; reload+probe routing_lab.py per request
│   ├── start_client.sh            # launcher-tile entry point
│   └── static/
│       ├── index.html             # dx-themed shell (reuses ../../.devx/_static devx-theme.css)
│       ├── client.js              # SSE consumer, unlock states, receipts, race mode
│       └── yard.svg               # the hand-authored animated switchyard scene
├── test_data/
│   └── routing_tasks.jsonl        # 12 tasks: 6 verifiable-easy, 6 rubric-hard
└── scripts/
    ├── install_switchyard.sh      # pinned pip versions + release-tagged server binary w/ sha256, --dry-run smoke test
    ├── smoke_switchyard.sh        # maintainer canary: fresh pinned install → dry-run answers TOML → 1 live routed call → drift warning
    └── serve_local_nim.sh         # thin wrapper over the M2 NIM runbook for Ex4b
```

`install_switchyard.sh` is deliberately a script (not inline page commands) so version pins live in one place — the npm-`n` incident taught this repo that unpinned toolchain installs rot on fresh builds. The server binary comes from a release-tagged GitHub artifact with a recorded sha256, never `cargo install` latest. `smoke_switchyard.sh` is the maintainer-side canary (§8b): run before events and on every version bump.

---

## 6. Deployment & fallback matrix (A100 / Spark / CPU / sandbox)

| Environment | Ex1–3, 5 | Ex4a gateway | Ex4b local-NIM target | Routing Client (§4c) |
|---|---|---|---|---|
| **Brev 1×A100 80GB** (primary) | ✅ hosted | ✅ | ✅ Nano-30B-A3B NIM (M2 known-good); Lightning NIM once verified on SM80 | ✅ launcher tile (same-origin SSE through the JupyterLab proxy, per the M2/M6 client pattern) |
| **DGX Spark (GB10, ARM64)** | ✅ hosted | ✅ (Rust binary builds on aarch64; **verify pip wheels**) | ⚠️ Lightning is launch-advertised on Spark — verify the local-serving path (NIM/other); else fall back to 4a | ✅ pure Python + static files, no arch concerns |
| **CPU-only** | ✅ hosted | ✅ both targets hosted | ⛔ page says so up front, M7-style | ✅ full experience (models are hosted anyway) |
| **NemoClaw/OpenShell sandbox** | ✅ if `integrate.api.nvidia.com` egress is in policy (modules 1–3 already work in-sandbox, so likely present; **confirm + extend the operator skill's egress policy** for `:4000` loopback and PyPI package) | ✅ pip-installed server, loopback only | ⛔ no Docker in sandbox — 4a is the path; worst case the M6 precedent applies (a canned trace/`--dry-run`-only mode still teaches the config) | ⚠️ one more forwarded port for the operator skill; "Demo (mock)" strategy keeps it alive even with restricted egress; CLI verifier is the guaranteed path |

---

## 7. Journey cohesion — callbacks, forward hooks, and files to touch

**Callback map (woven into pages above):**

| Module | Callback in Module 8 |
|---|---|
| M1 | Four components — the "routing" slot completed; control-flow routing vs model routing disambiguated (intro quiz) |
| M2 | Local-NIM runbook reused verbatim in Ex4b; "API catalog vs local NIM" island reprised as "now the router chooses, per turn" |
| M3 | Ex5 is an evaluation exercise; judge-model economics mirror classifier economics; "no claim without a suite" |
| M4 | Fine-tuned specialists as routing targets (Boomi); verifiable checks echo RLVR; learned routers = train-vs-prompt one level up |
| M5 | `SwitchyardRoutingMiddleware` drops into `create_deep_agent` (Ex3 dx-peek) — the actual benchmarked configuration |
| M6 | Policy routing (who *may*) vs performance routing (who *should*); they compose in a hardened deployment |
| M7 | Lab agent reused; context tax → model bill; `switchyard launch` drives the harnesses toured; Hermes routes with Switchyard in production; engine/car → "stop welding the engine in" |

**Existing files that need edits** (this is what makes it feel designed, not appended):

1. `.devx/7-agent-harnesses/evaluating_harnesses.md` — retitle finale (no longer "workshop complete"), add M8 cell to the arc bento, add the forward hook: *"You chose the car. Next: stop welding in the engine — Module 8 gives your harness a switchyard."*
2. `jp_app_launcher.yaml` — **two** new entries: the `8. Agent Routing` docs tile (same local-server pattern) and the **Routing Client** tile (§4c registration block, `chatbot.svg`, per the Simple Agents / NemoClaw Client precedent).
3. `README.md` — module list bullet, "seven progressive modules" → eight, skills list + `/module-8`.
4. `.devx/index.html` + any landing enumeration (verify at implementation).
5. `.claude/skills/workshop/` hub — `map.md` (new M8 entry: build/concepts/code/prereq/time/hardware), `connections.md` (the seven callbacks above), `glossary.md` (tokenomics, model portfolio/mix, route/target/llm_client, capability vs escalation, session affinity, router tax, Pareto frontier), `progress.md`, routing-shorthand line (`routing/switchyard/model-cost → M8`).
6. **New `.claude/skills/module-8/`** tutor skill following the established non-negotiables (guide-don't-solve; never open `*.answers*`; graduated hints) + `references/{diagrams,nvidia-tech,quizzes}.md` + the always-loaded Environment & hardware block (GPU optional, Ex4b gating, sandbox caveats). Then `.agents/sync-codex-skills.sh` for Codex parity.
7. `requirements.txt` / `postBuild.bash` — pinned `nemo-switchyard[cli]`, `langchain-nvidia-switchyard` (names verified at impl), server binary bake-in.

**Assets to produce:** 4 hand-authored dark SVGs (specs in §3 — authored directly, no mermaid, per the ARM64/no-Chrome constraint and the M7 root-cause lesson) + 2–3 robot PNGs in the module's `_static/robots/` (dispatcher/switchyard-themed; reuse or produce off-box).

---

## 8. Risks & verify-at-implementation checklist

1. **API surface drift** — Switchyard is at ~0.2; pin exact versions of `nemo-switchyard` and the LangChain middleware; re-verify `switchyard.libsy` Python names (`LlmTarget`, `algorithms.stage_router`) against the shipped package, and whether the pip CLI bundles a server or Ex4 needs the prebuilt/cargo binary baked into the image.
2. **Model availability** — confirm `nemotron-3.5-lightning-30b-a3b` on `integrate.api.nvidia.com` from the workshop image (retriever-EOL taught us hosted endpoints move); fallback efficient target: `nemotron-3-nano-30b-a3b`.
3. **Numbers in expected outputs** — every printed target (scoreboards, receipts, gauge values) gets calibrated from real runs during implementation; the outline's figures are shape-only.
4. **Escalation determinism** — `confirmations=2` demos need a reliably-escalating scripted task; design it during implementation with retries in mind.
5. **Sandbox egress** — extend `setup-workshop-nemoclaw(-operator)` policies for the new package + loopback port; decide the in-sandbox Ex4 story (live server vs `--dry-run`-only teaching mode).
6. **aarch64** — pip wheels + server binary on GB10/Spark.
7. **Gateway attribution (client):** confirm the gateway response's `model` field reports the upstream target id; if not, fall back to tailing `switchyard-server`'s route trace for the yard animation.
8. **Client scope creep:** the Routing Client is the module's largest implementation item — timebox it, hold the §4c scope guardrails (provided code, graceful locked states, CLI always sufficient), and keep the Streamlit descope path warm.
9. **JupyterLab proxy quirks:** the M5 client's "won't connect" history → same-origin SSE only (no WebSockets), health panel in the status strip, and an explicit troubleshooting entry in the module-8 tutor skill.

---

## 8b. Churn strategy — living with a v0.x dependency

Switchyard is weeks old; assume it iterates fast and occasionally breaks compatibility. The design treats that as a budgeted, manageable risk rather than a reason to wait, on three grounds: the pedagogy is deliberately concept-first (gradient below), the genuinely exposed surface is small, and this repo has survived worse (retriever-EOL, npm `n`).

**Exposure by surface:**

| Surface | Churn risk | Why / mitigation |
|---|---|---|
| Routing concepts & algorithm taxonomy | ~none | Classifier/stage/escalation/learned is the industry's routing vocabulary, not a Switchyard invention — the concept pages survive any API change |
| OpenAI-compatible gateway wire protocol (Ex4 client side) | ~none | Frozen by ecosystem gravity; "point `base_url` at `:4000`" is churn-proof |
| `routes.toml` schema | low-med | Config schemas move slower than code; upstream ships `schema_version = 1` (planned evolution) and `--dry-run` (free validation canary) |
| Hosted model IDs (Lightning/Super endpoints) | medium | The retriever-EOL lesson: service-side drift no pin can prevent — covered by the canary + single constants block |
| Python SDK surface (libsy bindings, LangChain middleware) | **high** | v0.x renames likely; the unverified parts flagged in §8 — confined to one exercise behind a shim |
| Quoted benchmark numbers | stale, not broken | Cited + dated ("measured Aug 2026"); the lab's receipts compute the learner's *own* numbers, which never age |

**The playbook:**

1. **Fail-soft dependency gradient, stated as a design rule:** Ex1–2 and Ex5 have zero Switchyard dependency; Ex4's client side is plain OpenAI-compat; only Ex3 (+ install mechanics) touches the SDK. If Switchyard vanished tomorrow, the module still teaches model routing end-to-end. Rule: **the SDK never carries the pedagogy.**
2. **Pin everything, in one place:** exact `nemo-switchyard` / middleware versions + a release-tagged server binary with sha256, all inside `install_switchyard.sh`. Learners on a built image never see churn; maintainers upgrade deliberately.
3. **Verify-then-expose:** learner-facing content shows raw APIs only where stability is verified (TOML keys, server CLI, client config); the speculative in-process Python surface routes through the ~20-line `switchyard_shim.py`, so an upstream rename is a one-file fix with zero doc-page edits. The real calls stay visible in the shim + 🆘 solutions — learners still meet the true API.
4. **Mock-router fallback:** if the pinned import breaks, the Ex3 runner drops to a deterministic lab-owned router with a loud banner. The M6 audit lesson (missing mock fallback was a P0) applied proactively: the degraded path must still teach.
5. **Version-stamp the teaching:** the meet_switchyard dx-aside names the tested version and frames velocity as evidence of the thesis (M7 precedent: "the harness layer is where the industry innovates fastest").
6. **Maintainer canary + bump runbook:** `smoke_switchyard.sh` = fresh pinned install → `--dry-run` the answers TOML → one live routed call → drift warning vs latest release. Run before events and on bumps. Bump runbook (module README, maintainer section): bump pin → smoke → run `routing_lab.answers.py` end-to-end → recalibrate printed numbers if outputs moved → update the version-stamp aside.
7. **Single-source the volatile strings:** package version, model IDs, install commands live in the install script + one constants block; only two doc pages (the meet_switchyard teardown and Ex4) contain literal config at all.
8. **Upstream ear (organizational):** watch the repo's releases; being NVIDIA-internal, get on the NeMo-Switchyard team's heads-up channel for breaking changes — pins make upgrades scheduled work, not emergencies.

**Net:** with the playbook, expected churn cost is a periodic one-file code touch + two-page doc touch on the maintainer's schedule — never a learner-visible breakage. The residual risks that matter (hosted model-ID drift; the unverified Python surface) are already on the §8 checklist and both covered by the canary.

---

## 9. Open decisions & next steps

1. **Framing (settled in review, 2026-08-13):** Option A spine + tokenomics (B) promoted to the motivation layer — the module opens and closes on "frontier vs open is a false binary; use both, efficiently" — with the ecosystem mapping (C) as the wrap.
2. **The lab's two-surface core** — Exercise 3 (in-process libsy) vs Exercise 4 (gateway + `routes.toml`) as the module's central teaching pair.
3. On approval: commit this as a design spec (e.g. `docs/superpowers/specs/2026-08-11-module-8-agent-routing-design.md`) and turn it into a step-by-step implementation plan.

---

## Sources

- [NVIDIA Developer Blog — Route AI Agent Workloads Across Models with NVIDIA NeMo Switchyard](https://developer.nvidia.com/blog/route-ai-agent-workloads-across-models-with-nvidia-nemo-switchyard/)
- [NVIDIA Blog — Nemotron 3.5 Lightning and NeMo Switchyard](https://blogs.nvidia.com/blog/nemotron-lightning-switchyard-rtx-dgx/)
- [NVIDIA-NeMo/Switchyard on GitHub](https://github.com/NVIDIA-NeMo/Switchyard)
  - [Getting started](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/getting_started.md)
  - [Core concepts](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/core_concepts.md)
  - [Routing algorithms overview](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/routing_algorithms/overview.md)
  - [TOML schema reference](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/reference/toml_schema.md)
- [LangChain — Switchyard agent-routing benchmark](https://www.langchain.com/blog/switchyard-agent-routing-benchmark)
- [Boomi — Why Open Model Routing Matters](https://boomi.com/blog/why-open-model-routing-matters/)
