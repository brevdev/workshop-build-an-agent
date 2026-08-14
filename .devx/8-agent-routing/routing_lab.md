<div class="dx-hero" data-eyebrow="MODULE 08 / 04 - HANDS ON" data-title="Put every call on a meter. Then send it somewhere cheaper." data-sub="Five exercises that take you from one hardwired model to a routing policy your application never reads - and a client that comes alive as you fill it in." data-meta="TIME::95 min|EXERCISES::5+client|FORMAT::.py (notebook alt)|ANSWERS::included"></div>

Five exercises: price your agent's calls, write a router by hand, hand the same decision to a library, move it out of the app into a config file, and finish with a scoreboard that says what routing cost you and what it bought.

They're not five demos. They're one product — the **Routing Client**, a JupyterLab tile that ships **dormant**, every panel labeled with the exercise that powers it. Each blank you fill lights something up, and the status strip counts it: `systems online: 1/5`, then `2/5`, up to the race panel at the end.

This page follows <button onclick="openOrCreateFileInJupyterLab('code/8-agent-routing/routing_lab.py');"><i class="fa-brands fa-python"></i> routing_lab.py</button>. Seven blanks marked `# TODO: Exercise …` live in that file — the sub-exercise labels below (**1a**, **1b**, **2a**…) match those markers exactly, and each blank gets its own instructions and its own `🆘` solution here. Fill the blanks, then look for the exercise's **Run it** line.

> **Prefer notebooks?** The same lab, cell for cell, lives in <button onclick="openOrCreateFileInJupyterLab('code/8-agent-routing/routing_lab.ipynb');"><i class="fa-solid fa-flask"></i> routing_lab.ipynb</button> — identical blanks, one runnable cell per exercise, a **💡 NEED SOME HELP?** accordion under each. Work it top to bottom and skip the **Run it** commands here; everything else applies unchanged, and a full Run-All is about **25 minutes** of mostly waiting on live suites. **One thing to know up front:** the Routing Client reads `routing_lab.py`, not the notebook — so if you work in the notebook, paste each finished function back into the `.py` when you're happy with it, or the tile stays dark. (Answer keys for either track: `routing_lab.answers.py` / `routing_lab.answers.ipynb`.)

**This lab spends real money — a few cents of it.** The whole thing is roughly 150 live model calls; each exercise below prints its own call count and how long it takes, because a suite that looks hung is usually just a suite. Nothing here runs on your GPU unless you take the optional Exercise 4b.

<!-- fold:break -->

## Exercise 0 — Open the Yard

<img src="_static/robots/assembly.png" alt="Assembly Robot" style="float:right;max-width:240px;margin:20px;" />

Before you write anything, look at what you're building. Open the <button onclick="launch('Routing Client');"><i class="fa-solid fa-rocket"></i> Routing Client</button> — it's also on the JupyterLab launcher, under the workshop's other client tiles.

![The Routing Client, dormant](img/client_dormant.png)

<!-- CAPTURE at Task 20: the dormant client at systems online: 0/5 - strategy chips greyed with
     their unlocks-in-Exercise-N titles, empty receipt rail, race drawer closed. -->

The yard renders, and almost nothing works. Every strategy chip but one is greyed out and titled with the exercise that unlocks it, the receipt rail is empty, the race drawer won't run, and the header reads `systems online: 0/5`. That's the syllabus: five systems, five exercises, in order.

The exception is the **demo (mock)** chip, which is never locked — but send it a query now and it answers with the name of the first blank it reached. That's the design contract in one interaction: **the client is a window, not a wizard.** It holds no routing logic of its own; every lane, price and receipt you'll see below comes out of your file.

It's also your environment check, done at minute five instead of mid-exercise. The client polls your lab file and reports three things as persistent banners — not toasts, because these don't go away by themselves:

- **No `NVIDIA_API_KEY`** — every live query fails until it's set. The banner prints the exact `source` line, absolute path filled in. The client's server reads the key once at startup, so set it in the terminal you launch the tile from and relaunch.
- **`routing_lab.py` didn't execute** — the file itself is broken, which is different from a blank exercise. Unfilled blanks are normal here and never produce this banner.
- **The Switchyard SDK isn't installed** — Exercise 3's chip still works, but through a deterministic `MockRouter` instead of the real stage router. Install it with `bash scripts/install_switchyard.sh` and **relaunch the tile**: that flag is read once, at server startup.

One clarification worth having early, because the demo strategy is easy to misread: **mock means SDK-less, not key-less.** The mock replaces the routing *decision*, never the call that answers — that one is real, and it's billed like every other.

<details class="dx-peek is-setup">
<summary>Working headless, or the tile won't open?</summary>

The client is a window, never a requirement. Every exercise below has a **Run it** command that prints the same numbers in a terminal, and the module is complete without ever opening the tile. If you're in a sandbox with no forwarded port, that's your path.

</details>

**The agent you're routing is provided.** So is the workload: `test_data/routing_tasks.jsonl`, twelve tasks split six **commodity** (extraction, reformatting, single-fact lookups) and six **frontier** (multi-step reasoning, planning, synthesis). Eleven carry a verifiable check — exact-match or contains assertions, the Module 4 RLVR reflex pointed at routing — and one is graded by an LLM judge. The judge grades off the meter: it scores the run, it isn't part of the workload.

<!-- fold:break -->

