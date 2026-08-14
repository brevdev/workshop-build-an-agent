"""Module 8 answers — complete implementations. Learner copy is derived from
this file in Task 8. Structure: constants import, suite, Ex1..Ex5 sections,
provided harness, CLI runner."""
import json, pathlib
from constants import *  # model ids, PRICING, STRATEGIES, AT_SCALE_TASKS_PER_DAY

HERE = pathlib.Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# The shared workload: 12 tasks, 6 commodity + 6 frontier. Eleven carry a
# verifiable check (the M4 RLVR callback); one is scored by an LLM judge.
# ---------------------------------------------------------------------------

def load_tasks():
    lines = (HERE / "test_data" / "routing_tasks.jsonl").read_text().splitlines()
    return [json.loads(l) for l in lines if l.strip()]

def _default_judge(rubric, output):
    """Real implementation lands with the model helpers in Task 3."""
    raise NotImplementedError("the LLM judge arrives with the model helpers (Task 3)")

def check_task(task, output, judge=None):
    c, out = task["check"], (output or "")
    if c["type"] == "contains":     return c["value"].lower() in out.lower()
    if c["type"] == "contains_all": return all(v.lower() in out.lower() for v in c["value"])
    if c["type"] == "judge":
        if judge is None:
            judge = _default_judge   # defined with the model helpers in Task 3
        return judge(c["value"], out)
    raise ValueError(f"unknown check type {c['type']}")
