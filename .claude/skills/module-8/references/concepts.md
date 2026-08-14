# Module 8 Concepts — tutor reference

The module's ideas in the workshop's own framing, with source pointers. The ⚠️ items are the
**high-misconception facts** — get these exactly right; SKILL.md carries one-line versions of
each for always-on recall.

## Tokenomics — the module's opening and closing frame
**Tokenomics** = the unit economics of LLM work: dollars and seconds per call, per task, per
user, per month. It's the number that decides whether an agent feature ships or dies in review.
Agents multiply it — LangChain's deep-agent benchmark averages **~6.3 model calls per task**, so
a per-token price gap that was a rounding error on a chat app compounds six times per task, all
day. (`intro_agent_routing.md`)

> **The one-line bridge from Module 7:** M7 taught that every token has a **cost** (the context
> tax). M8 teaches that every token has a **price** — and the price depends on *who generates it*.

## The false binary, and the portfolio answer
The industry argues **frontier or open** as a procurement decision. Both cases are honest —
Team Frontier (max capability, zero infra; premium per-token pricing that never amortizes, data
leaving your walls, single-vendor dependency) and Team Open (cheap at scale, private, customizable
— your M4 specialist; a capability ceiling on the hardest calls, and a serving stack you now own).
What kills the binary is that **it silently assumes every call is equally hard**, and any agent
transcript disproves that.

NVIDIA's answer: models as a **portfolio**, not a pick. Commodity calls to open models (most),
genuinely hard calls to a frontier model (few). In LangChain's 145-task run "most" measured
**~93% of calls** and "few" **~7%** — ⚠️ *a share of **CALLS**, not tokens or tasks*. Rebalancing
is a `routes.toml` edit plus an eval run, not a migration. The thesis, stated top and bottom:
***use both, efficiently.***

**Routing is a layer, not a rewrite** — same agent, same loop, same tools, with a dispatcher in
front of the model call. That's why it retrofits onto shipped systems, and why Exercise 4 changes
the policy with zero edits to the Python.

⚠️ **Nemotron Super 120B is a STAND-IN for the frontier tier** — it *plays* the
expensive-but-intelligent role relative to Lightning 30B so the whole module runs on one free
`NVIDIA_API_KEY`. Never present it as literally a frontier model. In production the strong slot
is often a closed frontier model at a steeper price, which makes routing pay off **more**
(`anthropic_messages` is a first-class client format — a two-line `targets` edit).

## The five algorithm families — evidence vs cost of deciding
Sorted by *what the router may look at before it picks, and what looking costs*
(`routing_decisions.md`). **Five families, four algorithm ids** — escalation is a **mode** of
`llm_classifier`, not a separate algorithm, which is why the page's figure carries four cards:

1. **Static splits** — `random` (weighted coin; indefensible as policy, excellent as an **A/B
   instrument**: *you can't credit the router if you never ran the split*), `passthrough` (one
   target — "no router" as a nameable configuration, i.e. the **control row**; Exercise 1 runs
   two), `noop` (no upstream at all; config-only).
2. **`llm_classifier`, capability mode** — a small **judge** reads the request text.
3. **`stage_router`** — reads the tool-result trajectory the agent already emits.
4. **`llm_classifier`, escalation mode** — same algorithm, cheap-first default, one-way.
5. **Learned / prefill routers** — the model's own **residual stream** from the prefill pass plus
   a small trained head. Richest evidence, near-free at inference; the cost is labelled outcomes
   and a training run. **Taught, not exercised** — a training run doesn't fit in 95 minutes, and
   it's M4's train-vs-prompt decision one level up.

Nothing in the ordering says *go right*: **the cheapest decision that's good enough for your
workload wins.** That's why there are five and not one.

## Router tax
The permanent per-turn overhead of *deciding* — M7's context tax pointed at dollars and
milliseconds. It is real, and this module puts it **on the receipt**.
- **This lab, Exercise 2:** ~**4–6%** of the routed run's own spend — the band actually measured
  across the lab's full runs, and the one `routing_decisions.md`'s bar and `routing_lab.md`'s
  published ranges both print.