## Exercise 1 — Two Engines, One Bill

**~15 min · two blanks.** No routing yet. First you need the two numbers routing sits between, and a meter that can't disagree with itself.

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-lab8-1">A stand-in for the frontier</button>
<div id="aside-lab8-1" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-lab8-1" popovertargetaction="hide" aria-label="Close">×</button>

In this lab, Nemotron Super 120B **plays the frontier role** — the expensive-but-intelligent tier relative to Lightning — so every learner can run both tiers with the one free `NVIDIA_API_KEY` and no closed-model account.

In the real world, the strong slot is often a closed-source frontier model — OpenAI's or Anthropic's — at materially steeper per-token prices: the routing logic and the economics are identical, the price gap just widens (which makes routing pay off *more*, not less).

Switchyard doesn't care either way — `anthropic_messages` is a first-class client format, so swapping the strong target for a Claude model is a two-line `targets` edit (shown in the optional peek on the [Meet NeMo Switchyard](meet_switchyard) page) with zero changes to the rest of the module.

</div>
</div>

### 1a — The model pool

<button onclick="goToLineAndSelect('code/8-agent-routing/routing_lab.py', 'TODO: Exercise 1a');"><i class="fas fa-code"></i> TODO: Exercise 1a</button> — return `{"strong": …, "efficient": …}`, both `ChatNVIDIA` clients: `STRONG_MODEL` and `EFFICIENT_MODEL`, with identical settings (`temperature=0.2`, `max_completion_tokens=2048`, `timeout=180`).

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
make = lambda mid: ChatNVIDIA(model=mid, temperature=0.2,
                              max_completion_tokens=2048, timeout=180)
return {"strong": make(STRONG_MODEL), "efficient": make(EFFICIENT_MODEL)}
```

Give both clients **identical** settings — same temperature, same completion budget, same timeout — so the only thing that differs between the two lanes is the model id. Change a second knob here (a smaller budget for the efficient lane, say) and every cost number downstream measures two things at once, and the verdict in Exercise 5 stops being evidence about routing.

</details>

### 1b — `bill_call`: the meter

<button onclick="goToLineAndSelect('code/8-agent-routing/routing_lab.py', 'TODO: Exercise 1b');"><i class="fas fa-code"></i> TODO: Exercise 1b</button> — one priced, timed model call. Time it, read `response.usage_metadata`, price it with `_price(model_id, usage)`, put it on the meter with `bill.add(...)`, and return `(response, receipt)` with all eight receipt keys.

Measure **both** halves while you're in there. Tokens are the bill; wall-clock latency is the other axis, and Lightning's headline is 4× output speed — the meter is what turns that from marketing into your own number.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
t0 = time.perf_counter()
response = chat.invoke(messages)
latency = time.perf_counter() - t0
usage = getattr(response, "usage_metadata", None) or {}
cost = _price(model_id, usage)
bill.add(model_id, usage, cost, latency)
return response, {
    "model": model_id, "input_tokens": usage.get("input_tokens", 0),
    "output_tokens": usage.get("output_tokens", 0), "cost": cost,
    "latency": latency, "counterfactual_cost": _price(STRONG_MODEL, usage),
    "why": why, "router_tax": 0.0,
}
```

The receipt carries eight keys, and the two easiest to drop are the two the lesson needs. `counterfactual_cost` prices *this call's* tokens at `STRONG_MODEL`'s rates — what the same work would have cost on the frontier model, which is the saving, and it is only visible if you compute it. `router_tax` is `0.0` here because a plain call has no router; Exercise 2 is what fills it in. Read usage off `response.usage_metadata` defensively (`or {}` — not every response carries it), price it with `_price(model_id, usage)`, and put those same numbers on the meter with `bill.add(...)` so the receipt and the running total can never disagree.

</details>

**Run it:** open a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button> and run — two suites, **≈26 live calls, 2-5 minutes**:

```bash
cd code/8-agent-routing && python3 routing_lab.py --exercise 1
```

A correct implementation prints two rows and two meters:

```text
     strong_only: 12/12 correct · $0.0270 · p50 3.8s
  nvidia/nemotron-3-super-120b-a12b: 12 calls · $0.0270
  TOTAL $0.0270
  efficient_only: 12/12 correct · $0.0055 · p50 2.7s
  nvidia/nemotron-3.5-lightning-30b-a3b: 12 calls · $0.0055
  TOTAL $0.0055
```

<!-- CALIBRATE: one measured run (Task 3, 2026-08-13, hosted): strong $0.0270 / p50 3.8s,
     efficient $0.0055 / p50 2.7s, both 12/12. Other runs: strong $0.0225-$0.0232, efficient
     $0.0055-$0.0062; p50 strong 3.5-14.0s, efficient 1.9-5.5s. Cost ratio ~4-5x is STABLE;
     latency separation is NOT (noise-dominated). Accuracy is saturated pre-hardening -
     both tiers scoring 12/12 is the honest current state. DENOMINATORS: cost is per
     12-task suite; p50 is per answer call. -->

<div class="dx-island dx-reveal">
  <p class="dx-island-title">THE WHOLE MODULE LIVES BETWEEN THOSE TWO ROWS</p>

Same twelve tasks. Same score, on this suite. One bill is **about 5×** the other — and that ratio is smaller than the per-token price gap, because the efficient model is a reasoning model that writes more tokens to get there. Which is the point of measuring instead of quoting a price sheet.

