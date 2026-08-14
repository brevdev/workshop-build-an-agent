# Module 8 Diagrams — tutor reference

Help a learner understand a figure they're looking at: what it depicts, what each part means,
the takeaway, and the common confusions. Module 8's three teaching figures are **hand-authored
dark SVGs** in `.devx/8-agent-routing/img/` (the workshop's modules-1–6 convention — no Mermaid);
the fourth is the **live** yard inside the Routing Client, which animates as queries run.

## 1. One model vs. routed (`intro_agent_routing.md` → `img/one_model_vs_routed_dark.svg`)
- **Depicts:** two side-by-side panels of *the same agent*.
  - **TODAY — "one model. every call."** An agent loop (`~6.3 calls/task`) with a single arrow
    carrying **100% of calls** to a **120B · $$$ frontier tier**. Footer:
    **86.0% accurate · $11.45 / task · ~$4.2M / yr at 1,000 tasks/day**.
  - **ROUTED — "same agent. one engine per call."** The same loop, labeled **same code**, now
    feeding a **dispatcher** (drawn with a `?`) that splits into **~93% of calls → 30B · $ open,
    efficient** and **~7% of calls → 120B · $$$ frontier tier**. Footer: **80.0% accurate ·
    $3.00 / task · ~$1.1M / yr**.
  - Caption: *LangChain deep-agent benchmark, 145 multi-step tasks · shares are of CALLS, not tokens.*
- **Takeaway:** the only thing that changed between the panels is the **dispatcher** — same
  agent, same loop, same tools, same code. **Routing is a layer, not a rewrite**, which is why
  it retrofits onto systems already shipped (Exercise 4 does it in a config file).
- **Common confusions:**
  - *"93/7 is a share of tokens/tasks."* No — **calls**. The caption says so; always restate the
    denominator when the number reappears.
  - *"The right panel is strictly better."* Read **both** footers: the cost fell 74% **and** the
    accuracy fell 6 points (86.0 → 80.0, absolute). That trade is right for bulk summarization
    and wrong for clinical coding — the router doesn't know which you're building.
  - *"Those are my numbers."* They're LangChain's, on their agent and their 145 tasks. The
    learner produces their own version of this table in Exercise 5.

## 2. What evidence, at what cost (`routing_decisions.md` → `img/routing_signals_dark.svg`)
- **Depicts:** the taxonomy as **four columns on two axes** — *evidence used* (rows: EVIDENCE /
  COST OF DECIDING / GOOD FOR), ordered left → right by richer evidence and more expensive decisions:
  | | `random` | `stage_router` | `llm_classifier` | prefill (learned) |
  |---|---|---|---|---|
  | **Evidence** | none at all (a weighted coin) | tool results your loop already emits | the request text + the recent turns | the model's own residual stream |
  | **Cost of deciding** | free — no call, no signals | free — no second round trip | one small LLM call, ~700 ms per turn | a training run, then free per call |
  | **Good for** | the A/B baseline | tool-heavy sessions | content decides | tuning-free plateaus |
- **Footnotes on the figure (all three are load-bearing):** *escalation is a **MODE** of
  `llm_classifier`, not a fifth algorithm — same evidence, cheap-first default, one-way* ·
  *LangChain measured the classifier tax at ~700 ms/turn and **21% of the ROUTED run's spend*** ·
  *prefill is the tunable family — taught on this page, not exercised in the lab.*
- **Takeaway:** the families differ mainly in **what they're allowed to look at before they pick,
  and what looking costs**. Some evidence is lying around (request text, tool results, session
  history); some has to be manufactured (a judge call, a training run).
- **Common confusions:**
  - *"Right is better."* Nothing in the ordering says *go right* — **the cheapest decision that's
    good enough for your workload wins.** That's why there are five families and not one.
  - *"Escalation is a fifth algorithm."* It's a **mode** of `llm_classifier` (the figure calls
    this out explicitly).
  - *"`random` is a toy."* As policy, mostly indefensible; as an **instrument** it's the most
    useful thing on the page — a weighted split is an A/B test, and *you can't credit the router
    if you never ran the split.*
  - *"`stage_router` is free because it's dumb."* It's free because **the evidence was already
    free** — the agent emitted it anyway. Its real trade is that it reads *behaviour*, not meaning.

