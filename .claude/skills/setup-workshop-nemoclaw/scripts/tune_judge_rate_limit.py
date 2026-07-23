#!/usr/bin/env python3
"""tune_judge_rate_limit.py — add a client-side rate limiter to the module-3
judge LLM (sandbox copy of code/3-agent-evaluation/evaluation_framework.py
and its .answers variant).

Why: ragas.evaluate()'s default RunConfig fires enough concurrent judge calls
to exceed the NVIDIA API key's RPM budget. The 429s are swallowed per-job and
the module-3 RAGAS cell "succeeds" printing
{'context_precision': 0.0, 'context_recall': nan, ...} — reproduced with the
eval notebook running SOLO. Throttling the judge model itself fixes every
caller (LLM-as-judge loops AND ragas) without touching exercise cells.

Idempotent (marker-guarded). Usage: tune_judge_rate_limit.py <repo-root>
"""
import os
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "/sandbox/workshop-build-an-agent"
MARKER = "# [sandbox] judge rate limiter"

LIMITER_BLOCK = f'''{MARKER} — ragas' default concurrency otherwise 429s the
# NVIDIA API key's RPM budget and yields nan RAGAS metrics (verified solo).
from langchain_core.rate_limiters import InMemoryRateLimiter

_JUDGE_RATE_LIMITER = InMemoryRateLimiter(
    requests_per_second=0.5, check_every_n_seconds=0.1, max_bucket_size=4
)
'''

OLD_RETURN = """    return ChatNVIDIA(
        model=JUDGE_MODEL,
        temperature=temperature,
        max_tokens=4096,
    )"""

NEW_RETURN = """    return ChatNVIDIA(
        model=JUDGE_MODEL,
        temperature=temperature,
        max_tokens=4096,
        rate_limiter=_JUDGE_RATE_LIMITER,
    )"""

TARGETS = [
    ("code/3-agent-evaluation/evaluation_framework.py", "def create_judge_llm"),
    ("code/3-agent-evaluation/evaluation_framework.answers.py", "def create_judge_llm"),
    ("code/6-agent-safety/safety_eval_framework.py", "def create_safety_judge_llm"),
    ("code/6-agent-safety/safety_eval_framework.answers.py", "def create_safety_judge_llm"),
]

changed = 0
for rel, anchor in TARGETS:
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        continue
    text = open(path).read()
    if MARKER in text or anchor not in text:
        continue
    if OLD_RETURN not in text:
        print(f"WARN: {rel}: judge return shape changed — skipping")
        continue
    text = text.replace(OLD_RETURN, NEW_RETURN, 1)
    text = text.replace(anchor, LIMITER_BLOCK + "\n\n" + anchor, 1)
    open(path, "w").write(text)
    changed += 1
    print(f"rate-limited judge in: {rel}")

print(f"done: {changed} file(s) modified")