The latency column moves around a lot between runs; the cost column barely does. When you argue for a router later, argue on the stable axis.

</div>

Now stretch those two rows. Twelve tasks is a rounding error; the same ratio at production volume is a line item, and that's the table a platform team actually presents. Exercise 5 does the arithmetic for you — `AT_SCALE_TASKS_PER_DAY` in `constants.py` is the multiplier, and the closing receipt prints both tiers in dollars per month.

<!-- CALIBRATE + DENOMINATOR CONFLICT for Task 20: routing_verdict computes
     monthly = SUITE cost * AT_SCALE_TASKS_PER_DAY * 30, so Ex5's printed "$610/mo" is the
     12-task suite run 1,000x/day, while the receipt's label reads "at 1000/day" (tasks).
     Per-TASK arithmetic on the same run gives ~$51/mo - a 12x gap. This page deliberately
     prints NO monthly dollars here so it cannot contradict the lab's own output; Task 20
     should reconcile the code's label and denominator, then decide whether an Ex1 dollar
     figure returns. -->

> **Client unlock (1/5).** The **strong-only** and **efficient-only** chips go live, and the meter starts running: session bill, per-query receipts, and the counterfactual line — *would-have-been*, the same tokens re-priced at the frontier tier. Ask it something, then ask the other tier the same thing, and watch the gap accrue. `systems online: 1/5`.

<!-- fold:break -->

## Exercise 2 — Route by Hand

**~20 min · two blanks.** Before the library does it for you, do it yourself. A cheap model reads the request first and picks the lane — and that extra call goes on the same meter as the work.

### 2a — `classify_difficulty`: the verdict

<button onclick="goToLineAndSelect('code/8-agent-routing/routing_lab.py', 'TODO: Exercise 2a');"><i class="fas fa-code"></i> TODO: Exercise 2a</button> — bill the classifier through `bill_call` (model id `CLASSIFIER_MODEL`, `why="router-tax"`) with `CLASSIFY_PROMPT.format(query=query)`, then read its reply: first word, punctuation stripped, upper-cased. Anything that isn't exactly `COMMODITY` or `FRONTIER` fails **up** to `FRONTIER`.

The classifier client is provided, and the comment above `build_classifier()` is worth reading before you write a line — it's this module's most expensive lesson, and it's already been paid for you.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
response, receipt = bill_call(CLASSIFIER_MODEL, classifier_chat,
                              CLASSIFY_PROMPT.format(query=query), bill, why="router-tax")
raw = response.content if hasattr(response, "content") else str(response)
words = (raw or "").strip().upper().split()
token = words[0].strip(".,!:;") if words else ""
verdict = token if token in ("COMMODITY", "FRONTIER") else "FRONTIER"   # misroutes fail UP
return verdict, receipt["cost"]
```

Unreadable verdicts must fail **UP**: first word, punctuation stripped, upper-cased, and anything that is not exactly `COMMODITY` or `FRONTIER` becomes `FRONTIER` — a blank or rambling reply is not evidence of an easy task. This is also why `build_classifier()` turns thinking off. A reasoning model handed a one-word contract and an 8-token budget spends the whole budget deliberating, never says the word, and this fail-up rule then quietly routes 100% of traffic to the strong model: a router that looks healthy and routes nothing. And bill the classifier through `bill_call` with `why="router-tax"` — asking which model to use is itself a model call, on the same meter as the work.

</details>

Notice the asymmetry the fail-up rule encodes. Send a hard task to the weak model and you fail the task; send an easy task to the strong model and you waste a fraction of a cent. Those aren't the same mistake, so the default isn't symmetric either.

### 2b — `route_call`: dispatch on the verdict

<button onclick="goToLineAndSelect('code/8-agent-routing/routing_lab.py', 'TODO: Exercise 2b');"><i class="fas fa-code"></i> TODO: Exercise 2b</button> — classify, send `COMMODITY` to `pool["efficient"]` and `FRONTIER` to `pool["strong"]` via `bill_call` with `why=f"classifier: {verdict}"`, then record the classifier's cost on the receipt as `receipt["router_tax"]`.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
verdict, tax = classify_difficulty(query, build_classifier(), bill)
lane = "efficient" if verdict == "COMMODITY" else "strong"
model_id = EFFICIENT_MODEL if lane == "efficient" else STRONG_MODEL
resp, receipt = bill_call(model_id, pool[lane], query, bill, why=f"classifier: {verdict}")
receipt["router_tax"] = tax          # already in the bill; recorded so the row can show it
return resp, receipt
```

`receipt["router_tax"] = tax` is a display field, not a second charge. The classifier's call already went through `bill_call`, so that money is on the meter; the receipt repeats it so a row can show what the routing decision cost. Add it to the cost anywhere downstream and you bill the router twice — that is Exercise 5's first accounting rule. Keep the `why` string's format too (`f"classifier: {verdict}"`): it is the audit trail, and it records the decision that was made, not just the lane it landed in.

</details>

**Run it:** in a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button> — three suites this time, **≈51 live calls, 4-6 minutes**:

```bash
cd code/8-agent-routing && python3 routing_lab.py --exercise 2
```

> **Heads up on the bill:** `--exercise 2` re-runs Exercise 1's two baselines first, so it costs those ~24 calls again even after Exercise 1 is solved. That's deliberate — a routed row means nothing without its controls on the same screen — but it's why this one takes twice as long as the last.

