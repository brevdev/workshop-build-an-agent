"""Module 8 Lab — Agent Routing.

Five exercises that put every call on a meter and then route it to the right model:

  1. The model pool and the bill meter  (build_model_pool, bill_call)
  2. The hand-rolled classifier router  (classify_difficulty, route_call)
  3. The same decision, from a library  (make_lab_router, switchyard_call)
  4. The same decision, out of the app  (routes.toml — a config file, not Python)
  5. The verdict                        (routing_verdict)

Complete the TODOs, then run a single exercise:
  python3 routing_lab.py --exercise 1

Answer key: routing_lab.answers.py"""
import json, pathlib, time
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from constants import *  # model ids, PRICING, STRATEGIES, AT_SCALE_TASKS_PER_DAY

HERE = pathlib.Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# The shared workload: 12 tasks, 6 commodity + 6 frontier. Eleven carry a
# verifiable check (the M4 RLVR callback); one is scored by an LLM judge.
# ---------------------------------------------------------------------------

def load_tasks():
    lines = (HERE / "test_data" / "routing_tasks.jsonl").read_text().splitlines()
    return [json.loads(l) for l in lines if l.strip()]

def check_task(task, output, judge=None):
    c, out = task["check"], (output or "")
    if c["type"] == "contains":     return c["value"].lower() in out.lower()
    if c["type"] == "contains_all": return all(v.lower() in out.lower() for v in c["value"])
    if c["type"] == "judge":
        if judge is None:
            judge = _default_judge   # the LLM judge, defined with the model helpers below
        return judge(c["value"], out)
    raise ValueError(f"unknown check type {c['type']}")

# ---------------------------------------------------------------------------
# Exercise 1 — the model pool and the bill meter. Every answered task flows
# through bill_call, so the receipt and the running total always agree. (The
# judge grades off-meter: it scores the run, it is not part of the workload.)
# ---------------------------------------------------------------------------

def build_model_pool():
    """The two-model portfolio every strategy draws from.
    Returns {"strong": <frontier stand-in>, "efficient": <open model>}."""
    # TODO: Exercise 1a — return that dict, both values ChatNVIDIA clients: "strong"
    # runs STRONG_MODEL, "efficient" runs EFFICIENT_MODEL. Give them identical settings
    # (temperature=0.2, max_completion_tokens=2048, timeout=180) so the only thing that
    # differs between the two lanes is the model itself.
    raise NotImplementedError("Exercise 1a")

class RunningBill:
    """Provided. The session meter behind every receipt, gauge, and race row."""
    def __init__(self):
        self.total_cost, self.by_model = 0.0, {}
    def add(self, model_id, usage, cost, latency):
        m = self.by_model.setdefault(model_id, {"calls": 0, "cost": 0.0, "in": 0, "out": 0, "latency": []})
        m["calls"] += 1; m["cost"] += cost
        m["in"] += usage.get("input_tokens", 0); m["out"] += usage.get("output_tokens", 0)
        m["latency"].append(latency); self.total_cost += cost
    def summary(self):
        lines = [f"  {mid}: {v['calls']} calls · ${v['cost']:.4f}" for mid, v in self.by_model.items()]
        return "\n".join(lines + [f"  TOTAL ${self.total_cost:.4f}"])

def _price(model_id, usage):
    p = PRICING[model_id]
    return usage.get("input_tokens", 0) / 1e6 * p["in"] + usage.get("output_tokens", 0) / 1e6 * p["out"]

def bill_call(model_id, chat, messages, bill, why="passthrough"):
    """One priced, timed model call. Returns (response, receipt)."""
    # TODO: Exercise 1b — time the call, read response.usage_metadata, price it
    # against PRICING[model_id], bill.add(...) it, and return (response, receipt)
    # with ALL receipt keys: model, input_tokens, output_tokens, cost, latency,
    # counterfactual_cost (same tokens at STRONG_MODEL rates), why, router_tax
    # (0.0 here — Exercise 2's router is what fills that one in).
    raise NotImplementedError("Exercise 1b")

