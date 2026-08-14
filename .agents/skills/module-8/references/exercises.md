# Module 8 Exercises — tutor guide (hint ladders)

Help learners through the five lab exercises in `code/8-agent-routing/routing_lab.py`
**without completing them**. For each blank: the learning goal, a graduated hint ladder
(**L1** conceptual → **L2** specific pointer), and the common mistakes. The teaching page
(`routing_lab.md`) prescribes the `.py` track and labels every blank as a sub-exercise
(**1a**, **1b**, **2a**, **2b**, **3a**, **3b**, **5**) matching the `# TODO: Exercise …`
markers; `routing_lab.ipynb` is the equivalent notebook track (same blanks, one runnable cell
per exercise). Ask which track they're on before pointing at run commands — and remember the
Routing Client reads the **`.py`**, so notebook work has to be pasted back for the tile to light up.

**Rules specific to Module 8:**
- **No targets here, by design.** Unlike the sibling modules, this file carries **no
  answer/target lines** — L2 is the most specific you go. The learner's self-serve escape hatch
  is the per-sub-exercise `🆘 Need some help?` block in `routing_lab.md` (`.py` track) or the
  `💡 NEED SOME HELP?` accordion in `routing_lab.ipynb` (notebook track) — point there as a last
  resort, never paste it.
- **Never open, echo, or diff from `routing_lab.answers.py`, `routing_lab.answers.ipynb`, or
  `routes.toml.answers`.**
- **Exercise 4's blank is a config file, not Python** — coach the three nouns and the dependency
  order; never dictate the TOML.
- **Never run a suite for them.** Each `--exercise N` is 18–51 **live, billed** calls.
- Unfilled blanks raise `NotImplementedError("Exercise <label>")` — that's the signal of an
  untouched blank, not a bug, and it's what the Routing Client's lock banners echo.

Provided scaffolding (do **not** have them rebuild it): `RunningBill` + `bill.add`, `_price`,
`load_tasks` / `check_task`, `CLASSIFY_PROMPT`, `build_classifier()`, `switchyard_shim` (`shim`),
`gateway_call` / `gateway_stats`, `run_suite`, `probe_unlocks`, and the constants
(`STRONG_MODEL`, `EFFICIENT_MODEL`, `CLASSIFIER_MODEL`, `AT_SCALE_TASKS_PER_DAY`).

Always start by asking what they've tried — and, for a run that "looks wrong," read the **split
line** and the meter with them before touching code.

---
## Exercise 1 — Two Engines, One Bill

### 1a · `build_model_pool` — the model pool
- **Goal:** the two-model pool everything downstream compares — and a *fair* comparison.
- **L1:** "It returns a dict the rest of the lab indexes by two fixed keys. Which class does this
  workshop use to talk to hosted Nemotron, and — more important — what is the **only** thing that
  should differ between the two clients?"
- **L2:** "Both values are `ChatNVIDIA` clients, one per model constant already imported at the
  top (`STRONG_MODEL`, `EFFICIENT_MODEL`), under the keys `strong` and `efficient`. Give them
  **identical** settings — the page names `temperature=0.2`, `max_completion_tokens=2048`,
  `timeout=180`."
- **Common mistakes:** a different completion budget or temperature per lane (every cost number
  downstream then measures two things at once, and Exercise 5 stops being evidence); hardcoding
  model-id strings instead of the constants; swapping the two keys (downstream lookups bill the
  wrong lane, silently).
- **Check-question if they push back on "identical":** *"if you shrink the efficient lane's
  budget, what is your cost column measuring?"*

### 1b · `bill_call` — the meter
- **Goal:** one priced, timed model call. This is the meter the whole module argues from, so the
  receipt and the running total must be incapable of disagreeing.
- **L1:** "Three things happen around a single `chat.invoke(messages)`: you time it, you find out
  what it cost, and you record that in **two** places — the receipt you return and the shared
  `bill`. Where does LangChain hang token counts on a response object, and what does the
  provided `_price(...)` helper want handed to it?"