```text
      strong_only: 12/12 correct · $0.0225 · p50 3.5s
   efficient_only: 12/12 correct · $0.0059 · p50 1.9s
manual_classifier: 12/12 correct · $0.0103 · p50 7.4s  (3 → strong / 9 → efficient)
  router tax: $0.0005 (5% of spend)
```

<!-- CALIBRATE: one measured run (Task 4, 2026-08-13, hosted). Across identical runs the SPLIT is
     the unstable number: 3/12, 2/12 and 1/12 to strong have all been observed, and the routed cost
     and tax move with it (routed $0.0080-$0.0117, tax 4-6%). Publish ranges. The meter block
     (bill.summary) prints after these lines and is elided here. DENOMINATORS: cost per 12-task
     suite; the tax % is a share of the ROUTED row's own spend; the split counts ANSWER calls. -->

Read the parenthesis before the dollars. **That split line is the health check** — it's how you catch a router that has quietly stopped routing. A classifier that returns nothing readable fails up on every request, so `12 → strong / 0 → efficient` is a collapsed router that still prints a perfectly plausible bill. Expect the split to wander between runs: on this twelve-task suite it lands somewhere around 1-3 tasks to the strong lane, and the routed cost follows it.

The vocabulary starts here too: `COMMODITY` and `FRONTIER` are the classifier's verdicts, mapping onto the *efficient* and *strong* lanes. Exercise 3 renames them again; Exercise 5 reconciles all of it.

<div class="dx-island dx-quiz">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">Your router tax is 5% of the routed bill and you want it lower. Which single change buys the most?</p>
  <button class="dx-quiz-opt" data-fb="There isn't one - the classifier is already the smallest model in the pool, and it is also the efficient tier. You would be shopping for a fourth model to save fractions of a cent.">A smaller classifier model</button>
  <button class="dx-quiz-opt" data-right data-fb="Decide once per session instead of once per request. Switchyard calls it session affinity - and the gateway in Exercise 4 shows the effect directly: once a session escalates, the judge is not consulted again, so the tax falls as the session ages.">Cache the verdict per session</button>
  <button class="dx-quiz-opt" data-fb="Backwards. A longer prompt is more input tokens on every single routing decision - that is the tax going up.">A longer, more careful prompt</button>
  <button class="dx-quiz-opt" data-fb="Temperature is already 0.0 and it costs nothing either way. Determinism is a good idea here; it is not a cost lever.">Lower the classifier temperature</button>
</div>

![The client routing a query](img/client_routed.png)

<!-- CAPTURE at Task 20: the client mid-route - manual_classifier chip on, a query card at the
     dispatcher with its verdict showing, and a receipt carrying the verdict + router tax lines. -->

> **Client unlock (2/5).** The **manual classifier** chip lights up and the yard starts switching tracks: the query card pauses at the dispatcher, the verdict appears, and the card rides the lane it picked. Receipts grow two lines — the verdict, and the router tax. Use the **commodity** and **frontier** example chips under the input to send divergent traffic on purpose. `systems online: 2/5`.

<!-- fold:break -->

## Exercise 3 — Routing as a Library

**~20 min · two blanks.** Same decision, production-grade, in your own process — and this one reads evidence you were already producing.

Switchyard's `stage_router` scores the tool-result trajectory your agent emits anyway, so it makes no second model call — `router_tax` stays `0.0`, and here that's honest on **both** axes.

The SDK is touched through exactly one file: `switchyard_shim.py`. Your blanks call lab-owned names, and the real API stays visible inside the shim.

### 3a — `make_lab_router`

<button onclick="goToLineAndSelect('code/8-agent-routing/routing_lab.py', 'TODO: Exercise 3a');"><i class="fas fa-code"></i> TODO: Exercise 3a</button> — return `shim.make_router(...)` with the capable target **first** and the efficient one second, each a `{"id": <model id>}` dict.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
return shim.make_router({"id": STRONG_MODEL}, {"id": EFFICIENT_MODEL})
```

Capable target **first**, efficient second — the order is positional, and getting it backwards inverts every routing decision silently: the suite still runs, every receipt still balances, and the hard turns just quietly go to the cheap model. Each target is a plain `{"id": <model id>}` dict, and the shim is the only file in this module that touches the SDK.

</details>

### 3b — `switchyard_call`

<button onclick="goToLineAndSelect('code/8-agent-routing/routing_lab.py', 'TODO: Exercise 3b');"><i class="fas fa-code"></i> TODO: Exercise 3b</button> — ask `shim.pick_target(router, [query], tool_events or [])` for the lane, map `capable`/`efficient` onto the pool and the model ids, print the `[route → …]` trace, and bill it.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
router = router or make_lab_router()
lane = shim.pick_target(router, [query], tool_events or [])
lane_key = "strong" if lane == "capable" else "efficient"
model_id = STRONG_MODEL if lane == "capable" else EFFICIENT_MODEL
why = ("mock" if isinstance(router, shim.MockRouter)
       else f"stage: {'synthesis' if lane == 'capable' else 'exploration'}")
print(f"  [route → {lane}] {why}")          # the stage transition, visible per turn
return bill_call(model_id, pool[lane_key], query, bill, why=why)
```