# ---------------------------------------------------------------------------
# Exercise 2 — the hand-rolled router. A cheap model reads the request first
# and picks the lane; that extra call is the router tax, and it goes on the
# same meter as the work. Unreadable verdicts fail UP: a misrouted hard task
# costs an outage, a misrouted easy one costs pennies.
# ---------------------------------------------------------------------------

CLASSIFY_PROMPT = (
    "You are a routing dispatcher. Classify this request as COMMODITY "
    "(extraction, reformatting, single-fact lookup, simple transforms) or FRONTIER "
    "(multi-step reasoning, planning, synthesis, ambiguity). "
    "Reply with exactly one word: COMMODITY or FRONTIER.\n\nRequest:\n{query}"
)

# Thinking OFF is load-bearing here. A one-word contract plus a reasoning model is a trap:
# with thinking on, the classifier spends the whole 8-token budget deliberating ("Here's a
# thinking process: 1."), never says the word, and the fail-up rule below quietly routes 100%
# of traffic to the strong model — a router that looks healthy and routes nothing. The library's
# `with_thinking_mode()` does not cover this model id; the knob is the `chat_template_kwargs`
# key `thinking`, passed through `model_kwargs`.
def build_classifier():
    return ChatNVIDIA(model=CLASSIFIER_MODEL, temperature=0.0,
                      max_completion_tokens=8, timeout=60,
                      model_kwargs={"chat_template_kwargs": {"thinking": False}})

def classify_difficulty(query, classifier_chat, bill):
    """Ask the cheap model which lane this request belongs in.
    Returns (verdict, tax): verdict is "COMMODITY" or "FRONTIER", tax is what asking cost."""
    # TODO: Exercise 2a — bill_call the classifier (model id CLASSIFIER_MODEL,
    # why="router-tax") with CLASSIFY_PROMPT.format(query=query), then read its reply:
    # first word, punctuation stripped, upper-cased. Anything that is not exactly
    # COMMODITY or FRONTIER must fail UP to FRONTIER — a blank or rambling verdict is
    # not evidence of an easy task. Return (verdict, receipt["cost"]).
    raise NotImplementedError("Exercise 2a")

def route_call(query, pool, bill):
    """Classify first, then answer in the lane the classifier picked.
    Returns (response, receipt) — the same receipt shape bill_call produces."""
    # TODO: Exercise 2b — classify_difficulty(query, build_classifier(), bill), send a
    # COMMODITY verdict to pool["efficient"] (EFFICIENT_MODEL) and a FRONTIER one to
    # pool["strong"] (STRONG_MODEL) via bill_call with why=f"classifier: {verdict}",
    # then record the classifier's cost on the receipt as receipt["router_tax"]. That
    # money is already ON the bill — this is for the row to display, not a second charge.
    raise NotImplementedError("Exercise 2b")

# ---------------------------------------------------------------------------
# Exercise 3 — the same decision, from a library. Switchyard's stage router
# reads the tool-result trajectory the agent already produces, so the routing
# decision costs no extra call: router_tax stays 0.0 and, unlike Ex2, that is
# honest on BOTH axes — there is no second round trip hiding in the latency
# either. The SDK is touched only through switchyard_shim (spec §8b.3): if
# upstream renames something, one file changes and this exercise does not.
# ---------------------------------------------------------------------------

import switchyard_shim as shim

def make_lab_router():
    """The Switchyard stage router, wired to this lab's two models."""
    # TODO: Exercise 3a — return shim.make_router(...) with the capable target FIRST and
    # the efficient one second; each target is a {"id": <model id>} dict. Get that order
    # backwards and every routing decision silently inverts.
    raise NotImplementedError("Exercise 3a")

def switchyard_call(query, pool, bill, router=None, tool_events=None):
    """One call routed by the library instead of by a classifier of your own.
    Returns (response, receipt)."""
    # TODO: Exercise 3b — default `router` to make_lab_router(); ask
    # shim.pick_target(router, [query], tool_events or []) for the lane, which comes back
    # as "capable" or "efficient"; map that to pool["strong"]/pool["efficient"] and
    # STRONG_MODEL/EFFICIENT_MODEL; print a `  [route → <lane>] <why>` trace so the stage
    # transition is visible per turn; and bill_call it. `why` is "mock" for a
    # shim.MockRouter, otherwise "stage: synthesis" (capable) or "stage: exploration".
    # There is no second model call here, so router_tax stays 0.0 — leave it alone.
    raise NotImplementedError("Exercise 3b")

