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

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Module 8 routing lab")
    ap.add_argument("--exercise", type=int, required=True, choices=range(1, 6))
    ex = ap.parse_args().exercise
    {1: _print_exercise_1}[ex]()   # dict grows: 2..5 added in Tasks 4–7
