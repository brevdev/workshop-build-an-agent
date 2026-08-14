# Module 8 Quizzes — tutor deep-dive

Use this to give richer feedback than the in-page one-liner. **If the learner hasn't attempted
the question yet, get them to commit to an answer first** — both `PLACE YOUR BET` widgets exist
precisely because a wrong guess makes the real number land. Once they've engaged: explain the
correct answer, the principle under it, why each distractor is *tempting*, and how to go deeper.

Every number below has a **denominator**. Say it out loud — that discipline is half of what the
module teaches.

---

## The in-page checks

### 1. `intro_agent_routing.md` — "Module 1 also had 'routing.' What did it decide?"
- **Correct:** *which tool or step.*
- **Why:** M1's routing was **control flow** — think, act, or answer. The model was a constant
  pinned at the top of the file (`MODEL_NAME = "nvidia/nemotron-3-super-120b-a12b"`), never a
  decision. Module 8 completes the component: **which brain**.
- **Distractors:**
  - *which model* → that's **this** module's job, not M1's.
  - *which user* → nothing in the agent loop routes users; that's tenancy/load-balancing one
    floor below. (M6's operator policy is the closest thing, and it routes **backends**, not people.)
  - *which GPU* → placement is the **serving** layer's job (NIM, Dynamo). A router picks a model;
    the serving stack picks the silicon it runs on.
- **Principle:** "routing" now names three layers that **compose** — policy decides who *may*
  answer (M6), the router decides who *should* (M8), the agent's own loop decides what to do next (M1).
- **Go deeper:** have them open a Module 1–7 file and find the pinned model constant. Every one
  has it under a different variable name.

### 2. `intro_agent_routing.md` (PLACE YOUR BET) — "An agent benchmark routed between a 30B open model and a frontier model. What fraction of calls actually needed the frontier?"
- **Options:** 75% · 40% · 20% · **7%**. **Correct: ~7%.**
- **Why:** in LangChain's 145-task deep-agent benchmark, **~93% of calls** were answered by the
  30B open model and only **~7% escalated** to the frontier — for **80.0% accuracy at roughly a
  quarter of the cost**.
- **The misconception it targets:** people bet high because *their* hard tasks feel
  representative. The transcript disagrees: "summarize this tool output" and "plan a five-step
  investigation across these three files" sit one line apart, and today they cost the same.
- **⚠️ Denominator:** 93/7 are shares of **CALLS**, not tokens and not tasks. Restate that
  every time the number reappears.
- **Go deeper:** ask them to predict their own Exercise 5 mix before running it (the lab lands
  around **83/17 to 92/8**, and moves run to run).

### 3. `routing_decisions.md` — "Your agent does long tool-heavy sessions and you can't afford an extra LLM call per turn — which algorithm?"
- **Correct:** *`stage_router`.*
- **Why:** it routes on **tool signals the loop already produces** — no classifier call, no tax,
  no extra round trip. Long tool-heavy sessions are exactly where it earns its keep.
- **Distractors:**
  - *`llm_classifier`* → reads content well, but that's an extra LLM call **every turn** — the
    constraint the question set.
  - *`random`* → a baseline, not a decision.
  - *`passthrough`* → that's not routing at all (it's the control row).
- **Principle:** evidence vs cost of deciding. The cheapest decision that's good enough wins.
- **The trade to name if they ask "why not always stage_router?":** it reads **behaviour, not
  meaning** — a genuinely hard question asked in one short turn with no tool history looks
  identical to an easy one. That's why Exercise 3's twelve single-shot prompts produce **zero
  escalations, correctly**.