# ---------------------------------------------------------------------------
# Exercise 4 — the same decision, moved OUT of the application. routes.toml
# owns the policy; the app asks for one model id ("switchyard") and never has to
# choose which model answers — the yard does, and it reports the upstream model
# id back on the response. The blank here is a config file, not Python:
# everything below is provided. The gateway is the Rust server embedded in the
# pip wheel — start it with scripts/serve_gateway.sh (there is no separate
# binary to install; docs/specs/switchyard-api-notes.md § Server install).
# ---------------------------------------------------------------------------

import urllib.request

def _local_opener():
    """Provided. localhost is a local socket, never a proxy hop — say so explicitly,
    because an inherited http_proxy would otherwise swallow every gateway call."""
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))

def gateway_call(query, bill, *, session=None, history=None, max_tokens=None):
    """Provided: call the route id through the local gateway; bill from the response.
    `session` is the escalation router's memory — same id, same session, and the move
    to the strong tier is one-way once it happens. `history` is the trajectory it reads."""
    payload = {"model": GATEWAY_ROUTE_ID,
               "messages": (history or []) + [{"role": "user", "content": query}]}
    if max_tokens:
        payload["max_tokens"] = max_tokens
    headers = {"Content-Type": "application/json"}
    if session:
        headers["x-switchyard-session-id"] = session   # how the gateway groups turns
    t0 = time.perf_counter()
    req = urllib.request.Request(f"{GATEWAY_BASE_URL}/chat/completions",
                                 data=json.dumps(payload).encode(), headers=headers)
    body = json.load(_local_opener().open(req, timeout=180))
    latency = time.perf_counter() - t0
    served_by = body.get("model", GATEWAY_ROUTE_ID)    # attribution: the UPSTREAM model id
    usage = {"input_tokens": body["usage"]["prompt_tokens"],
             "output_tokens": body["usage"]["completion_tokens"]}
    model_id = served_by if served_by in PRICING else EFFICIENT_MODEL
    cost = _price(model_id, usage)
    bill.add(model_id, usage, cost, latency)
    return body["choices"][0]["message"]["content"], {
        "model": served_by, **usage, "cost": cost, "latency": latency,
        "counterfactual_cost": _price(STRONG_MODEL, usage),
        # 0.0 on THIS meter, and that is the catch: the judge's tokens are spent
        # server-side and never appear in a completion's usage. gateway_stats() has them.
        "why": "gateway (switchyard route)", "router_tax": 0.0}

def gateway_stats():
    """Provided: GET /v1/stats — the gateway's own books. The tier split and the
    router tax (the judge's spend) live here; a completion response shows neither."""
    with _local_opener().open(f"{GATEWAY_BASE_URL}/stats", timeout=30) as response:
        return json.load(response)

# ---------------------------------------------------------------------------
# Exercise 5 — the verdict. Suite results in, scoreboard out: accuracy, spend,
# the open/frontier mix, and what the router itself cost. Three accounting rules,
# both easy to get backwards:
#   · The tax is already IN the cost. run_suite's per-task `cost` is a meter
#     delta covering the classifier call AND the answer; `router_tax` repeats
#     the classifier's share so a row can show it. So tax and cost make a
#     RATIO, never a sum — add them and you bill the router twice.
#   · `models` counts ANSWER calls only, by design (run_suite records the model
#     that answered). frontier_pct is therefore the share of answers that bought
#     frontier tokens; the router's own calls surface only as router_tax_pct.
#   · The monthly projection is PER TASK. AT_SCALE_TASKS_PER_DAY counts tasks per
#     day, so divide the suite's cost by the number of tasks in it before you
#     multiply — projecting the whole 12-task suite 1,000x/day overstates the
#     bill by 12x, and the receipt's "at 1000/day" label would be a lie.
# ---------------------------------------------------------------------------

