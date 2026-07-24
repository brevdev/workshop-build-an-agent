#!/usr/bin/env python3
"""tune_model_map.py — repair module-5's MODEL_MAP in the sandbox copies.

Two defective entries ship in `demo/backend/agent.py` and
`code/5-deep-agents/deep_agent{,.answers}.py` (audited 2026-07-24 against
integrate.api.nvidia.com/v1/models with a live key):

  - "deepseek": deepseek-ai/deepseek-r1-0528 is RETIRED from the catalog —
    every request 404s on every pathway. Remap to deepseek-ai/deepseek-v4-flash
    (served; ~27s incl. reasoning, inside client timeouts).
  - "llama"/"claude": meta/llama-3.3-70b-instruct is served but answered in
    ~90s — beyond ChatNVIDIA's 60s default timeout, so both the sync and
    aiohttp paths raise ReadTimeout/SocketTimeoutError and the Deep Agent
    backend errors on every turn. Remap to meta/llama-3.1-70b-instruct
    (same family, ~0.6s). Revisit if 3.3-70b capacity recovers.

Display names are updated too so the UI stays honest. Idempotent
(exact-string replaces; re-runs are no-ops). Usage: tune_model_map.py <repo>.
"""
import os
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "/sandbox/workshop-build-an-agent"
MARKER = "# [sandbox] model map tuned"

REPLACEMENTS = [
    ('"llama": "meta/llama-3.3-70b-instruct"',
     '"llama": "meta/llama-3.1-70b-instruct"'),
    ('"claude": "meta/llama-3.3-70b-instruct"',
     '"claude": "meta/llama-3.1-70b-instruct"'),
    ('"deepseek": "deepseek-ai/deepseek-r1-0528"',
     '"deepseek": "deepseek-ai/deepseek-v4-flash"'),
    ('"llama": "Llama 3.3 (Meta)"', '"llama": "Llama 3.1 (Meta)"'),
    ('"deepseek": "DeepSeek R1 (DeepSeek)"',
     '"deepseek": "DeepSeek V4 Flash (DeepSeek)"'),
]

TARGETS = [
    "demo/backend/agent.py",
    "code/5-deep-agents/deep_agent.py",
    "code/5-deep-agents/deep_agent.answers.py",
]

changed = 0
for rel in TARGETS:
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        print(f"skip (missing): {rel}")
        continue
    text = open(path).read()
    orig = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text != orig:
        if MARKER not in text and "MODEL_MAP = {" in text:
            text = text.replace(
                "MODEL_MAP = {",
                MARKER + " — r1-0528 retired; 3.3-70b exceeds client timeouts "
                "(see skill scripts/tune_model_map.py)\nMODEL_MAP = {", 1)
        open(path, "w").write(text)
        changed += 1
        print(f"model map tuned: {rel}")

print(f"done: {changed} file(s) modified")
