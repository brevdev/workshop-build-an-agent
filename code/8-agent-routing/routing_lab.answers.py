"""Module 8 answers — complete implementations. Learner copy is derived from
this file in Task 8. Structure: constants import, suite, Ex1..Ex5 sections,
provided harness, CLI runner."""
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
    # === Exercise 1a (answer) ===
    make = lambda mid: ChatNVIDIA(model=mid, temperature=0.2,
                                  max_completion_tokens=2048, timeout=180)
    return {"strong": make(STRONG_MODEL), "efficient": make(EFFICIENT_MODEL)}

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
    # === Exercise 1b (answer) ===
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
    # === Exercise 2a (answer) ===
    response, receipt = bill_call(CLASSIFIER_MODEL, classifier_chat,
                                  CLASSIFY_PROMPT.format(query=query), bill, why="router-tax")
    raw = response.content if hasattr(response, "content") else str(response)
    words = (raw or "").strip().upper().split()
    token = words[0].strip(".,!:;") if words else ""
    verdict = token if token in ("COMMODITY", "FRONTIER") else "FRONTIER"   # misroutes fail UP
    return verdict, receipt["cost"]

def route_call(query, pool, bill):
    # === Exercise 2b (answer) ===
    verdict, tax = classify_difficulty(query, build_classifier(), bill)
    lane = "efficient" if verdict == "COMMODITY" else "strong"
    model_id = EFFICIENT_MODEL if lane == "efficient" else STRONG_MODEL
    resp, receipt = bill_call(model_id, pool[lane], query, bill, why=f"classifier: {verdict}")
    receipt["router_tax"] = tax          # already in the bill; recorded so the row can show it
    return resp, receipt

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
    # === Exercise 3a (answer) ===
    return shim.make_router({"id": STRONG_MODEL}, {"id": EFFICIENT_MODEL})

def switchyard_call(query, pool, bill, router=None, tool_events=None):
    # === Exercise 3b (answer) ===
    router = router or make_lab_router()
    lane = shim.pick_target(router, [query], tool_events or [])
    lane_key = "strong" if lane == "capable" else "efficient"
    model_id = STRONG_MODEL if lane == "capable" else EFFICIENT_MODEL
    why = ("mock" if isinstance(router, shim.MockRouter)
           else f"stage: {'synthesis' if lane == 'capable' else 'exploration'}")
    print(f"  [route → {lane}] {why}")          # the stage transition, visible per turn
    return bill_call(model_id, pool[lane_key], query, bill, why=why)

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
            resp, receipt = route_call(task["prompt"], pool, bill)          # Task 4
        elif strategy == "switchyard_stage":
            resp, receipt = switchyard_call(task["prompt"], pool, bill)     # Task 5
        else:
            raise ValueError(f"run_suite: unsupported strategy {strategy!r}")
        results.append({"id": task["id"], "kind": task["kind"],
                        "passed": check_task(task, resp.content, judge=judge),
                        "cost": bill.total_cost - before, "latency": receipt["latency"],
                        "models": {receipt["model"]: 1}, "router_tax": receipt["router_tax"]})
    return results

# ---------------------------------------------------------------------------
# CLI runner — one branch per exercise:
# `python3 routing_lab.answers.py --exercise 1`.
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

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Module 8 routing lab")
    ap.add_argument("--exercise", type=int, required=True, choices=range(1, 6))
    ex = ap.parse_args().exercise
    {1: _print_exercise_1, 2: _print_exercise_2,
     3: _print_exercise_3}[ex]()                        # dict grows: 4..5 added in Tasks 6–7