## 3. Switchyard, end to end (`meet_switchyard.md` → `img/switchyard_architecture_dark.svg`)
- **Depicts:** one left-to-right pipeline with **two brackets** over it —
  **in-process (`switchyard.libsy`)** and **gateway (embedded server, `scripts/serve_gateway.sh` —
  Exercise 4)**:
  **your agent** (`model = switchyard`) → **ROUTE** (`id = "switchyard"`) → **ALGORITHM** (the
  dispatcher: `llm_classifier`, `mode = escalation`, `confirmations = 2`) → **TARGETS**
  (`weak` Lightning 30B · `strong` Super 120B · `judge` Nano 30B) → **LLM_CLIENTS** (`[nvidia]`:
  wire format `openai_chat`, one `base_url`, credential `NVIDIA_API_KEY`) → **WHERE THE TOKENS
  ARE MADE** (build.nvidia.com hosted · a local NIM on your own GPU (Ex 4b) · any
  OpenAI-compatible server — vLLM, Ollama, anything).
- **Legend, and it carries meaning:** *solid = what the lab ships · dashed = the same
  `llm_client` with a different `base_url`* · *in-process, your code supplies the clients; at the
  gateway all three nouns come from `routes.toml`* · *green = the cheap tier; amber = what costs
  — the strong answer, **and the judge's own call*** · *the algorithm shown is Exercise 4's;
  Exercise 3 runs this same in-process placement with `stage_router` and two targets — no judge,
  no router tax.*
- **Takeaway:** the **three nouns in dependency order** — a route names an algorithm, the
  algorithm picks a target, the target names the client, the client points at whoever actually
  makes the tokens. The **two brackets are the only real decision**: who owns the transport.
- **Common confusions:**
  - *"There are two products."* One routing core, two placements. The difference is transport
    ownership — and how the decision is reported back (**library → target name** `weak`;
    **gateway → upstream model id** on the response's `model` field).
  - *"The judge is free."* It's drawn amber for a reason: it is a **target**, i.e. a model call
    you pay for. In Exercise 3's stage-router version there is no judge box at all.
  - *"Three targets? I only have two tiers."* `weak` + `strong` are the pool; `judge` is what the
    algorithm consults. It needs its **own model id** (dedupe trap) and **thinking off** (verdict
    trap).
  - *"The dashed boxes are other products."* Same `llm_client`, different `base_url` — a local
    NIM or any OpenAI-compatible server. A router that reaches exactly one vendor isn't managing
    a portfolio; it's a client library.

## 4. The live yard (Routing Client → `code/8-agent-routing/routing_client/static/yard.svg`)
- **Depicts:** the module's metaphor as a working instrument, animated by the learner's own
  queries. **QUERY IN** enters on the inbound rail, a **card** travels to the **DISPATCHER**
  (which prints *why* it decided what it did), and then rides one of the lanes to its locomotive:
  - **commodity lane → LIGHTNING 30B** (*efficient · open*)
  - **frontier lane → SUPER 120B** (*strong · **frontier stand-in***) — the label says stand-in
    right on the diagram
  - **local lane → YOUR GPU · local NIM** with a live **utilization badge** ("the GPU under this
    box, read from `nvidia-smi`") — appears on the Exercise 4b path only.
- **Takeaway:** it makes the routing *decision* visible — the card pauses at the dispatcher, the
  verdict/stage signal appears, then the card takes a lane. Around it: the receipt rail
  (per-query cost, latency, the **counterfactual** "would-have-been" line, the router-tax line),
  the `systems online: N/5` strip, and — once the gateway is up — a stats line under the yard
  with the tier split and the judge's spend.
- **Common confusions:**
  - *"The client is doing the routing."* **Window, not wizard.** It contains zero routing logic;
    it re-reads `routing_lab.py` from disk per request and renders whatever the learner's file
    returns. A dark panel means an unfilled blank, not a broken client.
  - *"The demo (mock) chip means it's not calling a model."* **Mock = SDK-less, not key-less.**
    The mock replaces the *decision*; the answering call is real and billed.
  - *"The GPU lane is missing/idle."* It only exists on the optional 4b path; on 4a there is no
    local locomotive, and that's correct.