The library's lane names are `capable` / `efficient` — not Exercise 2's `strong` / `efficient` — so map the name it returns to *both* the pool key and the model id, or you will bill one model for another's tokens. Leave `router_tax` at `0.0`: the stage router scores the trajectory the agent already produced and decides locally, so there is no second model call to pay for and no second round trip hiding in the latency either. The `[route → …]` print is what makes the stage transition visible per turn; `why` is `"mock"` for a `shim.MockRouter`, otherwise `stage: synthesis` (capable) or `stage: exploration`.

</details>

**Run it:** in a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button> — one suite plus a five-turn demo, **≈18 live calls, 1-3 minutes**:

```bash
cd code/8-agent-routing && python3 routing_lab.py --exercise 3
```

The suite comes first, and its result is a lesson in itself:

```text
 switchyard_stage: 12/12 correct · $0.0062 · p50 5.9s  (0 → capable / 12 → efficient)
  router tax: $0.0000 — the stage signal is already in the trajectory, so there is no second call
  nvidia/nemotron-3.5-lightning-30b-a3b: 12 calls · $0.0062
  TOTAL $0.0062
```

Twelve single-turn prompts, twelve efficient answers, zero escalations — and that's correct. A stage router reads *behavior*, and a one-shot prompt has no behavior to read yet, so every task lands on the default tier. Which is why the second half of this exercise exists.

<div class="dx-term">
  <span class="dx-term-title">stage transition - one task, five turns</span>
  <span class="dx-term-line" data-kind="prompt">The router sends every task to the same lane. Diagnose it and propose a fix.</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">turn 1 · no tool calls yet            [route → efficient] stage: exploration</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">turn 2 · read + grep (exploring)      [route → efficient] stage: exploration</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">turn 3 · first failing test run       [route → efficient] stage: exploration</span>
  <span class="dx-term-line" data-kind="tool" data-delay="350">turn 4 · still failing, wider         [route → capable] stage: synthesis</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">turn 5 · failing plus an error        [route → capable] stage: synthesis</span>
  <span class="dx-term-line" data-kind="tokens" data-delay="250">TOTAL $0.0025</span>
  <span class="dx-term-line" data-kind="answer" data-delay="400">turns 1–3 → efficient · turns 4–5 → capable — the trajectory escalated the router, not the prompt</span>
</div>

<!-- CALIBRATE: measured runs put the flip at turn 4 (Task 5, Task 9) - roughly four accumulated
     tool results, where the failures start repeating. Task 6's gateway judge flipped at turn 3 on
     the same strings; the scorers are different and neither turn number is guaranteed. The demo's
     own meter printed $0.0025 (3 efficient calls $0.0003 + 2 capable $0.0023). -->

**The prompt never changes.** It's the same sentence on all five turns; only the tool results accumulate. The scorer reads the tool-result *text*, not the count — a clean run rides the default tier however long it gets, and it's failures repeating that flip it, at roughly four accumulated results in the runs behind this page. Your turn number may differ, and the closing line never claims a transition that didn't happen.

The demo keeps its own meter and prints it — two escalated turns carrying most of the bill on under half the calls. That's a second meter, not a running total: the suite and the demo are separate runs.

<details class="dx-peek">
<summary>Seeing a ⚠️ MockRouter banner instead of stage decisions?</summary>

The SDK isn't importable from the interpreter you're running. Install it and check which Python it landed in:

```bash
cd code/8-agent-routing && bash scripts/install_switchyard.sh
```

The installer prefers your ambient environment and falls back to a dedicated venv when the ambient one is externally managed (PEP 668). It prints the interpreter it used, and you can ask for that path alone:

```bash
cd code/8-agent-routing && bash scripts/install_switchyard.sh --print-python
```

The degraded path still teaches — `MockRouter` is deterministic and the trace still prints — but it decides with a heuristic, not the stage scorer, and it says so on every run. If you're in the client, relaunch the tile after installing: the SDK flag is read once at startup.

</details>

<details class="dx-peek">
<summary>Where this goes in a real agent</summary>

You built the source of these signals last module: a loop that appends `ToolMessage`s and goes around again. Anywhere that loop runs — including the Module 5 deep agent, which is the shape LangChain benchmarked — a stage router can read it. NVIDIA's launch coverage names LangChain, LiteLLM and Kong as surfaces where the router becomes middleware instead of a call you make yourself; treat that as direction, because there's no Switchyard middleware package to install today. The honest version in your own code is the one you just wrote.

</details>

> **Client unlock (3/5).** The **Switchyard: stage router** chip lights up, and the dispatcher starts showing stage signals instead of a classifier verdict. If the SDK isn't installed, the **demo (mock)** chip covers the same panel with a deterministic router — SDK-less, not key-less. `systems online: 3/5`.

<!-- fold:break -->

## Exercise 4 — The Gateway

**~20 min · the blank is a file, not Python.** You've already seen a finished yard — the [Meet NeMo Switchyard](meet_switchyard) page tears one down line by line. Now build yours.

Everything in Python is provided for this exercise. What you write is `routes.toml`: three nouns in dependency order — `llm_clients` (where requests go), `targets` (which model), `routes` (what your app asks for, and the algorithm behind it).