- **LangChain's benchmark:** **21%** of the routed run's own spend and **~700 ms per turn**, on
  much heavier work (long multi-step trajectories vs this lab's one short prompt).
- It's a **ratio**, so it swings with how expensive the work underneath it is. Always name the
  denominator: *the routed run's own total spend*.
- ⚠️ **At the gateway the tax lives in `/v1/stats`, not on your receipt.** Judge tokens are spent
  server-side and never appear in a completion's `usage`, so Exercise 4's receipts read
  `router_tax: 0.0` **structurally, and truthfully**. Exercise 3's `0.0` is a different claim:
  there genuinely is no second call.
- `stage_router` avoids it entirely — *when your workload gives it something to read.*

## `llm_classifier` — the knobs
- ⚠️ **`base_threshold` polarity (capability mode).** The judge scores **how likely the
  *efficient* model is to succeed** on this task. **Above** the threshold rides the efficient
  model; **below** it escalates to strong. So **raising the dial escalates MORE** — you're
  demanding more confidence before trusting the cheap model (spend more, fail less); lowering it
  saves more and drops more tasks on the floor. It's a **policy dial**, not a tuned constant —
  sweep it to trace the cost-accuracy frontier on your own workload. **Escalation mode has no
  threshold at all**; it counts `confirmations`.
- **`session_affinity`** pins a session to the tier it started on, so the agent doesn't flap
  between brains mid-conversation. **`message_hash_fallback`** is its backstop for clients that
  send no session id (hash the conversation prefix) — it **requires `session_affinity`**, and the
  SDK rejects it without one.
- **Abstention:** when the judge comes back with nothing usable the classifier doesn't invent a
  verdict — it abstains and the request falls through to the default tier. **Served, not errored.**
- **The judge is itself an LLM call**, every turn, before any work happens. That's the tax.

## `stage_router`
Scores the recent trajectory and picks a tier with **no second model call** — zero tax, no added
latency, no extra round trip: the decision is free because the evidence was free.
- ⚠️ **It reads the tool-result *text*, not the count.** A clean run rides the efficient tier
  however long it gets; **failures repeating** are what flip it (≈4 accumulated tool results in
  the runs behind the page — not a guaranteed turn number).
- Knobs: **`picker`** (`efficient_first` / `capable_first` — which tier is the default) and
  **`confidence_threshold`** (how sure the scorer must be to leave that default).
- **The trade:** it reads *behaviour*, not meaning — a genuinely hard question asked in one short
  turn with no tool history looks identical to an easy one. Hence Exercise 3's twelve single-shot
  prompts producing **0 escalations, correctly**. Long, tool-heavy sessions are where it earns
  its keep — the shape of every agent since M5.
- The source of those signals is M7's minimal harness: a loop that appends `ToolMessage`s and
  goes around again.

## Escalation mode
⚠️ **Escalation judges RUNS, not prompts.** Every session **starts on `weak`** and only moves up
after `confirmations` consecutive escalate verdicts (the lab uses **2** — one confused turn is a
bad sentence, two in a row is a pattern), and the move is **one-way: it never de-escalates** (the
pathology being avoided is demoting a session that genuinely needed the strong model the moment
things look calm, so it falls over again).
- **What makes a run a run is the session:** the gateway groups turns by the
  **`x-switchyard-session-id`** header. Send no header and every request is its own session of
  length one — so single-shot traffic never escalates, correctly and unhelpfully.
- **A hard-*looking* prompt is not evidence of a hard *run*** — in Exercise 4 both single-shot
  requests (including a five-step migration plan) are served by the efficient model, and that's
  the algorithm being right.
- Side effect: once a session latches to strong the judge isn't consulted again, so **the router
  tax falls as a session ages** (judge calls come out lower than the request count).
- The analogy that sticks: **a junior engineer with a senior on call.**

## ⚠️ Policy routing (M6) vs performance routing (M8)
*Who **may** answer* vs *who **should***.
- **M6 — NemoClaw's Privacy Router:** an **operator-chosen, credential-isolating HTTP forwarder**
  set with `openshell inference set`. One backend per gateway; it strips sandbox credentials and
  injects host-side ones. **It never inspects content** — no classification, no per-query model
  choice. The "keep sensitive data private" line gets misread this way constantly.
- **M8 — `llm_classifier`:** **is** that content classification — a judge model reading each
  request and choosing a target on what it finds. It never decides what is *permitted*.
- **They compose**, and in a hardened deployment both are on: policy sits **outside** (which
  backends are reachable at all, who holds the keys), performance sits **inside** (within the
  reachable set, the cheapest model that can do this call). Neither substitutes for the other.

## NeMo Switchyard's three nouns
In dependency order, because that's the order you fill them in:
- **`llm_clients`** — *where requests go*: an endpoint, the wire `format` to speak to it, and the
  **name** of the environment variable holding the key (never the key).
- **`targets`** — *which model*: an upstream model id on one of those clients, under a short name
  you pick.
- **`routes`** — *what your app asks for*: a public model `id` plus the algorithm that chooses
  among targets. **The route id is the only string your application ever sees**, and it doesn't
  change when the policy under it does.

**Two placements, one core:** in-process (`switchyard.libsy` — you construct targets and the
algorithm, libsy takes the decision, *your* code makes the HTTP call) and at the gateway (all
three nouns come from `routes.toml`; your app sends one model id). Details + the algorithms table
in `nvidia-tech.md`.

## Vocabulary — six names, two tiers
⚠️ Three exercises rotate three vocabularies over the same two models; Exercise 5's receipt
reconciles them:

| Exercise 2 (lanes) | Exercise 3 (libsy targets) | Exercise 4 (`routes.toml`) | The essay word |
|---|---|---|---|
| `strong` | `capable` | `strong` | **frontier** |
| `efficient` | `efficient` | `weak` | **open** |

Plus Exercise 2's classifier **verdicts**: `COMMODITY` (→ efficient lane) and `FRONTIER`
(→ strong lane). And **two attribution vocabularies**: the library reports the **target name**
you chose; the gateway reports the **upstream model id** on the response's standard `model`
field. The lab prints both; the Routing Client maps them.

## The Routing Client
⚠️ **A window, not a wizard.** It holds **zero routing logic** (its `server.py` says so in the
first line of its docstring) — it re-reads the learner's `routing_lab.py` from disk on every
request and renders whatever that file returns. Every lane, price, receipt and verdict came out
of their file. **If a panel is dark, the answer is in the lab file, not the client.**
- `systems online: N/5` is `probe_unlocks(module)` rendered as chips; Ex4 isn't probed (its blank
  is a config file) — **gateway liveness stands in for it**.