def routing_verdict(results_by_strategy):
    """Suite results in, scoreboard out.
    Returns {"rows": [...], "savings_pct": float, "monthly": {...}, "receipt": str}."""
    # TODO: Exercise 5 — one row per strategy, each with: strategy, accuracy (how many
    # passed), cost (the sum), frontier_pct (STRONG_MODEL's share of the `models` calls)
    # and router_tax_pct (the tax as a share of cost — a RATIO, never a sum: read the two
    # accounting rules above). Project every strategy out to
    # monthly[strategy] = cost / max(len(results), 1) * AT_SCALE_TASKS_PER_DAY * 30 — the
    # multiplier counts TASKS per day, so divide the suite cost by the number of tasks in
    # it first — work out savings_pct for the routed row against strong_only, and build the
    # one-line 🧾 receipt that says it all.
    raise NotImplementedError("Exercise 5")

# ---------------------------------------------------------------------------
# Provided harness — the LLM judge behind the one unverifiable task, and the
# runner that puts the whole 12-task suite through a single strategy.
# ---------------------------------------------------------------------------

def _default_judge(rubric, output):
    pool = build_model_pool()
    verdict = pool["strong"].invoke(
        f"Rubric: {rubric}\n\nAnswer to grade:\n{output}\n\nReply with exactly PASS or FAIL.").content
    return "PASS" in verdict.upper()

def run_suite(strategy, bill=None, judge=None):
    """Provided. Runs the 12-task suite under one strategy; returns TaskResult dicts."""
    bill = bill if bill is not None else RunningBill()
    pool = build_model_pool()
    results = []
    for task in load_tasks():
        before = bill.total_cost
        if strategy == "strong_only":
            resp, receipt = bill_call(STRONG_MODEL, pool["strong"], task["prompt"], bill)
        elif strategy == "efficient_only":
            resp, receipt = bill_call(EFFICIENT_MODEL, pool["efficient"], task["prompt"], bill)
        elif strategy == "manual_classifier":
            resp, receipt = route_call(task["prompt"], pool, bill)          # Exercise 2's router
        elif strategy == "switchyard_stage":
            resp, receipt = switchyard_call(task["prompt"], pool, bill)     # Exercise 3's router
        else:
            raise ValueError(f"run_suite: unsupported strategy {strategy!r}")
        results.append({"id": task["id"], "kind": task["kind"],
                        "passed": check_task(task, resp.content, judge=judge),
                        "cost": bill.total_cost - before, "latency": receipt["latency"],
                        "models": {receipt["model"]: 1}, "router_tax": receipt["router_tax"]})
    return results

def probe_unlocks(module):
    """Provided, not a blank. True per exercise iff its blanks no longer raise
    NotImplementedError — this dict IS the Routing Client's `systems online: N/5`
    strip. It probes ANY module object (the client reloads the learner's file and
    passes it here), and it is polled, so it must stay cheap: fake inputs only,
    never a token, never a socket. Ex4's blank is a config file, so it is not
    probed — the client checks gateway liveness for that one instead."""
    class _FakeResp:
        content, usage_metadata, tool_calls = "COMMODITY", {"input_tokens": 1, "output_tokens": 1}, []
    class _FakeChat:
        def __init__(self, *_, **__): pass
        def invoke(self, _): return _FakeResp()
    def _solved(fn, *args, **kw):
        try:
            fn(*args, **kw); return True
        except NotImplementedError:
            return False
        except Exception:
            return True     # ran past the blank → implemented (maybe buggy; still unlocked)
    fake_pool = {"strong": _FakeChat(), "efficient": _FakeChat()}
    # Ex2's router builds its own classifier client, and constructing a real ChatNVIDIA
    # fetches the hosted model catalog over the network. Swap the class the lab builds
    # FROM — the same seam the thinking-off guard test patches — so the probe stays
    # offline whether route_call goes through build_classifier or constructs its own.
    real_chat_cls = module.ChatNVIDIA
    module.ChatNVIDIA = _FakeChat
    try:
        return {
            "ex1": _solved(module.bill_call, module.EFFICIENT_MODEL, _FakeChat(), "q",
                           module.RunningBill()),
            "ex2": _solved(module.route_call, "q", fake_pool, module.RunningBill()),
            "ex3": _solved(module.switchyard_call, "q", fake_pool, module.RunningBill(),
                           router=module.shim.MockRouter()),
            "ex5": _solved(module.routing_verdict, {"strong_only": [], "efficient_only": []}),
        }
    finally:
        module.ChatNVIDIA = real_chat_cls