**Step 1 — copy the skeleton.** The shipped file is <button onclick="openOrCreateFileInJupyterLab('code/8-agent-routing/routes.toml.template');"><i class="fa-solid fa-file-lines"></i> routes.toml.template</button>, commented and full of TODOs. Your copy is git-ignored, so it's yours to break:

```bash
cd code/8-agent-routing && cp routes.toml.template routes.toml
```

**Step 2 — fill the TODOs.** Open your new `routes.toml` from the file browser and work down its `# TODO: Exercise 4` comments — edit the copy, not the template. There are three groups: the client's `format`, `base_url` and `api_key_env`; the `weak` and `strong` target ids; and the route's `type`, `mode`, `classifier_target`, `weak_target`, `strong_target` and `escalation` confirmations. The judge target is provided, and the two traps commented above it are the ones that cost this module the most to find.

**Step 3 — validate before you serve.** There's no `--dry-run` flag; the embedded gateway validates a config when you construct it, and port 0 binds and releases at once:

```bash
cd code/8-agent-routing && "$(bash scripts/install_switchyard.sh --print-python)" -c \
  "from switchyard_rust.server import Server; Server('routes.toml', port=0).close()"
```

Silence means it's valid. This is Module 7's validate-before-you-save lesson with a config file in the blank.

**Step 4 — serve it.** In a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>second terminal</button>, and mind where the key lives — the gateway reads it from **its own** environment, via `api_key_env`, which is the single most predictable failure in this module:

```bash
cd code/8-agent-routing
set -a; source /project/secrets.env; set +a
bash scripts/serve_gateway.sh routes.toml
```

Ask it what it serves, from anywhere:

```bash
curl -s localhost:4000/v1/models
```

One route id comes back: `switchyard`. That string is the entire public surface of your policy.

**Run it:** back in your first <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button> — **7 routed requests plus the judge calls behind them, about 2 minutes**:

```bash
cd code/8-agent-routing && python3 routing_lab.py --exercise 4
```

<div class="dx-term">
  <span class="dx-term-title">python3 routing_lab.py --exercise 4</span>
  <span class="dx-term-line" data-kind="think">two single-shot requests - the app names the route, never the model:</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[gateway → nvidia/nemotron-3.5-lightning-30b-a3b] $0.0002 · 3.6s</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[gateway → nvidia/nemotron-3.5-lightning-30b-a3b] $0.0019 · 8.4s</span>
  <span class="dx-term-line" data-kind="think" data-delay="350">escalation - one task, five turns, session lab-1786680424:</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">turn 1 · the task, no tools yet     [gateway → nvidia/nemotron-3.5-lightning-30b-a3b]</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">turn 2 · first failing test run     [gateway → nvidia/nemotron-3.5-lightning-30b-a3b]</span>
  <span class="dx-term-line" data-kind="tool" data-delay="350">turn 3 · a second failure appears   [gateway → nvidia/nemotron-3-super-120b-a12b]</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">turn 4 · and now a fixture error    [gateway → nvidia/nemotron-3-super-120b-a12b]</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">turn 5 · re-ran it; identical       [gateway → nvidia/nemotron-3-super-120b-a12b]</span>
  <span class="dx-term-line" data-kind="tokens" data-delay="250">TOTAL $0.0119</span>
  <span class="dx-term-line" data-kind="answer" data-delay="400">escalated at turn 3 and stayed there — the judge confirmed the run</span>
  <span class="dx-term-line" data-kind="answer">was stuck as many times as routes.toml asks for, and the move is one-way</span>
</div>

<!-- CALIBRATE: measured run (Task 6, 2026-08-13): escalated at turn 3, 7 routed calls + 5 judge
     calls, TOTAL $0.0119, ~2 min. The escalation turn is NOT guaranteed - the code never claims an
     escalation that did not happen, and the same tool strings flipped Exercise 3's stage scorer at
     turn 4. DENOMINATOR: dollars per call, seconds per call. -->

Look at the first two lines before the escalation. One is a trivial conversion and one asks for a five-step migration plan, and **both** were served by the efficient model. That's escalation mode being right: a hard-*looking* prompt is not evidence of a hard *run*. **Escalation judges runs, not prompts** — which is why single-shot traffic never escalates, correctly and unhelpfully.

What makes a run a run is the **session**. The gateway groups turns by the `x-switchyard-session-id` header; same id, same session, and once the judge has confirmed trouble as many times as your `escalation.confirmations` asks for, the move to the strong tier is one-way for the rest of it. Send no header and every request is its own session of length one.

<!-- fold:break -->

### The tax you can't see from here

Every receipt in that run reads `router_tax: 0.0`, and every one of them is telling the truth about what it can see. The judge's tokens are spent server-side and never appear in a completion's `usage`. So the exercise finishes by asking the gateway for its own books:

```bash
curl -s localhost:4000/v1/stats
```

```text
the gateway's own meter — /v1/stats, cumulative since it started:
  tier strong:   1536 tokens (42% of routed spend)
  tier   weak:   2142 tokens (58% of routed spend)
  router tax: 5 judge calls · 11940 tokens · 1586 ms avg per request
```