- ⚠️ **`mock_demo` = SDK-less, NOT key-less.** The mock replaces the routing *decision*
  (`MockRouter`, a deterministic heuristic); the call that answers is real and billed like any
  other. The demo chip is never locked — and its answer names the first blank it reached.

## Specialists change the game (the M4 payoff)
Everything above quietly assumes weak-vs-strong *generalists*. It doesn't have to. Boomi reports
**100% accuracy on its domain-routing decisions** while sending **59% of production traffic** to a
**5× faster fine-tuned** model. Read the middle number twice: the efficient target wasn't a
smaller general model giving up quality — it was a model *customized for their domain*, which on
their traffic is both faster and better. **Routing to a specialist isn't a compromise; it's an
upgrade that happens to be cheaper.** That completes M4's argument: fine-tuning always had a
capability case, and routing is the missing economic one — **customize small, then route to it.**
And you can only own a specialist if you can own the weights.

## The honest limits (`evaluating_routing.md`)
- **Routing quality is workload-specific** — your split, savings and giveback are properties of
  *your* task mix.
- **Saturated benchmarks flatter routers** — when every strategy scores 12/12 the cheap one wins
  by default; a suite that can't separate two models can't price accuracy either. Harden the
  suite first.
- **The judge is spend and latency.**
- **A six-point accuracy giveback is a *choice*** — obviously right for bulk summarization,
  obviously wrong for clinical coding. Nothing in the router tells you which you're building.
- **NeMo Switchyard is young** (pre-alpha; API expected to change before v1.0). The module pins a
  tested version so everything runs as printed.
- The coda: sometimes the right mix **is** 100% frontier. The point was never that routing wins —
  it's that the router **and the suite** let you *know* instead of guessing.

## Source pointers
- Concepts → `intro_agent_routing.md` (tokenomics, the binary, the portfolio),
  `routing_decisions.md` (the taxonomy, the tax, policy-vs-performance, specialists),
  `meet_switchyard.md` (three nouns, two placements, the judge traps, the version stamp)
- Lab + numbers → `routing_lab.md`; wrap-up + limits → `evaluating_routing.md`
- Code truth → `constants.py`, `switchyard_shim.py`, `routing_lab.py`, `routes.toml.template`
- Verified SDK surface + deviations → `docs/specs/switchyard-api-notes.md`