- **L2:** "`time.perf_counter()` either side of the invoke; read usage defensively
  (`getattr(response, 'usage_metadata', None) or {}` — not every response carries it); dollars
  from `_price(model_id, usage)`; record with `bill.add(model_id, usage, cost, latency)`; return
  `(response, receipt)` carrying all **eight** keys — `model`, `input_tokens`, `output_tokens`,
  `cost`, `latency`, `counterfactual_cost`, `why`, `router_tax`."
- **Common mistakes:** dropping `counterfactual_cost` — *this call's* tokens re-priced at
  `STRONG_MODEL`, i.e. the would-have-been; the saving is invisible unless you compute it;
  dropping `router_tax` (it's `0.0` here — a plain call has no router; Exercise 2 fills it);
  reading `usage_metadata` without the `or {}` guard; computing the receipt from different
  numbers than `bill.add` receives (then the receipt and the total drift); not passing `why`
  through to the receipt.

> **Run it:** `python3 routing_lab.py --exercise 1` — two suites, ≈26 live calls, 2–5 min.

---
## Exercise 2 — Route by Hand

### 2a · `classify_difficulty` — the verdict
- **Goal:** the judge call, billed to the **same meter as the work** — plus the fail-up asymmetry.
- **L1:** "Two halves. First make the classifier call *through* the meter rather than around it —
  what `why` label would make the router's own cost identifiable later on a receipt? Second,
  reduce a free-text reply to exactly one of two verdicts. What should happen when the reply is
  neither?"
- **L2:** "Send it through `bill_call` with the classifier's model id, the provided classifier
  client, `CLASSIFY_PROMPT.format(query=query)`, and `why='router-tax'`. Then take the **first
  word** of the reply, strip punctuation, upper-case it; if it isn't exactly `COMMODITY` or
  `FRONTIER`, treat it as `FRONTIER`. Return the verdict together with what the call cost."
- **Common mistakes:** invoking the classifier client directly so the router's cost never reaches
  the meter (that *is* the lesson); failing **down** to `COMMODITY` on an unreadable reply;
  substring-matching the whole reply instead of the first token (a reply mentioning both words
  then flips a coin); forgetting the punctuation strip.
- **Point them at, before they write:** the comment above `build_classifier()` — thinking is off
  for a reason. A reasoning model handed a one-word contract and an 8-token budget spends the
  whole budget deliberating, never says the word, and the fail-up rule then routes **100%** of
  traffic to strong: a router that looks healthy and routes nothing.

### 2b · `route_call` — dispatch on the verdict
- **Goal:** send the query down the lane the verdict names, and record what the decision cost
  **without charging it twice**.
- **L1:** "Classify first, then dispatch. The receipt comes back from `bill_call` — what still
  has to be written onto it before you return, and is that a *new* charge or a *display* of one
  you already made?"
- **L2:** "Classify with the provided classifier builder and the same `bill`; `COMMODITY` goes to
  the efficient pool entry with `EFFICIENT_MODEL`, anything else to the strong entry with
  `STRONG_MODEL`; bill it with `why=f'classifier: {verdict}'`; then set the receipt's
  `router_tax` to the classifier's cost — a display field, because that money is already on the
  meter."
- **Common mistakes:** adding the tax into `receipt['cost']` (double-billing — Exercise 5's first
  accounting rule); pool key and model id disagreeing (you bill one model for another's tokens);
  a `why` string that records the *lane* rather than the *verdict* (it's the audit trail).

> **Run it:** `python3 routing_lab.py --exercise 2` — three suites, ≈51 live calls, 4–6 min.
> ⚠️ It re-runs Exercise 1's two baselines first (~24 of those calls), deliberately: a routed row
> means nothing without its controls on the same screen.

---
## Exercise 3 — Routing as a Library

### 3a · `make_lab_router`
- **Goal:** hand the decision to the library — through the module's one SDK seam.
- **L1:** "One call into `shim`. It takes two target descriptions **positionally**. Which tier
  goes first — and how would you *notice* if you had them backwards?" (Answer to the second half:
  you wouldn't, from the output alone. That's the point.)
- **L2:** "Return `shim.make_router(<capable>, <efficient>)` — **capable first** — where each
  argument is a plain `{'id': <model id>}` dict built from the `STRONG_MODEL` / `EFFICIENT_MODEL`
  constants."
- **Common mistakes:** efficient first — the suite still runs, every receipt still balances, and
  the hard turns quietly go to the cheap model; passing bare model-id strings instead of `{'id':
  …}` dicts; importing `switchyard` directly instead of going through the shim (the shim is the
  module's churn armor).

### 3b · `switchyard_call`
- **Goal:** ask the router, translate its vocabulary into the lab's, and bill the answer honestly.
- **L1:** "The shim replies with a **target name**, not a pool key — libsy says
  `capable`/`efficient`, the pool says `strong`/`efficient`. **Two** things have to be derived
  from that one name; which two, and what breaks if only one of them is? Then: what should
  `router_tax` be here, and why is that honest rather than a shortcut?"
- **L2:** "Default `router` to `make_lab_router()`; get the lane from `shim.pick_target(router,
  [query], tool_events or [])`; derive **both** the pool key and the model id from it; print the
  `[route → <lane>]` trace with a `why` that is `'mock'` for a `shim.MockRouter` and otherwise
  `stage: synthesis` (capable) / `stage: exploration` (efficient); return `bill_call(...)` with
  that `why`."
- **Common mistakes:** mapping the lane to the pool key but not the model id (or the reverse) —
  the receipt then names a model that didn't answer; treating a `MockRouter` as an error rather
  than a labelled fallback; setting a non-zero `router_tax` (there was no second model call, and
  no second round trip in the latency either).

> **Run it:** `python3 routing_lab.py --exercise 3` — one suite + a five-turn demo, ≈18 live
> calls, 1–3 min. `0 → capable / 12 → efficient` on the suite is **correct** (see *Interpreting
> the run*).

---
## Exercise 4 — The Gateway (the blank is a file, not Python)
Everything in Python is provided. What they write is `routes.toml`, from
`routes.toml.template`. **Coach the three nouns; never dictate the values.**

- **Goal:** the routing policy leaves the application entirely — the app sends one string.
- **The shape to coach (dependency order — it's also fill-in order):**
  1. `llm_clients` — *where requests go*: which wire dialect, which `base_url`, and the **name**
     of the env var holding the key.
  2. `targets` — *which model*: an upstream model id on one of those clients, under a short name.
  3. `routes` — *what the app asks for*: the public model id, the algorithm `type`, and that
     algorithm's keys (here: `mode`, the three target names, and the escalation confirmations).
- **L1 (when they're stuck anywhere):** "Which of the three nouns does the thing you're stuck on
  belong to? Each has exactly one job — where requests go, which model, what your app asks for."
- **L2:** "Work the template's `# TODO: Exercise 4` comments top to bottom; the values you need
  are the ones the lab already knows — `constants.py` has the base URL and both model ids, and
  the page names `escalation = { confirmations = 2 }`. The judge target is provided, with its two
  traps commented above it."
- **Common mistakes:** editing `routes.toml.template` instead of the copy (`cp
  routes.toml.template routes.toml` — the copy is git-ignored, so it's theirs to break); putting
  the key *value* in `api_key_env` instead of the variable **name**; giving the judge the weak
  target's model id (**trap 1** — dedupe collapses the tier split onto `strong` and `/v1/stats`
  reports no tiers); deleting the judge's `extra_body` thinking-off line (**trap 2** — the judge
  never emits its verdict and the router falls through to `strong`); starting the gateway from a
  terminal that never exported the key.
- **The order of operations to walk them through:** copy → fill → **validate** (construct the
  embedded server on port 0; silence means valid) → serve in a second terminal → `curl
  /v1/models` → run `--exercise 4` → `curl /v1/stats` for the tax a receipt structurally cannot
  show. `routes.toml.answers` is a **diff-after** reference for *them* — never open it for them.
- **4b is optional** (Docker + an NVIDIA GPU). No Docker/GPU → skip it; 4a is the full exercise.

---
## Exercise 5 — Prove It

### 5 · `routing_verdict` — the scoreboard
- **Goal:** Module 3's rule applied to routing: no claim without a suite. Four columns, two
  accounting rules.
- **L1:** "One row per strategy, four columns: accuracy, cost, frontier share, router tax. Three
  of those are sums; **one is a ratio** — which, and of what over what? Then: what exactly does
  each result's `models` dict count?"
- **L2:** "Per strategy: cost = the sum of per-task `cost`; accuracy = how many `passed`;
  frontier share = 100 × the `STRONG_MODEL` count in `models` ÷ all model counts; router tax % =
  100 × summed `router_tax` ÷ that same cost. Monthly is **per task** — cost ÷ the number of
  results × `AT_SCALE_TASKS_PER_DAY` × 30 — because the multiplier counts *tasks* per day, not
  suites. Savings compares the routed row against `strong_only`. **Guard both divisions.**"
- **Common mistakes:** **adding** `router_tax` to `cost` — the per-task cost is a meter delta
  that already covers the classifier *and* the answer, so summing double-bills the router, and
  the bug ships green because the number still looks plausible; counting the router's own calls
  in the frontier share (`models` counts **answer calls only**, so the router surfaces in the tax
  column and never in the mix); unguarded division — the Routing Client's unlock probe calls this
  with **empty** result lists; inventing a percentage when there is no baseline (`insufficient
  data` is the honest output, and a real state).

> **Run it:** `python3 routing_lab.py --exercise 5` — three suites, the longest run in the lab:
> ≈51 live calls, 4–12 min. It also unlocks the client's **race** mode (≈64 more calls for all
> four strategies — 13 per suite, 25 for `manual_classifier` — no cancel button).