### 4. `meet_switchyard.md` (PLACE YOUR BET) — "Cognition put a Switchyard staged router inside Devin Desktop… how much did the routed mix cut mean cost per run?"
- **Options:** ~5% · ~15% · **~28%** · ~70%. **Correct: ~28% lower mean cost per run.**
- **Why:** on FrontierCode Main (Cognition's own production-coding benchmark) the routed mix
  scored **50.6% accuracy at $3.11 mean cost per run** — about **28% below the frontier-only
  baseline** and **within 2.8 accuracy points** of it. It routed between **Opus 5 and Kimi K2.7**
  — neither of them NVIDIA's. *The dispatcher doesn't care whose locomotives are in the yard.*
- **⚠️ Two numbers, two denominators** (this is the point of the question):
  **50.6% is an ABSOLUTE accuracy** on that benchmark — *not* 50.6% *of* the baseline.
  **~28% is a COST** — mean spend per run measured against that same baseline.
- **Why ~70% is tempting and wrong:** the intro page's 74% cut is a *different* workload with a
  *different* task mix. Savings are workload-specific; that's the module's first honest limit.
- **Go deeper:** "that's the discipline you'll owe your own results in Exercise 5" — ask them to
  state the denominator for each column of their own scoreboard.

### 5. `meet_switchyard.md` — "Your `routes.toml` gives the judge the same model id as the weak target, on the same client. What happens?"
- **Correct:** *routing silently collapses onto the strong target.*
- **Why:** targets are deduplicated on **(client, model id)** when the config loads. One is
  dropped, the router loses the tier it was going to name, every request lands on `strong`, and
  `/v1/stats` reports **no tiers at all**. It looks healthy and bills like frontier-only.
- **Distractors:**
  - *the gateway refuses to start* → it starts fine. **That's the problem** — one warning, then
    it serves happily.
  - *both targets share one connection — a small optimization* → nothing is shared; dedupe costs
    you a target.
  - *everything routes weak, since the judge picks itself* → the opposite: a missing verdict
    **fails up** to strong. Failing up is the safe default.
- **Principle:** the routing bugs worth knowing aren't exceptions — **they're bills**. Give the
  judge its own model id (the lab uses Nano 30B) or a second `llm_client`.
- **Sibling trap:** the judge must **not think** (`extra_body = { chat_template_kwargs =
  { thinking = false } }`) — a thinking judge spends its verdict budget deliberating, never emits
  the JSON, and the classifier falls through to `strong` without raising. Same symptom, same bill.

### 6. `routing_lab.md` (Exercise 2) — "Your router tax is 5% of the routed bill and you want it lower. Which single change buys the most?"
- **Correct:** *cache the verdict per session.*
- **Why:** decide **once per session** instead of once per request. Switchyard calls it
  **session affinity**, and Exercise 4's gateway shows the effect directly: once a session
  escalates, the judge isn't consulted again, so **the tax falls as the session ages** (judge
  calls < request count).
- **Distractors:**
  - *a smaller classifier model* → there isn't one. The classifier is already the smallest model
    in the pool **and** it's the efficient tier; you'd be shopping for a fourth model to save
    fractions of a cent.
  - *a longer, more careful prompt* → backwards. More input tokens on **every** routing decision
    is the tax going **up**.
  - *lower the classifier temperature* → already 0.0, and it costs nothing either way.
    Determinism is a good idea here; it is not a cost lever.
- **Principle:** the router tax is a **per-decision** cost, so the lever is **how often you
  decide**, not how cheaply.

---

## Four deeper questions (no in-page version — use these to stretch a learner)

### 7. "Why does the escalation router never de-escalate mid-session?"
- **Answer:** because the failure it's avoiding is worse than the money it would save. A session
  that genuinely needed the strong model gets demoted the moment things *look* calm — and
  immediately falls over again, having burned the strong-model turns that fixed nothing. So the
  move is **one-way for the rest of the session**.
- **The other half of the design:** `confirmations` (the lab uses **2**) filters noise in the
  other direction — **one confused turn is a bad sentence; two in a row is a pattern.** Together:
  slow to escalate, never to come back.
- **The analogy that sticks:** *a junior engineer with a senior on call.* The junior takes every
  ticket; if two consecutive turns go badly the senior takes it over — **and doesn't hand it back
  halfway through.**
- **Common misconception:** "then it's just expensive after one bad patch." It's scoped to the
  **session** — the `x-switchyard-session-id` header. A new session starts on `weak` again.
  (And note the side effect: the *tax* falls once a session latches, because the judge stops
  being consulted.)