# ---------------------------------------------------------------------------
# CLI runner — one branch per exercise:
# `python3 routing_lab.py --exercise 1`.
# ---------------------------------------------------------------------------

def _print_exercise_1():
    for strategy in ("strong_only", "efficient_only"):
        bill = RunningBill()
        results = run_suite(strategy, bill)
        acc = sum(r["passed"] for r in results)
        p50 = sorted(r["latency"] for r in results)[len(results) // 2]
        print(f"{strategy:>16}: {acc}/12 correct · ${bill.total_cost:.4f} · p50 {p50:.1f}s")
        print(bill.summary())

def _print_exercise_2():
    for strategy in ("strong_only", "efficient_only", "manual_classifier"):
        bill = RunningBill()
        results = run_suite(strategy, bill)
        acc = sum(r["passed"] for r in results)
        p50 = sorted(r["latency"] for r in results)[len(results) // 2]
        row = f"{strategy:>17}: {acc}/12 correct · ${bill.total_cost:.4f} · p50 {p50:.1f}s"
        if strategy != "manual_classifier":
            print(row); continue
        strong = sum(1 for r in results if STRONG_MODEL in r["models"])
        tax = sum(r["router_tax"] for r in results)
        share = 100 * tax / bill.total_cost if bill.total_cost else 0.0
        print(f"{row}  ({strong} → strong / {len(results) - strong} → efficient)")
        print(f"  router tax: ${tax:.4f} ({share:.0f}% of spend)")
        print(bill.summary())   # the meter, not the receipts: it counts the classifier's calls too

# The suite is 12 single-turn prompts, so the stage router has no trajectory to
# read and every task lands on its default tier — true, and worth seeing. The
# demo below is the other half: one task over five turns, with the tool results
# an agent loop would already be producing. The scorer reads the tool-result
# TEXT, not just the count — five terse "FAILED" strings escalate nothing, while
# the realistic pytest output below flips the router at turn 4. Synthetic
# strings: no tool is run, only the routing signal changes between turns.
_READ  = "routing_lab.py: 214 lines read"
_GREP  = "3 matches for 'lane' in routing_lab.py"
_FAIL1 = ("FAILED tests/test_router.py::test_split - AssertionError: 3 != 6\n"
          "1 failed, 11 passed in 0.5s")
_FAIL2 = ("FAILED tests/test_router.py::test_split - AssertionError: 0 != 6\n"
          "FAILED tests/test_router.py::test_tax - KeyError: 'router_tax'\n"
          "2 failed, 10 passed in 0.6s")
_FAIL3 = ("FAILED tests/test_router.py::test_split - AssertionError: 0 != 6\n"
          "ERROR tests/test_router.py::test_tax - fixture 'bill' not found\n"
          "1 failed, 1 error, 10 passed in 0.6s")
_DEMO_TASK = "The router sends every task to the same lane. Diagnose it and propose a fix."
_DEMO_TURNS = [("turn 1 · no tool calls yet",       []),
               ("turn 2 · read + grep (exploring)", [_READ, _GREP]),
               ("turn 3 · first failing test run",  [_READ, _GREP, _FAIL1]),
               ("turn 4 · still failing, wider",    [_READ, _GREP, _FAIL1, _FAIL2]),
               ("turn 5 · failing plus an error",   [_READ, _GREP, _FAIL1, _FAIL2, _FAIL3])]

def _print_stage_transition():
    # Only the routing decision is on show here — the five answers are discarded — so
    # the demo runs its own pool with a tiny completion cap. Identical bill_call,
    # receipts and traces; a fraction of the tokens. The demo keeps its own meter, and
    # prints it: every call this file makes has to land on a meter somebody can read.
    pool = {lane: ChatNVIDIA(model=mid, temperature=0.2, max_completion_tokens=64, timeout=180)
            for lane, mid in (("strong", STRONG_MODEL), ("efficient", EFFICIENT_MODEL))}
    bill, router = RunningBill(), make_lab_router()
    print("stage transition — one task, five turns, the trajectory accumulating:")
    lanes = []
    for label, tool_events in _DEMO_TURNS:
        print(f"  {label:36}", end="")            # switchyard_call prints the [route → …] trace
        _, receipt = switchyard_call(_DEMO_TASK, pool, bill, router=router, tool_events=tool_events)
        lanes.append("capable" if receipt["model"] == STRONG_MODEL else "efficient")
    print(bill.summary())
    split = lanes.count("efficient")
    if lanes == ["efficient"] * split + ["capable"] * (len(lanes) - split) and 0 < split < len(lanes):
        print(f"  turns 1–{split} → efficient · turns {split + 1}–{len(lanes)} → capable "
              f"— the trajectory escalated the router, not the prompt")
    else:   # never claim a transition that did not happen (a MockRouter has no trajectory to read)
        print(f"  no stage transition: {' → '.join(lanes)} — stage signals need trajectories")

def _print_exercise_3():
    bill = RunningBill()
    results = run_suite("switchyard_stage", bill)   # the [route → …] traces print as it runs
    acc = sum(r["passed"] for r in results)
    p50 = sorted(r["latency"] for r in results)[len(results) // 2]
    capable = sum(1 for r in results if STRONG_MODEL in r["models"])
    print(f"{'switchyard_stage':>17}: {acc}/12 correct · ${bill.total_cost:.4f} · p50 {p50:.1f}s"
          f"  ({capable} → capable / {len(results) - capable} → efficient)")
    print(f"  router tax: ${sum(r['router_tax'] for r in results):.4f} "
          f"— the stage signal is already in the trajectory, so there is no second call")
    print(bill.summary())
    print()
    _print_stage_transition()

_SERVE_HINT = (
    "Start the gateway in another terminal. It reads NVIDIA_API_KEY from THAT\n"
    "terminal's environment (`api_key_env` in routes.toml) — the #1 way this fails:\n\n"
    "    cd code/8-agent-routing\n"
    "    bash scripts/serve_gateway.sh routes.toml\n\n"
    "Ask it what it serves:  curl -s localhost:4000/v1/models\n")

# Exercise 3's task and its tool output again — but the turns are shaped for a
# different reader. The stage router scores the trajectory mechanically and flips on
# accumulated failure; the gateway's judge is an LLM with a deliberately high bar
# ("reading the first failing test" is not trouble), so what convinces it is a run
# that stays stuck: failures that keep arriving, and the same one twice.
_GATEWAY_TURNS = [("turn 1 · the task, no tools yet", None),
                  ("turn 2 · first failing test run", _FAIL1),
                  ("turn 3 · a second failure appears", _FAIL2),
                  ("turn 4 · and now a fixture error", _FAIL3),
                  ("turn 5 · re-ran it; identical", _FAIL3)]

def _gateway_escalation(bill):
    """One agent session, five turns, replayed through the gateway. The decision
    happens server-side now, inside a session it tracks by header — no tool is run
    here, only the routing signal changes between turns."""
    session = f"lab-{int(time.time())}"      # a fresh session: escalation is one-way
    print(f"escalation — one task, five turns, session {session}:")
    history, served = [], []
    for label, tool_output in _GATEWAY_TURNS:
        query = _DEMO_TASK if tool_output is None else (
            f"<tool_result>\n$ pytest -q\n{tool_output}\n</tool_result>")
        text, receipt = gateway_call(query, bill, session=session,
                                     history=history, max_tokens=64)
        history = history + [{"role": "user", "content": query},
                             {"role": "assistant", "content": (text or "")[:400]}]
        served.append(receipt["model"])
        print(f"  {label:36}[gateway → {receipt['model']}]")
    up = [i for i, model in enumerate(served) if model == STRONG_MODEL]
    if up and served[up[0]:] == [STRONG_MODEL] * (len(served) - up[0]):
        print(f"  escalated at turn {up[0] + 1} and stayed there — the judge confirmed the run"
              "\n  was stuck as many times as routes.toml asks for, and the move is one-way")
    else:   # never claim an escalation that did not happen
        print("  no escalation: " + " → ".join("strong" if m == STRONG_MODEL else "weak"
                                               for m in served) +
              "\n  — the judge is deliberately reluctant to spend frontier money")

def _gateway_meter():
    """The gateway's own books, including the part the receipts above cannot see."""
    stats = gateway_stats()
    print("the gateway's own meter — /v1/stats, cumulative since it started:")
    tiers = stats.get("tiers") or {}
    if not tiers:
        print("  ⚠️  /v1/stats reports no tiers — the split collapsed and every request is\n"
              "      being served without a routing decision. Check the judge target in\n"
              "      routes.toml: the two traps commented there are exactly this failure.")
    for name, tier in sorted(tiers.items()):
        print(f"  tier {name:>6}: {tier['total_tokens']:>6} tokens "
              f"({tier['token_pct']:.0f}% of routed spend)")
    classifier, overhead = stats.get("classifier") or {}, stats.get("routing_overhead") or {}
    print(f"  router tax: {classifier.get('total_requests', 0)} judge calls · "
          f"{(classifier.get('total_tokens') or {}).get('total', 0)} tokens · "
          f"{overhead.get('avg_ms', 0.0):.0f} ms avg per request\n"
          "  — spent server-side, so none of it shows up in the receipts above")

def _print_exercise_4():
    print(_SERVE_HINT)
    try:
        gateway_stats()                      # is anything actually listening?
    except OSError as exc:
        print(f"No gateway on {GATEWAY_BASE_URL} yet ({exc}) — start it, then re-run.")
        return
    bill = RunningBill()
    print("two single-shot requests — the app names the route, never the model:")
    for query in ("Convert 2 hours to minutes. Just the number.",
                  "Plan a 5-step rollout for migrating a service to a routed model pool."):
        _, receipt = gateway_call(query, bill)
        print(f"  [gateway → {receipt['model']}] ${receipt['cost']:.4f} · {receipt['latency']:.1f}s")
    print("  escalation mode starts every session cheap: a hard-LOOKING prompt is not\n"
          "  evidence of a hard run, so neither of those bought frontier tokens.\n")
    _gateway_escalation(bill)
    print(bill.summary())
    print()
    _gateway_meter()

def _print_exercise_5():
    """The scoreboard: the same 12 tasks under three strategies, then the receipt.
    Each row's cost IS that strategy's whole meter — run_suite's per-task cost is a
    bill delta, so the classifier's calls are already inside the routed row's number
    (which is why the tax is shown as a share of it, not added to it)."""
    results = {}
    for strategy in ("strong_only", "efficient_only", "manual_classifier"):
        print(f"  running {strategy} …", flush=True)
        results[strategy] = run_suite(strategy)
    verdict = routing_verdict(results)
    print(f"\n{'strategy':>17}  {'accuracy':>8}  {'cost':>9}  {'frontier':>8}  {'router tax':>10}")
    for row in verdict["rows"]:
        accuracy, cost = f"{row['accuracy']}/12", f"${row['cost']:.4f}"
        print(f"{row['strategy']:>17}  {accuracy:>8}  {cost:>9}  "
              f"{row['frontier_pct']:>7.0f}%  {row['router_tax_pct']:>9.0f}%")
    # Two tiers, six names — the receipt reconciles the vocabulary this module has
    # been using: Ex2 routed to a lane, Ex3 named a stage, Ex4 named a tier in a
    # TOML file, and all three meant the same two models.
    print("  frontier = Ex2's 'strong' lane = Ex3's 'capable' stage; open = the efficient\n"
          "  model = Ex4's 'weak' tier in routes.toml. Two tiers, six names. The % is the\n"
          "  share of ANSWER calls — the router's own calls are the tax column, never the mix.")
    print(f"\n🧾 {verdict['receipt']}")

if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser(description="Module 8 routing lab")
    ap.add_argument("--exercise", type=int, required=True, choices=range(1, 6))
    ex = ap.parse_args().exercise
    try:
        {1: _print_exercise_1, 2: _print_exercise_2, 3: _print_exercise_3,
         4: _print_exercise_4, 5: _print_exercise_5}[ex]()
    except NotImplementedError as blank:      # an unfilled TODO is not a crash
        label = str(blank).replace("Exercise ", "")
        print(f'\n❌ Exercise {label} not implemented yet — open routing_lab.py '
              f'and search for "TODO: Exercise {label}"')
        sys.exit(1)