---
## Interpreting the run (where most of the teaching actually happens)
- **Exercise 1's two rows are the whole module:** same twelve tasks, same score, one bill **~5×**
  the other. The **cost ratio is stable; the latency separation is noise-dominated** — have them
  argue on the stable axis. (The ratio is *smaller* than the per-token price gap, because the
  efficient model is a reasoning model that writes more tokens to get there.)
- **Exercise 2's split line is the health check** — `(3 → strong / 9 → efficient)`. A collapsed
  router (`12 → strong / 0 → efficient`) still prints a perfectly plausible bill. Expect the
  split to wander between runs; 1–3 tasks to strong is the normal band on this suite.
- **Exercise 3's `0 → capable / 12 → efficient` is correct, not broken** — a stage router reads
  *behaviour*, and a one-shot prompt has none yet. The five-turn demo is where the flip shows:
  the prompt never changes, only the tool results accumulate, and it's **failures repeating**
  that escalate it (≈4 accumulated results in the runs behind the page; their turn number may
  differ). The demo keeps **its own meter** — a second meter, not a running total.
- **Exercise 4:** the two single-shot requests both go efficient *even though one looks hard* —
  that's escalation mode being right (**it judges runs, not prompts**). Judge calls come out
  **lower** than request counts once a session latches.
- **Exercise 5:** savings usually land **40–60%**, mix **83/17 to 92/8**, tax **4–6%**. Accuracy
  is typically 12/12 for all three strategies — which means **the suite isn't hard enough to
  price accuracy**, so the savings number is the only claim it supports. Say that plainly; it's
  the module's own honest limit, and a run where `efficient_only` drops a task is the suite
  starting to bite.

---
## Escalation protocol
1. Ask what they've tried; read the error, the split line, or the meter **with** them.
2. **L1** — conceptual nudge (which noun / which half of the function / what the number means).
3. **L2** — specific pointer (the call, the parameter, the shape). Stop here.
4. **Last resort** — point them at that sub-exercise's own self-serve reveal: the `🆘 Need some
   help?` block in `routing_lab.md`, or the `💡 NEED SOME HELP?` accordion in
   `routing_lab.ipynb`. **Never paste it**; never open `routing_lab.answers.*` or
   `routes.toml.answers`; never fill a blank, write their `routes.toml`, or run a billed suite
   for them.