### 8. "My routed accuracy dropped 6 points vs strong-only — is the router broken?"
- **Answer: no — that's the deal, and it's a CHOICE.** LangChain's headline is exactly this
  trade: **86.0% → 80.0% absolute accuracy for a 74% cost cut** (~$4.2M/yr → ~$1.1M/yr at 1,000
  tasks/day). Routing didn't make anything smarter; it made a purchase decision.
- **The tutor move:** don't tell them whether their trade is acceptable — that's *their*
  analysis (rule 4). Ask instead: *what is this agent for?* The same six points are obviously
  fine for bulk summarization and obviously unacceptable for clinical coding. **Nothing in the
  router tells you which one you're building. Your eval suite does.**
- **What would make it a bug:** accuracy dropping *without* a matching change in the mix — check
  the split line first. `12 → strong / 0 → efficient` (or the reverse) is a **collapsed router**
  that still prints a plausible bill. Also check that both lanes got **identical client settings**
  in Exercise 1a, or the comparison measures two things at once.
- **The honest inverse, which the lab usually shows:** when every strategy scores **12/12**, the
  suite **can't price accuracy at all** — the cheap one then "wins" by default. That's a
  limitation of a small suite, and the first thing to harden. The module prints it rather than
  hiding it.
- **Closing beat:** *"the router didn't earn that claim. Your eval suite did."*

### 9. "Where does this module's ONLY Switchyard import live, and why?"
- **Answer:** `code/8-agent-routing/switchyard_shim.py`. Every other file — the lab, the
  notebook, the Routing Client — reaches the SDK **through** it (`from switchyard.libsy import
  LlmTarget, algorithms`), and the learner's Exercise 3 blanks call lab-owned names
  (`shim.make_router`, `shim.pick_target`).
- **Why: churn armor.** Switchyard is **pre-alpha** — "expected to change significantly before
  v1.0", four releases inside days, and `main` already diverged from the pinned 0.2.0. One import
  site means an upstream surface change is a **one-file fix**, and the exercise's teaching
  survives it. The shim also degrades on purpose: if the import fails *or* the constructor
  rejects its arguments, it returns a deterministic `MockRouter` **behind a loud banner** rather
  than dying.
- **The transferable lesson (it's Module 7's, one floor down):** wrap a fast-moving dependency at
  exactly one seam. The same reflex explains why the routing policy lives in `routes.toml` and
  not in the application.
- **Follow-up worth asking:** *"and where do the version pins live?"* →
  `scripts/install_switchyard.sh` (package pin, per-wheel sha256s, the three model ids);
  `constants.py` holds what the lab code reads. Never bump ad hoc — the README has the runbook.

### 10. "What's the difference between Module 6's Privacy Router and Module 8's `llm_classifier`?"
- **Answer: who MAY answer vs who SHOULD.**
  - **M6 — Privacy Router (policy routing):** an **operator-chosen, credential-isolating HTTP
    forwarder**, set with `openshell inference set`. It picks **one inference backend per
    gateway**, strips the sandbox's credentials and injects host-side ones. ⚠️ **It never inspects
    content** — it does not classify requests and it does not pick a model per query.
  - **M8 — `llm_classifier` (performance routing):** **is** content classification — a judge
    model reads each request and picks the cheapest target that can handle it. It never decides
    what is *permitted*.
- **Why this is the module's most-corrected confusion:** the "keep sensitive data private" line
  around the Privacy Router gets misread as classification constantly — Module 6 spends a whole
  exercise correcting it. Same English word, **opposite mechanisms**.
- **They compose, and in a hardened deployment both are on:** policy sits **outside** (which
  backends are reachable at all, and who holds the keys); performance sits **inside** (within the
  reachable set, the cheapest model that can do this call). Neither substitutes for the other —
  a performance router will happily route to a backend compliance never approved, and a policy
  gateway will happily spend frontier money converting 2 hours into minutes.
- **Go deeper:** ask where a *content-aware* router would sit relative to a NemoClaw deployment.
  (Answer: **in front of** the operator's gateway — that's the composition, drawn.)