<!-- CALIBRATE: measured run (Task 6). The client's status line on a shorter session read
     1 judge call / 2,245 tokens / 1,954 ms against a 202-token answer (Task 12). Judge overhead
     range across runs: 1.5-2.6 s. DENOMINATORS: tier % is a TOKEN share of routed spend (the
     gateway's per-tier CALL counters are unreliable for the default tier - upstream quirk);
     judge tokens are prompt+completion for the judge target only. -->

That's real money, and it's substantial in relative terms: on one short session the judge burned **2,245 tokens to decide about a 202-token answer**. The capability card it reads is most of that. **At the gateway, the tax lives in the yard's books, not on your receipt** — which is the part worth carrying into production, because it's exactly the cost a per-request dashboard will never show you.

Watch the judge-call count, too: it's *lower* than the request count. Once a session latches to strong, escalation is one-way and the judge isn't consulted again — so the router tax falls as a session ages.

<details class="dx-peek is-solution">
<summary>🆘 The gateway won't start, or it starts and routes nothing</summary>

Three nouns, in dependency order, and each one has a way of failing quietly:

- **`llm_clients`** — `format = "openai_chat"`, the `base_url` from `constants.py`, and `api_key_env = "NVIDIA_API_KEY"`: the **name** of the variable, never the key itself.
- **`targets`** — `weak` is `EFFICIENT_MODEL`, `strong` is `STRONG_MODEL`, and the judge is provided.
- **`routes`** — `type = "llm_classifier"`, `mode = "escalation"`, the three target names, and `escalation = { confirmations = 2 }`.

**TRAP 1 — the judge needs its own model id.** Two targets naming the same model on the same client are deduplicated, one is dropped, and the tier split collapses: every request lands on `strong` while `/v1/stats` reports no tiers at all. If the lab prints `⚠️ /v1/stats reports no tiers`, this is why.

**TRAP 2 — the judge must not think.** With thinking on it spends its whole verdict budget deliberating, never emits the JSON the classifier asked for, and the router doesn't raise — it falls through to `strong`. Both traps look like a healthy router and bill like a frontier-only one.

**And the key comes from the serving terminal.** `api_key_env` is read by the gateway process, so exporting the key in the terminal running the *lab* does nothing for it. `serve_gateway.sh` checks this before it starts and prints the exact `source` line with the absolute path already filled in.

Validate with the port-0 command above — it fails loudly and specifically on a malformed config. Once yours works, `routes.toml.answers` is the completed reference: fill in your own first, then diff them.

</details>

<details class="dx-peek">
<summary>4b (optional, needs Docker + an NVIDIA GPU) — make the weak tier your own silicon</summary>

Same route id, same algorithm, same agent code. The only thing that changes is where the cheap tokens are made:

```bash
cd code/8-agent-routing && bash scripts/serve_local_nim.sh
```

It's Module 2's NIM runbook, parameterized — `docker login nvcr.io`, a cached model volume, a container on the workbench network. When it's up, uncomment the two `Exercise 4b` blocks at the bottom of your `routes.toml`, delete the hosted `[targets.weak]`, and restart the gateway.

Then run the M7 ritual in a third <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button>:

```bash
watch -n 0.5 nvidia-smi
```

Easy turns light up your GPU. Hard turns escalate to the hosted 120B and leave it idle. **No Docker or GPU? Skip 4b entirely — 4a is the full exercise**, and nothing later in this module depends on it.

</details>

<details class="dx-peek">
<summary>Try it at home: sweep the policy dial (unscripted)</summary>

Escalation mode has no threshold — it counts confirmations. Capability mode does, and `base_threshold` is the dial that traces the cost-accuracy frontier on your own workload. There's no lab code for this and no expected output; it's an experiment, and it's a good one.

Copy your working config to a second file, switch that route to `mode = "capability"` with a `base_threshold` (the judge scores how likely the *efficient* model is to succeed, so **above** the threshold rides weak and **below** escalates — raise the dial and more traffic goes to the strong tier). Serve the copy, re-run `--exercise 4`, and read the tier split off `/v1/stats` each time. Three values are enough to see the curve move.

</details>

> **Client unlock (4/5).** The **gateway** chip goes live the moment the client can reach `:4000` — no blank to fill, because your blank was a file. The dispatcher relabels itself as the external server, and a stats line appears under the yard with the tier split and the judge's spend: the numbers a receipt structurally cannot show. On the 4b path a **your GPU** locomotive joins the yard with a live utilization badge. `systems online: 4/5`.

<!-- fold:break -->

## Exercise 5 — Prove It

**~15 min · one blank.** Module 3's rule, applied to your own router: no claim without a suite.

<button onclick="goToLineAndSelect('code/8-agent-routing/routing_lab.py', 'TODO: Exercise 5');"><i class="fas fa-code"></i> TODO: Exercise 5</button> — one row per strategy (accuracy, cost, frontier share of answer calls, router tax as a share of cost), the monthly projection at `AT_SCALE_TASKS_PER_DAY`, the savings against `strong_only`, and the one-line 🧾 receipt.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
rows, monthly = [], {}
for strategy, results in results_by_strategy.items():
    cost = sum(r["cost"] for r in results)
    strong_calls = sum(r["models"].get(STRONG_MODEL, 0) for r in results)
    total_calls = sum(sum(r["models"].values()) for r in results)
    tax = sum(r["router_tax"] for r in results)
    rows.append({"strategy": strategy, "accuracy": sum(r["passed"] for r in results),
                 "cost": cost, "frontier_pct": 100.0 * strong_calls / max(total_calls, 1),
                 "router_tax_pct": 100.0 * tax / max(cost, 1e-12)})
    monthly[strategy] = cost * AT_SCALE_TASKS_PER_DAY * 30
strong = next((r for r in rows if r["strategy"] == "strong_only"), None)
routed = next((r for r in rows if r["strategy"] in ("manual_classifier", "switchyard_stage", "gateway")), None)
savings = (1 - routed["cost"] / strong["cost"]) * 100 if strong and routed and strong["cost"] else 0.0
receipt = (f"routed: {100 - routed['frontier_pct']:.0f}/{routed['frontier_pct']:.0f} open/frontier mix · "
           f"${routed['cost']:.2f} vs ${strong['cost']:.2f} (−{savings:.0f}%) · "
           f"at {AT_SCALE_TASKS_PER_DAY}/day: ${monthly[routed['strategy']]:,.0f} vs ${monthly['strong_only']:,.0f}/mo · "
           f"accuracy {routed['accuracy']}/12 vs {strong['accuracy']}/12 · "
           f"router tax {routed['router_tax_pct']:.0f}% of spend") if strong and routed else "insufficient data"
return {"rows": rows, "savings_pct": savings, "monthly": monthly, "receipt": receipt}
```

Divide, never add. `run_suite`'s per-task `cost` is a meter delta that already covers the classifier call *and* the answer, and `router_tax` repeats the classifier's share so a row can display it — so the two make a ratio (`100 * tax / cost`); summing them bills the router twice, and the bug ships green because the number still looks plausible. The other rule is what `models` counts: **answer calls only**, so `frontier_pct` is the share of answers that bought frontier tokens and the router's own calls surface in the tax column, never in the mix. Guard both divisions (`max(total_calls, 1)`, `max(cost, 1e-12)`) — `routing_verdict` is called with empty result lists by the Routing Client's unlock probe.

</details>

**Run it:** in a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button> — three suites, the longest run in the lab: **≈51 live calls, 4-12 minutes**:

```bash
cd code/8-agent-routing && python3 routing_lab.py --exercise 5
```

```text
         strategy  accuracy       cost  frontier  router tax
      strong_only     12/12    $0.0204      100%          0%
   efficient_only     12/12    $0.0062        0%          0%
manual_classifier     12/12    $0.0117       17%          4%

🧾 routed: 83/17 open/frontier mix · $0.01 vs $0.02 (−43%) · at 1000/day: $350 vs $610/mo · accuracy 12/12 vs 12/12 · router tax 4% of spend
```

<!-- CALIBRATE: verbatim from the primary calibration run (Task 7, 2026-08-13, exit 0, 3m44s,
     ~51 calls). A second full run (Task 9, in-notebook) printed -58%, a 92/8 mix, $249 vs $587/mo
     and a 6% tax, and scored efficient_only 11/12 while the same notebook's Ex1 scored it 12/12.
     PUBLISH RANGES: savings 40-60%, mix 83/17 to 92/8, tax 4-6%. DENOMINATORS: frontier % is a
     share of ANSWER calls; router tax % is a share of the routed row's own spend; the monthly
     figures are the SUITE cost x AT_SCALE_TASKS_PER_DAY x 30 (see the Exercise 1 note - the
     receipt labels that "at 1000/day" but the multiplicand is a 12-task suite, not a task). -->

**Two tiers, six names.** The receipt reconciles the vocabulary this module has been rotating through: `strong` (Exercise 2's lane) = `capable` (Exercise 3's stage) = **frontier**; `efficient` (the lane) = `weak` (Exercise 4's tier in `routes.toml`) = **open**. Three exercises, three vocabularies, the same two models.

Read the accuracy column honestly. On this twelve-task suite all three strategies usually score 12/12 — which means the suite isn't yet hard enough to price accuracy, and the savings number is the only claim it supports. That's a real limitation of a small suite, printed rather than hidden; a run where `efficient_only` drops a task is the suite starting to bite. Your savings will land somewhere in the 40-60% band and your mix somewhere around 83/17 to 92/8, because the split moves run to run.

<!-- fold:break -->

![Race mode, all four strategies](img/client_race.png)

<!-- CAPTURE at Task 20: race mode open at 5/5 - leaderboard filled for all four strategies, the
     accuracy-vs-cost Pareto scatter populated, and the closing receipt line. -->

> **Client unlock (5/5).** **Race mode** opens in the bottom drawer — the same twelve-task suite under each strategy you select, with the leaderboard and the accuracy-vs-cost scatter filling in live as rows stream back. The chips are the four suite strategies only (`strong_only`, `efficient_only`, `manual_classifier`, `switchyard_stage`); gateway and demo answer single queries, not suites. All four is **≈48 live calls and several minutes**, there's no cancel button, and closing the tab won't stop a suite that's already started. Run fewer if you're in a hurry. `systems online: 5/5`.

One honest note on the receipt: `insufficient data` is a real state, not a bug. Race a single strategy and there's no baseline to divide by, so the verdict says so instead of inventing a percentage.

You now have the table this module opened with, generated by your own agent in your own account: what each strategy costs, what share of calls bought frontier tokens, what the router itself cost, and what all of it projects to at production volume. *Frontier quality where it's needed, open-model prices where it isn't — use both, efficiently.*

And the honesty beat that has to come last: **the router didn't earn that claim. Your eval suite did.**

> All five systems online? Head to [Wrapping Up](evaluating_routing) to connect the lab back to production — and to the other seven modules.
