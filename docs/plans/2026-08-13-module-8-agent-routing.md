# Module 8 — Agent Routing (NeMo Switchyard) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build workshop Module 8 — doc pages, a 95-minute two-track lab, and the Routing Client app tile — teaching model routing with NeMo Switchyard per the approved spec at `docs/specs/2026-08-13-module-8-agent-routing-design.md` (Rev 5).

**Architecture:** Learner-edited routing logic lives in `code/8-agent-routing/routing_lab.py` (blanks + CLI verifier); a provided FastAPI+SSE Routing Client renders that logic live and unlocks capability-by-capability; `.devx/8-agent-routing/` doc pages follow the established dx-theme conventions; all Switchyard SDK contact is confined to `switchyard_shim.py` behind pinned versions.

**Tech Stack:** Python 3.12, `langchain-nvidia-ai-endpoints` (ChatNVIDIA), `nemo-switchyard` (pinned at Task 1), `switchyard-server` (pinned release binary), FastAPI + sse-starlette + uvicorn, vanilla JS/HTML reusing `devx-theme.css`, pytest (maintainer-side), jupytext (notebook twins).

## Global Constraints

Copied from the spec — every task's requirements implicitly include these:

- **Model pool (exact ids):** strong `nvidia/nemotron-3-super-120b-a12b` · efficient `nvidia/nemotron-3.5-lightning-30b-a3b` · classifier = the efficient model. Endpoint `https://integrate.api.nvidia.com/v1`. **`NVIDIA_API_KEY` is the only secret.**
- **Super is a stand-in:** the lesson must state plainly (required Ex1 dx-aside "A stand-in for the frontier") that in production the strong slot is often closed frontier models (OpenAI/Anthropic). Never present Super as literally frontier.
- **The client is a window, not a wizard:** all routing decisions computed by learner-edited `routing_lab.py`; the UI renders events only, contains zero routing logic.
- **The SDK never carries the pedagogy:** Ex1/Ex2/Ex5 must work with Switchyard absent; only Ex3 (+install) touches the SDK, via `switchyard_shim.py` — the ONLY file that imports it.
- **Pins single-sourced:** every volatile string (package versions, model ids, binary URLs) lives in `code/8-agent-routing/constants.py` or `scripts/install_switchyard.sh` — never inline elsewhere.
- **Diagrams:** hand-authored dark SVGs only. **No mermaid** (ARM64 + M7 root-cause lessons).
- **Docs conventions:** dx- widgets (`dx-hero`, `dx-island`, `dx-quiz`, `dx-bet`, `dx-peek is-solution`, `dx-term`, `dx-bento`), `<!-- fold:break -->` section breaks, per-blank `🆘 Need some help?` peeks, `openOrCreateFileInJupyterLab` / `openNewTerminal` / `goToLineAndSelect` buttons — mirror `.devx/7-agent-harnesses/*.md` exactly.
- **Two-track lab naming:** `routing_lab.py` / `routing_lab.ipynb` with `# TODO: Exercise Na` markers; complete keys in `routing_lab.answers.py` / `.answers.ipynb`; notebook blanks get collapsible **💡 NEED SOME HELP?** accordions.
- **Printed numbers:** every expected output in docs is a placeholder until Task 20 calibrates real values on the A100 — mark with `<!-- CALIBRATE -->` comments until then.
- **This dev box is a GB10 (aarch64, 128GB unified):** no SM80/NIM-container verification here (defer to Task 20 on Brev A100); run subagents sequentially (max 1–2); memory-frugal commands.
- **Canonical strategy names** (CLI, client, race mode all use these strings): `strong_only`, `efficient_only`, `manual_classifier`, `switchyard_stage`, `gateway`, `mock_demo`.
- **Commit style:** repo uses `type(scope): summary` (e.g. `feat(module-8): …`, `docs(module-8): …`).

## File Structure

```
code/8-agent-routing/
├── README.md                       # code-dir readme (module map, run commands)
├── constants.py                    # model ids, PRICING, endpoints, strategy names
├── routing_lab.py                  # LEARNER file: blanks 1a,1b,2a,2b,3a,3b,5 + provided harness/runner
├── routing_lab.answers.py          # complete implementation (source of truth; blanked copy derived from it)
├── routing_lab.ipynb / routing_lab.answers.ipynb   # jupytext twins + 💡 accordions
├── switchyard_shim.py              # ONLY SDK importer: make_router/pick_target + MockRouter
├── routes.toml.template            # Ex4 blank (commented skeleton)
├── routes.toml.answers             # completed config (+ commented 4b local-NIM variant)
├── test_data/routing_tasks.jsonl   # 12-task suite (6 commodity/verifiable, 6 frontier)
├── routing_client/
│   ├── server.py                   # FastAPI: /api/status /api/query /api/race + static mount
│   ├── start_client.sh             # launcher-tile entry point
│   └── static/{index.html, client.css, client.js, yard.svg}
├── scripts/
│   ├── install_switchyard.sh       # THE pin record: pip pins + release binary + sha256
│   ├── smoke_switchyard.sh         # maintainer canary
│   └── serve_local_nim.sh          # Ex4b NIM wrapper (M2 runbook)
└── tests/                          # maintainer-side pytest (test the .answers module)
    ├── conftest.py                 # FakeChat + fixtures
    ├── test_suite_checkers.py
    ├── test_lab_logic.py
    └── test_client_logic.py
.devx/8-agent-routing/              # shell copied from 7-agent-harnesses, then 6 content pages
docs/specs/switchyard-api-notes.md  # Task 1 spike output
.claude/skills/module-8/            # tutor skill + references/
```

---

## Phase 0 — Ground truth

### Task 1: Switchyard verification spike + pin record

**Files:**
- Create: `docs/specs/switchyard-api-notes.md`
- Create: `code/8-agent-routing/scripts/install_switchyard.sh`
- Create: `code/8-agent-routing/scripts/smoke_switchyard.sh`

**Interfaces:**
- Produces: `switchyard-api-notes.md` documenting (a) exact pip package/version pins, (b) the real Python routing surface (import paths, constructor signatures) that Task 5's shim internals must use, (c) server binary install path for aarch64 + x86_64, (d) whether gateway responses report the upstream model id in the `model` field (consumed by Task 12), (e) whether `langchain-nvidia-switchyard` exists on PyPI.
- Produces: `install_switchyard.sh` (idempotent, pins inside) and `smoke_switchyard.sh` — both consumed by postBuild (Task 18) and CI-style checks.

- [ ] **Step 1: Probe the endpoints and packages (read-only)**

```bash
# Lightning model live on the hosted API?
curl -s https://integrate.api.nvidia.com/v1/models -H "Authorization: Bearer $NVIDIA_API_KEY" \
  | python3 -c "import sys,json; ms=[m['id'] for m in json.load(sys.stdin)['data']]; print([m for m in ms if 'lightning' in m or 'nemotron-3-super' in m])"
# PyPI surfaces (no install yet)
pip index versions nemo-switchyard 2>/dev/null || pip download nemo-switchyard --no-deps -d /tmp/claude-syd --quiet && ls /tmp/claude-syd
pip index versions langchain-nvidia-switchyard 2>/dev/null || echo "middleware pkg: NOT on PyPI"
```

- [ ] **Step 2: Install the latest release into a scratch venv and record the real API**

```bash
python3 -m venv /tmp/claude-syd-venv && /tmp/claude-syd-venv/bin/pip install "nemo-switchyard[cli]"
/tmp/claude-syd-venv/bin/python - <<'EOF'
import importlib, pkgutil, inspect
import switchyard  # adjust if top-level name differs — record whatever is true
print("version:", getattr(switchyard, "__version__", "?"))
for name in ("switchyard.libsy", "switchyard"):
    try:
        m = importlib.import_module(name)
        print(name, "->", [x for x in dir(m) if not x.startswith("_")])
    except Exception as e:
        print(name, "FAILED:", e)
EOF
```

Record in the notes: exact import path for targets + algorithms, constructor/call signatures (use `inspect.signature`), and how a selection call returns its choice. If the pip package has no Python routing surface (CLI-only), record that — Task 5's shim then wraps the **server + `llm_classifier` route** via HTTP instead, and the notes must say so explicitly.

- [ ] **Step 3: Verify the server path on this machine (aarch64)**

```bash
which switchyard-server || ls /tmp/claude-syd-venv/bin | grep -i switch
# If not shipped via pip: check GitHub releases for a prebuilt aarch64 + x86_64 binary and record URLs + sha256s.
```

- [ ] **Step 4: Dry-run a minimal config against the hosted endpoint**

Write `/tmp/claude-syd/routes-probe.toml` using the spec §0 schema (`schema_version = 1`, one `llm_clients.nvidia` with `api_key_env = "NVIDIA_API_KEY"`, targets weak/strong with the Global Constraints model ids, one `llm_classifier` route id `switchyard`), then:

```bash
switchyard-server --config /tmp/claude-syd/routes-probe.toml --dry-run
switchyard-server --config /tmp/claude-syd/routes-probe.toml --host 127.0.0.1 --port 4000 &
sleep 2 && curl -s localhost:4000/v1/models
curl -s localhost:4000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"switchyard","messages":[{"role":"user","content":"hi"}]}' | python3 -m json.tool | head -30
kill %1
```

Record: does the response `model` field name the upstream target id? (Feeds Task 12's attribution decision.)

- [ ] **Step 5: Write `docs/specs/switchyard-api-notes.md`**

Sections: `## Pins` (exact versions), `## Python surface` (verbatim signatures or "CLI/server only"), `## Server install` (per-arch), `## Gateway attribution` (answer from Step 4), `## Deviations from spec assumptions` (anything the spec's §0 got wrong).

- [ ] **Step 6: Write `scripts/install_switchyard.sh`** — idempotent, pins from Step 2/3:

```bash
#!/bin/bash
# THE single pin record for Module 8's Switchyard stack (spec §8b.2/§8b.7).
# Bump pins ONLY via the runbook in code/8-agent-routing/README.md.
set -euo pipefail
SWITCHYARD_PIP_PIN="nemo-switchyard[cli]==X.Y.Z"        # <- from api-notes
SERVER_VERSION="vX.Y.Z"                                  # <- from api-notes
SERVER_SHA256_x86_64="<sha256>"
SERVER_SHA256_aarch64="<sha256>"

pip install --quiet "$SWITCHYARD_PIP_PIN"
if ! command -v switchyard-server >/dev/null; then
  ARCH=$(uname -m)
  URL="https://github.com/NVIDIA-NeMo/Switchyard/releases/download/${SERVER_VERSION}/switchyard-server-${ARCH}"
  curl -fsSL "$URL" -o /tmp/switchyard-server
  echo "$(eval echo \$SERVER_SHA256_${ARCH})  /tmp/switchyard-server" | sha256sum -c -
  install -m 0755 /tmp/switchyard-server "$HOME/.local/bin/switchyard-server"
fi
switchyard-server --help >/dev/null && echo "✅ switchyard-server ready"
```

(Adjust the download stanza to whatever Step 3 found is actually true — pip-shipped binary means the whole `if` block collapses to a comment saying so.)

- [ ] **Step 7: Write `scripts/smoke_switchyard.sh`** — the canary (spec §8b.6):

```bash
#!/bin/bash
# Maintainer canary: run before events and on any pin bump.
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/install_switchyard.sh
switchyard-server --config routes.toml.answers --dry-run
python3 - <<'EOF'
import json, os, urllib.request
req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=json.dumps({"model": "nvidia/nemotron-3.5-lightning-30b-a3b",
                     "messages": [{"role": "user", "content": "Reply OK"}],
                     "max_tokens": 8}).encode(),
    headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}",
             "Content-Type": "application/json"})
print("✅ hosted efficient target:", json.load(urllib.request.urlopen(req))["model"])
EOF
pip index versions nemo-switchyard | head -2   # drift visibility vs pin
echo "✅ smoke complete"
```

(`routes.toml.answers` lands in Task 6 — until then run the dry-run against the Step 4 probe config; note that in the script header and remove the note in Task 6.)

- [ ] **Step 8: Verify both scripts run clean** (`bash scripts/install_switchyard.sh && bash scripts/smoke_switchyard.sh` — smoke's dry-run line pointed at the probe config for now)

- [ ] **Step 9: Commit**

```bash
git add docs/specs/switchyard-api-notes.md code/8-agent-routing/scripts/
git commit -m "feat(module-8): switchyard verification spike, pin record, install + smoke scripts"
```

---

## Phase 1 — Lab core

### Task 2: Constants, task suite, and checkers

**Files:**
- Create: `code/8-agent-routing/constants.py`
- Create: `code/8-agent-routing/test_data/routing_tasks.jsonl`
- Create: `code/8-agent-routing/tests/conftest.py`
- Create: `code/8-agent-routing/tests/test_suite_checkers.py`
- Create: `code/8-agent-routing/routing_lab.answers.py` (suite-loading + checker section only; grows in Tasks 3–7)

**Interfaces:**
- Produces: `constants.py` — `STRONG_MODEL`, `EFFICIENT_MODEL`, `CLASSIFIER_MODEL`, `NVIDIA_BASE_URL`, `GATEWAY_BASE_URL`, `GATEWAY_ROUTE_ID`, `PRICING: dict[str, dict]`, `STRATEGIES: list[str]`.
- Produces: `load_tasks() -> list[dict]` and `check_task(task: dict, output: str) -> bool` in `routing_lab.answers.py`.
- Produces: `tests/conftest.py` — `FakeChat` fixture used by all later test tasks.

- [ ] **Step 1: Write `constants.py`**

```python
"""Module 8 single source of truth (spec §8b.7): every volatile string lives
here or in scripts/install_switchyard.sh — never inline in exercises or docs."""

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

STRONG_MODEL = "nvidia/nemotron-3-super-120b-a12b"        # plays the frontier role (stand-in — see lab Ex1 aside)
EFFICIENT_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
CLASSIFIER_MODEL = EFFICIENT_MODEL                         # no third model by design

# USD per 1M tokens {in, out}. Teaching rates representative of public per-token
# pricing tiers; recalibrate/source in the Task 20 pass.  <!-- CALIBRATE -->
PRICING = {
    STRONG_MODEL:    {"in": 5.00, "out": 15.00},
    EFFICIENT_MODEL: {"in": 0.30, "out": 1.20},
}

GATEWAY_BASE_URL = "http://localhost:4000/v1"
GATEWAY_ROUTE_ID = "switchyard"

STRATEGIES = ["strong_only", "efficient_only", "manual_classifier",
              "switchyard_stage", "gateway", "mock_demo"]

AT_SCALE_TASKS_PER_DAY = 1000   # the tokenomics extrapolation everyone sees
```

- [ ] **Step 2: Author the 12-task suite** — `test_data/routing_tasks.jsonl`, one JSON object per line. 6 `commodity` (verifiable), 6 `frontier` (5 verifiable + 1 judged). Fields: `id`, `kind`, `prompt`, `check` (`{"type": "contains"|"contains_all"|"judge", "value": ...}`).

```jsonl
{"id":"json_reformat","kind":"commodity","prompt":"Convert to a JSON object: name=Ada, role=engineer, team=platform. Reply with ONLY the JSON.","check":{"type":"contains_all","value":["\"name\"","Ada","\"team\"","platform"]}}
{"id":"fact_year","kind":"commodity","prompt":"What year was the first moon landing? Answer with just the year.","check":{"type":"contains","value":"1969"}}
{"id":"title_case","kind":"commodity","prompt":"Rewrite in Title Case, reply with only the rewritten text: 'the switchyard routes every train'","check":{"type":"contains","value":"The Switchyard Routes Every Train"}}
{"id":"csv_count","kind":"commodity","prompt":"How many values are in this CSV row: a,b,c,d,e? Answer with just the number.","check":{"type":"contains","value":"5"}}
{"id":"email_extract","kind":"commodity","prompt":"Extract the email address from: 'Contact Ada at ada@example.com for details.' Reply with only the email address.","check":{"type":"contains","value":"ada@example.com"}}
{"id":"unit_convert","kind":"commodity","prompt":"Convert 2 hours to minutes. Answer with just the number.","check":{"type":"contains","value":"120"}}
{"id":"logic_order","kind":"frontier","prompt":"Alice is taller than Bob. Bob is taller than Carol. Dana is shorter than Carol. Who is the second-shortest person? Answer with just the name.","check":{"type":"contains","value":"Carol"}}
{"id":"math_multistep","kind":"frontier","prompt":"A team ships 3 features per sprint. Each feature needs 2 reviews and each review takes 45 minutes. How many review-HOURS does the team spend across a 4-sprint quarter? Answer with just the number.","check":{"type":"contains","value":"18"}}
{"id":"code_alias","kind":"frontier","prompt":"What does this Python print? x=[1,2,3]; y=x; y.append(4); print(len(x)) — answer with just the number.","check":{"type":"contains","value":"4"}}
{"id":"slo_pick","kind":"frontier","prompt":"Server A: p95=210ms, error rate 0.2%. Server B: p95=180ms, error rate 1.4%. The SLO requires error rate < 0.5% AND p95 < 250ms. Which server meets the SLO? Answer with just the letter.","check":{"type":"contains","value":"A"}}
{"id":"schedule_deps","kind":"frontier","prompt":"Tasks: build(3d) depends on design(2d); test(2d) depends on build; docs(1d) depends on design and can run parallel to build/test. What is the minimum total days to finish everything? Answer with just the number.","check":{"type":"contains","value":"7"}}
{"id":"explain_routing","kind":"frontier","prompt":"In exactly 3 bullet points, explain to a product manager why routing between a small open model and a large frontier model can cut cost dramatically while losing little accuracy.","check":{"type":"judge","value":"Award PASS only if the answer has ~3 bullets and mentions (a) that most calls are easy / calls differ in difficulty, and (b) that only a minority of calls need the expensive model."}}
```

- [ ] **Step 3: Write the test fixture** — `tests/conftest.py`:

```python
import sys, types, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest

class FakeResponse:
    def __init__(self, content, in_tok=100, out_tok=20):
        self.content = content
        self.usage_metadata = {"input_tokens": in_tok, "output_tokens": out_tok}
        self.tool_calls = []

class FakeChat:
    """Stands in for ChatNVIDIA: returns queued responses, records prompts."""
    def __init__(self, responses):
        self.responses = list(responses); self.calls = []
    def invoke(self, messages):
        self.calls.append(messages)
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]

@pytest.fixture
def fake_chat():
    return lambda *responses: FakeChat([FakeResponse(r) if isinstance(r, str) else r for r in responses])
```

- [ ] **Step 4: Write failing checker tests** — `tests/test_suite_checkers.py`:

```python
import routing_lab_answers_import_helper  # see Step 5 note
from routing_lab_answers_import_helper import answers as lab

def test_load_tasks_shape():
    tasks = lab.load_tasks()
    assert len(tasks) == 12
    assert {t["kind"] for t in tasks} == {"commodity", "frontier"}

def test_contains_checker():
    t = {"check": {"type": "contains", "value": "1969"}}
    assert lab.check_task(t, "It was 1969.") is True
    assert lab.check_task(t, "no idea") is False

def test_contains_all_checker():
    t = {"check": {"type": "contains_all", "value": ["Ada", "platform"]}}
    assert lab.check_task(t, '{"name":"Ada","team":"platform"}') is True
    assert lab.check_task(t, "Ada only") is False

def test_judge_checker_uses_injected_judge():
    t = {"check": {"type": "judge", "value": "rubric text"}}
    assert lab.check_task(t, "three bullets...", judge=lambda rubric, out: True) is True
```

Import helper (`tests/routing_lab_answers_import_helper.py`) because the answers filename has a dot: 

```python
import importlib.util, pathlib
p = pathlib.Path(__file__).resolve().parents[1] / "routing_lab.answers.py"
spec = importlib.util.spec_from_file_location("routing_lab_answers", p)
answers = importlib.util.module_from_spec(spec); spec.loader.exec_module(answers)
```

- [ ] **Step 5: Run tests, verify they fail** — `cd code/8-agent-routing && python3 -m pytest tests/test_suite_checkers.py -v` → FAIL (no answers module yet). (`pip install pytest` if absent.)

- [ ] **Step 6: Start `routing_lab.answers.py` with the suite section**

```python
"""Module 8 answers — complete implementations. Learner copy is derived from
this file in Task 8. Structure: constants import, suite, Ex1..Ex5 sections,
provided harness, CLI runner."""
import json, pathlib
from constants import *  # model ids, PRICING, STRATEGIES, AT_SCALE_TASKS_PER_DAY

HERE = pathlib.Path(__file__).resolve().parent

def load_tasks():
    lines = (HERE / "test_data" / "routing_tasks.jsonl").read_text().splitlines()
    return [json.loads(l) for l in lines if l.strip()]

def check_task(task, output, judge=None):
    c, out = task["check"], (output or "")
    if c["type"] == "contains":     return c["value"].lower() in out.lower()
    if c["type"] == "contains_all": return all(v.lower() in out.lower() for v in c["value"])
    if c["type"] == "judge":
        if judge is None:
            from functools import partial
            judge = _default_judge   # defined with the model helpers in Task 3
        return judge(c["value"], out)
    raise ValueError(f"unknown check type {c['type']}")
```

- [ ] **Step 7: Run tests, verify pass** (judge test passes via injection; `_default_judge` stub can `raise NotImplementedError` until Task 3 — the injected-judge test never hits it)

- [ ] **Step 8: Commit** — `git add code/8-agent-routing && git commit -m "feat(module-8): constants, 12-task routing suite, checkers + tests"`

### Task 3: Exercise 1 — model pool + bill meter (answers) + CLI runner skeleton

**Files:**
- Modify: `code/8-agent-routing/routing_lab.answers.py`
- Create: `code/8-agent-routing/tests/test_lab_logic.py`

**Interfaces:**
- Produces: `build_model_pool() -> dict[str, ChatNVIDIA]` keyed `{"strong","efficient"}` **(Ex1a blank)**; `RunningBill` (provided) with `.add(model_id, usage, cost, latency)`, `.total_cost`, `.by_model`, `.summary() -> str`; `bill_call(model_id, chat, messages, bill) -> tuple[response, receipt]` **(Ex1b blank)**; receipt dict keys — used verbatim by the client and race mode: `{"model", "input_tokens", "output_tokens", "cost", "latency", "counterfactual_cost", "why", "router_tax"}`; `run_suite(strategy: str, bill: RunningBill, judge=None) -> list[dict]` (provided) returning TaskResult dicts `{"id","kind","passed","cost","latency","models":{model_id:n_calls},"router_tax"}`; `_default_judge(rubric, output) -> bool`.

- [ ] **Step 1: Write failing tests** (append to `tests/test_lab_logic.py`):

```python
from routing_lab_answers_import_helper import answers as lab
from conftest import FakeResponse, FakeChat
from constants import STRONG_MODEL, EFFICIENT_MODEL, PRICING

def test_bill_call_prices_and_counterfactuals():
    bill = lab.RunningBill()
    chat = FakeChat([FakeResponse("hi", in_tok=1_000_000, out_tok=1_000_000)])
    resp, receipt = lab.bill_call(EFFICIENT_MODEL, chat, "prompt", bill)
    p = PRICING[EFFICIENT_MODEL]; pf = PRICING[STRONG_MODEL]
    assert abs(receipt["cost"] - (p["in"] + p["out"])) < 1e-9
    assert abs(receipt["counterfactual_cost"] - (pf["in"] + pf["out"])) < 1e-9
    assert bill.total_cost == receipt["cost"]

def test_running_bill_accumulates_by_model():
    bill = lab.RunningBill()
    bill.add(EFFICIENT_MODEL, {"input_tokens": 10, "output_tokens": 10}, 0.01, 0.5)
    bill.add(STRONG_MODEL, {"input_tokens": 10, "output_tokens": 10}, 0.20, 1.5)
    assert set(bill.by_model) == {EFFICIENT_MODEL, STRONG_MODEL}
    assert abs(bill.total_cost - 0.21) < 1e-9
```

- [ ] **Step 2: Run → FAIL** (`python3 -m pytest tests/test_lab_logic.py -v`)

- [ ] **Step 3: Implement in `routing_lab.answers.py`**

```python
import time
from langchain_nvidia_ai_endpoints import ChatNVIDIA

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
```

- [ ] **Step 4: Run → PASS**

- [ ] **Step 5: Add the CLI runner skeleton** (bottom of the answers file; grows a branch per task):

```python
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
```

- [ ] **Step 6: Live smoke (network + `NVIDIA_API_KEY` required)** — `python3 routing_lab.answers.py --exercise 1`. Expected shape: two strategy blocks; strong slower/pricier, efficient cheaper/faster. Record raw numbers in a scratch note for Task 20 calibration. If `EFFICIENT_MODEL` 404s, re-check Task 1's model listing and update `constants.py` fallback to `nvidia/nemotron-3-nano-30b-a3b` with a `# CALIBRATE` note.

- [ ] **Step 7: Commit** — `git commit -am "feat(module-8): Ex1 model pool, RunningBill meter, billed calls, suite runner + CLI"`

### Task 4: Exercise 2 — hand-rolled classifier router (answers)

**Files:**
- Modify: `code/8-agent-routing/routing_lab.answers.py`
- Modify: `code/8-agent-routing/tests/test_lab_logic.py`

**Interfaces:**
- Produces: `CLASSIFY_PROMPT: str`; `classify_difficulty(query, classifier_chat, bill) -> tuple[str, float]` returning `("COMMODITY"|"FRONTIER", tax_cost)` **(Ex2a blank)**; `route_call(query, pool, bill) -> tuple[response, receipt]` **(Ex2b blank)** — receipt `why` = `"classifier: COMMODITY"` etc., `router_tax` = classifier cost.

- [ ] **Step 1: Failing tests**

```python
def test_classifier_parses_and_fails_up(fake_chat):
    bill = lab.RunningBill()
    assert lab.classify_difficulty("q", fake_chat("COMMODITY"), bill)[0] == "COMMODITY"
    assert lab.classify_difficulty("q", fake_chat("frontier."), bill)[0] == "FRONTIER"
    assert lab.classify_difficulty("q", fake_chat("dunno maybe hard?"), bill)[0] == "FRONTIER"  # fail UP

def test_route_call_dispatches_and_taxes(fake_chat, monkeypatch):
    bill = lab.RunningBill()
    pool = {"strong": fake_chat("strong answer"), "efficient": fake_chat("easy answer")}
    monkeypatch.setattr(lab, "build_classifier", lambda: fake_chat("COMMODITY"))
    resp, receipt = lab.route_call("reformat this", pool, bill)
    assert receipt["model"] == lab.EFFICIENT_MODEL
    assert receipt["router_tax"] > 0
    assert "COMMODITY" in receipt["why"]
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implement**

```python
CLASSIFY_PROMPT = (
    "You are a routing dispatcher. Classify this request as COMMODITY "
    "(extraction, reformatting, single-fact lookup, simple transforms) or FRONTIER "
    "(multi-step reasoning, planning, synthesis, ambiguity). "
    "Reply with exactly one word: COMMODITY or FRONTIER.\n\nRequest:\n{query}"
)

def build_classifier():
    return ChatNVIDIA(model=CLASSIFIER_MODEL, temperature=0.0,
                      max_completion_tokens=8, timeout=60)

def classify_difficulty(query, classifier_chat, bill):
    # === Exercise 2a (answer) ===
    _, receipt = bill_call(CLASSIFIER_MODEL, classifier_chat,
                           CLASSIFY_PROMPT.format(query=query), bill, why="router-tax")
    raw = _.content if hasattr(_, "content") else str(_)
    token = (raw or "").strip().upper().split()[0].strip(".,!:;") if (raw or "").strip() else ""
    verdict = token if token in ("COMMODITY", "FRONTIER") else "FRONTIER"   # misroutes fail UP
    return verdict, receipt["cost"]

def route_call(query, pool, bill):
    # === Exercise 2b (answer) ===
    verdict, tax = classify_difficulty(query, build_classifier(), bill)
    lane = "efficient" if verdict == "COMMODITY" else "strong"
    model_id = EFFICIENT_MODEL if lane == "efficient" else STRONG_MODEL
    resp, receipt = bill_call(model_id, pool[lane], query, bill, why=f"classifier: {verdict}")
    receipt["router_tax"] = tax
    return resp, receipt
```

(Note the answer returns the response object from `bill_call` inside `classify_difficulty` via `_` — keep it simple: have `bill_call` return the response first; the code above already does.)

- [ ] **Step 4: Run → PASS.** Add `_print_exercise_2` (runs `manual_classifier` suite, prints the three-row comparison + `router tax: $X (N% of spend)` line) and register `2:` in the CLI dict.

- [ ] **Step 5: Live smoke** — `python3 routing_lab.answers.py --exercise 2`; routed row should land between the Ex1 baselines. Record numbers for Task 20.

- [ ] **Step 6: Commit** — `git commit -am "feat(module-8): Ex2 hand-rolled classifier router with fail-up parsing + router tax"`

### Task 5: Exercise 3 — Switchyard shim + stage-routed calls (answers)

**Files:**
- Create: `code/8-agent-routing/switchyard_shim.py`
- Modify: `code/8-agent-routing/routing_lab.answers.py`
- Modify: `code/8-agent-routing/tests/test_lab_logic.py`

**Interfaces:**
- Consumes: the verified API from `docs/specs/switchyard-api-notes.md` (Task 1).
- Produces: `switchyard_shim.make_router(capable_meta: dict, efficient_meta: dict) -> RouterHandle`; `switchyard_shim.pick_target(router, messages: list, tool_events: list[str]) -> "capable"|"efficient"`; `switchyard_shim.MockRouter` (deterministic); `switchyard_shim.SDK_AVAILABLE: bool`. Lab-side: `make_lab_router()` **(Ex3a blank)** and `switchyard_call(query, pool, bill, router=None) -> tuple[response, receipt]` **(Ex3b blank)**, receipt `why` = `"stage: exploration"`/`"stage: synthesis"`/`"mock"`.

- [ ] **Step 1: Write `switchyard_shim.py`** — full file; the two `<ADJUST>` blocks are the only lines that change per the api-notes:

```python
"""The ONLY file in Module 8 that imports the Switchyard SDK (spec §8b.3).
If the import or API shifts upstream, fix it HERE — nothing else changes.
Verified against the pins in scripts/install_switchyard.sh; see
docs/specs/switchyard-api-notes.md for the recorded surface."""

SDK_AVAILABLE = True
try:
    from switchyard.libsy import LlmTarget, algorithms          # <ADJUST per api-notes>
except Exception:                                               # ImportError or any v0.x surprise
    SDK_AVAILABLE = False

class MockRouter:
    """Deterministic fallback + 'Demo (mock)' strategy. Heuristic stage signal:
    tool activity or short prompts → efficient; otherwise capable."""
    def pick(self, messages, tool_events):
        text = str(messages[-1]) if messages else ""
        if tool_events or len(text) < 200:
            return "efficient"
        return "capable"

def make_router(capable_meta, efficient_meta):
    if not SDK_AVAILABLE:
        print("⚠️  switchyard SDK unavailable — using MockRouter (see scripts/install_switchyard.sh)")
        return MockRouter()
    return algorithms.stage_router(                              # <ADJUST per api-notes>
        LlmTarget("capable", capable_meta["id"]),
        LlmTarget("efficient", efficient_meta["id"]),
    )

def pick_target(router, messages, tool_events):
    if isinstance(router, MockRouter):
        return router.pick(messages, tool_events)
    decision = router.select(messages=messages, signals=tool_events)   # <ADJUST per api-notes>
    return "capable" if "capable" in str(decision).lower() else "efficient"
```

- [ ] **Step 2: Failing tests** (SDK-independent — they exercise the Mock path + the lab wiring):

```python
import switchyard_shim as shim

def test_mock_router_is_deterministic():
    r = shim.MockRouter()
    assert r.pick(["short prompt"], []) == "efficient"
    assert r.pick(["x" * 500], []) == "capable"
    assert r.pick(["x" * 500], ["tool_result"]) == "efficient"

def test_switchyard_call_routes_via_router(fake_chat):
    bill = lab.RunningBill()
    pool = {"strong": fake_chat("deep answer"), "efficient": fake_chat("quick answer")}
    resp, receipt = lab.switchyard_call("short prompt", pool, bill, router=shim.MockRouter())
    assert receipt["model"] == lab.EFFICIENT_MODEL
    assert receipt["router_tax"] == 0.0        # stage routing: no extra LLM call
    assert receipt["why"].startswith(("stage:", "mock"))
```

- [ ] **Step 3: Run → FAIL**, then implement in the answers file:

```python
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
    why = "mock" if isinstance(router, shim.MockRouter) else f"stage: {'synthesis' if lane == 'capable' else 'exploration'}"
    return bill_call(model_id, pool[lane_key], query, bill, why=why)
```

- [ ] **Step 4: Run → PASS.** Add `_print_exercise_3` (suite under `switchyard_stage` + per-call `[route → …]` trace prints) and register `3:` in the CLI dict.

- [ ] **Step 5: Live smoke with the real SDK** — `python3 routing_lab.answers.py --exercise 3`. If the real router surface differs from the `<ADJUST>` guesses, fix the shim (only) and update `switchyard-api-notes.md`.

- [ ] **Step 6: Commit** — `git commit -am "feat(module-8): switchyard shim (sole SDK import), mock fallback, Ex3 stage-routed calls"`

### Task 6: Exercise 4 — gateway configs + local-NIM script

**Files:**
- Create: `code/8-agent-routing/routes.toml.template`
- Create: `code/8-agent-routing/routes.toml.answers`
- Create: `code/8-agent-routing/scripts/serve_local_nim.sh`
- Modify: `code/8-agent-routing/routing_lab.answers.py` (Ex4 runner branch)
- Modify: `code/8-agent-routing/scripts/smoke_switchyard.sh` (point dry-run at `routes.toml.answers`; drop the Task 1 interim note)

**Interfaces:**
- Produces: `routes.toml.answers` — route id **`switchyard`**, `llm_classifier` + `mode = "escalation"`, `escalation.confirmations = 2`, targets `weak`/`strong` on the Global Constraints model ids (this exact file is what smoke + the client's gateway mode run against); `gateway_call(query, bill) -> tuple[str, receipt]` (provided helper using `openai`-style POST to `GATEWAY_BASE_URL` with `model=GATEWAY_ROUTE_ID`).

- [ ] **Step 1: Write `routes.toml.answers`** (adjust key names only if Task 1's notes demand):

```toml
schema_version = 1

[llm_clients.nvidia]
format = "openai_chat"
base_url = "https://integrate.api.nvidia.com/v1"
api_key_env = "NVIDIA_API_KEY"

[targets.weak]
id = "nvidia/nemotron-3.5-lightning-30b-a3b"
llm_client = "nvidia"

[targets.strong]
id = "nvidia/nemotron-3-super-120b-a12b"
llm_client = "nvidia"

[routes.switchyard]
id = "switchyard"
type = "llm_classifier"
mode = "escalation"
classifier_target = "weak"
weak_target = "weak"
strong_target = "strong"
escalation.confirmations = 2

# ---- Exercise 4b (optional GPU path): local NIM as the weak target ----
# [llm_clients.local_nim]
# format = "openai_chat"
# base_url = "http://localhost:8000/v1"
#
# [targets.weak]                      # replaces the hosted weak target
# id = "nvidia/nemotron-3-nano-30b-a3b"
# llm_client = "local_nim"
```

- [ ] **Step 2: Derive `routes.toml.template`** — same file with the values of `format`/`base_url`/`api_key_env`, both target `id`s, and the five `[routes.switchyard]` algorithm keys replaced by `# TODO: Exercise 4 — <hint>` comments (structure and section headers stay; the blank is filling values, not inventing schema).

- [ ] **Step 3: Validate** — `switchyard-server --config routes.toml.answers --dry-run` → exits 0. Template must FAIL dry-run (that's the point): confirm non-zero exit.

- [ ] **Step 4: Add `gateway_call` + `_print_exercise_4`** to the answers file:

```python
def gateway_call(query, bill):
    """Provided: call the route id through the local gateway; bill from the response."""
    import urllib.request, json as _json, time as _t
    t0 = _t.perf_counter()
    req = urllib.request.Request(
        f"{GATEWAY_BASE_URL}/chat/completions",
        data=_json.dumps({"model": GATEWAY_ROUTE_ID,
                          "messages": [{"role": "user", "content": query}]}).encode(),
        headers={"Content-Type": "application/json"})
    body = _json.load(urllib.request.urlopen(req, timeout=180))
    latency = _t.perf_counter() - t0
    served_by = body.get("model", GATEWAY_ROUTE_ID)     # attribution — per Task 1 notes
    usage = {"input_tokens": body["usage"]["prompt_tokens"],
             "output_tokens": body["usage"]["completion_tokens"]}
    model_id = served_by if served_by in PRICING else EFFICIENT_MODEL
    cost = _price(model_id, usage)
    bill.add(model_id, usage, cost, latency)
    return body["choices"][0]["message"]["content"], {
        "model": served_by, **usage, "cost": cost, "latency": latency,
        "counterfactual_cost": _price(STRONG_MODEL, usage),
        "why": "gateway (external switchyard-server)", "router_tax": 0.0}

def _print_exercise_4():
    print("Start the gateway in another terminal:\n"
          "  switchyard-server --config routes.toml.answers --host 127.0.0.1 --port 4000\n")
    bill = RunningBill()
    for q in ("Convert 2 hours to minutes. Just the number.",
              "Plan a 5-step rollout for migrating a service to a routed model pool."):
        text, receipt = gateway_call(q, bill)
        print(f"[gateway → {receipt['model']}] ${receipt['cost']:.4f} · {receipt['latency']:.1f}s")
    print(bill.summary())
```

- [ ] **Step 5: Write `scripts/serve_local_nim.sh`** — the M2 runbook, parameterized (login to nvcr.io with `$NVIDIA_API_KEY`, `docker volume create nim-cache`, `docker run --gpus 1 --shm-size=16GB -v nim-cache:/opt/nim/.cache -e NGC_API_KEY -p 8000:8000 nvcr.io/nim/nvidia/nemotron-3-nano-30b-a3b:latest`), with a top-of-file guard: `command -v docker || { echo "Docker required — Ex4b is optional; Ex4a is the full exercise"; exit 1; }`. Mirror the exact image tag from `.devx/2-agentic-rag/migrate.md` (read it; do not guess).

- [ ] **Step 6: Live smoke** — start server, `python3 routing_lab.answers.py --exercise 4`, confirm both queries answer and the second (frontier-ish) escalates on a multi-turn variant if the mode supports it; record attribution behavior. Kill server. Run `bash scripts/smoke_switchyard.sh` → all ✅.

- [ ] **Step 7: Commit** — `git commit -am "feat(module-8): Ex4 gateway configs (answers+template), gateway_call, local-NIM script"`

### Task 7: Exercise 5 — routing verdict + at-scale receipt (answers)

**Files:**
- Modify: `code/8-agent-routing/routing_lab.answers.py`
- Modify: `code/8-agent-routing/tests/test_lab_logic.py`

**Interfaces:**
- Produces: `routing_verdict(results_by_strategy: dict[str, list[dict]]) -> dict` **(Ex5 blank)** with keys `rows` (list of `{"strategy","accuracy","cost","frontier_pct","router_tax_pct"}`), `savings_pct` (routed vs strong_only), `monthly` (`{"strategy": usd_at_1k_tasks_per_day}`), `receipt` (the one-line 🧾 string) — consumed verbatim by the CLI, the client's Race mode, and the doc page's expected output.

- [ ] **Step 1: Failing test**

```python
def _mk(strategy, passed, cost, strong_calls, tax):
    return [{"id": f"t{i}", "kind": "commodity", "passed": i < passed, "cost": cost / 12,
             "latency": 1.0, "models": {lab.STRONG_MODEL if i < strong_calls else lab.EFFICIENT_MODEL: 1},
             "router_tax": tax / 12} for i in range(12)]

def test_routing_verdict_math():
    v = lab.routing_verdict({
        "strong_only": _mk("strong_only", 12, 1.55, 12, 0.0),
        "efficient_only": _mk("efficient_only", 9, 0.10, 0, 0.0),
        "manual_classifier": _mk("manual_classifier", 11, 0.41, 3, 0.04),
    })
    routed = next(r for r in v["rows"] if r["strategy"] == "manual_classifier")
    assert routed["accuracy"] == 11 and abs(routed["frontier_pct"] - 25.0) < 0.1
    assert abs(v["savings_pct"] - (1 - 0.41 / 1.55) * 100) < 0.1
    assert "$" in v["receipt"] and "%" in v["receipt"]
    assert abs(v["monthly"]["strong_only"] - 1.55 * lab.AT_SCALE_TASKS_PER_DAY * 30) < 1e-6
```

- [ ] **Step 2: Run → FAIL**, implement:

```python
def routing_verdict(results_by_strategy):
    # === Exercise 5 (answer) ===
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

- [ ] **Step 3: Run → PASS.** Add `_print_exercise_5` (runs `strong_only`, `efficient_only`, `manual_classifier` suites, prints the rows table + `🧾 ` + receipt) and register `5:`.

- [ ] **Step 4: Live smoke** — `--exercise 5`; sanity-check the receipt string reads like the spec §4 example. Record all numbers for Task 20.

- [ ] **Step 5: Commit** — `git commit -am "feat(module-8): Ex5 routing verdict, Pareto rows, at-scale receipt"`

### Task 8: The learner file — blanks + unlock probe

**Files:**
- Create: `code/8-agent-routing/routing_lab.py` (derived from answers)
- Modify: `code/8-agent-routing/routing_lab.answers.py` (add `probe_unlocks`)
- Modify: `code/8-agent-routing/tests/test_lab_logic.py`
- Create: `code/8-agent-routing/README.md`

**Interfaces:**
- Produces: `routing_lab.py` — identical to answers EXCEPT the seven blank bodies (`build_model_pool` 1a, `bill_call` 1b, `classify_difficulty` 2a, `route_call` 2b, `make_lab_router` 3a, `switchyard_call` 3b, `routing_verdict` 5) each replaced by a `# TODO: Exercise Na — <one-line restatement of the page instruction>` comment block + `raise NotImplementedError("Exercise Na")`.
- Produces: `probe_unlocks(module) -> dict` with keys `{"ex1","ex2","ex3","ex5"}` → bool (ex4 is config-file based; the client checks gateway liveness instead) — consumed by the client's `/api/status` and its `systems online: N/5` strip.

- [ ] **Step 1: Failing test**

```python
def test_probe_distinguishes_blank_from_solved():
    import importlib.util, pathlib
    p = pathlib.Path(lab.__file__).parent / "routing_lab.py"
    spec = importlib.util.spec_from_file_location("routing_lab_blank", p)
    blank = importlib.util.module_from_spec(spec); spec.loader.exec_module(blank)
    assert lab.probe_unlocks(blank) == {"ex1": False, "ex2": False, "ex3": False, "ex5": False}
    assert lab.probe_unlocks(lab) == {"ex1": True, "ex2": True, "ex3": True, "ex5": True}
```

- [ ] **Step 2: Implement `probe_unlocks` in the answers file** (it probes ANY module object — the client reloads and passes the learner module):

```python
def probe_unlocks(module):
    """True per exercise iff its blanks no longer raise NotImplementedError.
    Uses cheap fake inputs — never makes network calls."""
    class _FakeResp:
        content, usage_metadata, tool_calls = "COMMODITY", {"input_tokens": 1, "output_tokens": 1}, []
    class _FakeChat:
        def invoke(self, _): return _FakeResp()
    fake_pool = {"strong": _FakeChat(), "efficient": _FakeChat()}
    def _solved(fn, *args, **kw):
        try:
            fn(*args, **kw); return True
        except NotImplementedError:
            return False
        except Exception:
            return True   # runs past the blank → implemented (maybe buggy; still unlocked)
    bill = module.RunningBill()
    return {
        "ex1": _solved(module.bill_call, module.EFFICIENT_MODEL, _FakeChat(), "q", bill),
        "ex2": _solved(module.route_call, "q", fake_pool, module.RunningBill()),
        "ex3": _solved(module.switchyard_call, "q", fake_pool, module.RunningBill(),
                       router=__import__("switchyard_shim").MockRouter()),
        "ex5": _solved(module.routing_verdict, {"strong_only": [], "efficient_only": []}),
    }
```

(`build_model_pool` intentionally not probed — it constructs real clients; `bill_call` blanked is the ex1 gate. If `routing_verdict` with empty dicts raises `KeyError` in the solved version, that's caught by the `except Exception: return True` arm — correct behavior.)

- [ ] **Step 3: Create `routing_lab.py`** — copy the answers file, then for each of the seven functions replace the body. Every blank follows this exact shape (example for 1b; write all seven):

```python
def bill_call(model_id, chat, messages, bill, why="passthrough"):
    """One priced, timed model call. Returns (response, receipt)."""
    # TODO: Exercise 1b — time the call, read response.usage_metadata, price it
    # against PRICING[model_id], bill.add(...) it, and return (response, receipt)
    # with ALL receipt keys: model, input_tokens, output_tokens, cost, latency,
    # counterfactual_cost (same tokens at STRONG_MODEL rates), why, router_tax.
    raise NotImplementedError("Exercise 1b")
```

Also: CLI runner in the learner file catches `NotImplementedError` and prints `❌ Exercise Na not implemented yet — open routing_lab.py and search for "TODO: Exercise Na"` instead of a traceback. Both files import `probe_unlocks` availability the same way (define it in both; it's provided scaffolding, not a blank).

- [ ] **Step 4: Run full test suite → PASS** (`python3 -m pytest tests/ -v`)

- [ ] **Step 5: Verify learner UX** — `python3 routing_lab.py --exercise 1` → friendly ❌ message, exit code 1, no traceback.

- [ ] **Step 6: Write `code/8-agent-routing/README.md`** — sections: what's here (file map from this plan's File Structure), run commands per exercise, the client tile, **Maintainer: pin-bump runbook** (verbatim from spec §8b.6: bump pin in `install_switchyard.sh` → `smoke_switchyard.sh` → run `routing_lab.answers.py --exercise {1..5}` → recalibrate printed numbers → update the version-stamp aside in `meet_switchyard.md`).

- [ ] **Step 7: Commit** — `git commit -am "feat(module-8): learner lab file with TODO blanks, unlock probe, friendly CLI errors, code README"`

### Task 9: Notebook twins

**Files:**
- Create: `code/8-agent-routing/routing_lab.ipynb`, `code/8-agent-routing/routing_lab.answers.ipynb`

- [ ] **Step 1:** `pip show jupytext || pip install jupytext`; generate both notebooks (`jupytext --to ipynb routing_lab.py -o routing_lab.ipynb`, same for answers).
- [ ] **Step 2:** Restructure each into one-markdown-cell + one-code-cell per exercise (match `code/7-agent-harnesses/harness_lab.ipynb`'s cell layout — open it and mirror). Under every blank cell in `routing_lab.ipynb`, add the collapsible solution markdown cell: `<details><summary>💡 NEED SOME HELP?</summary>` + the answer code block + the one-paragraph gotcha note (copy both from the corresponding answers function and the 🆘 text written in Task 17). Final cell in both: launch note for the Routing Client tile + `python routing_lab.py --exercise N` equivalents.
- [ ] **Step 3:** Verify the answers notebook executes top-to-bottom (network required): `jupyter nbconvert --to notebook --execute routing_lab.answers.ipynb --output /tmp/claude-nb-check.ipynb` → exit 0. (Skip the Ex4 gateway cell via a `%%script true` guard cell marked "requires running switchyard-server — see terminal instructions".)
- [ ] **Step 4:** Commit — `git commit -am "feat(module-8): notebook twins with 💡 solution accordions"`

---

## Phase 2 — Routing Client

### Task 10: Client backend (`server.py`) — status, query, receipts

**Files:**
- Create: `code/8-agent-routing/routing_client/server.py`
- Create: `code/8-agent-routing/routing_client/start_client.sh`
- Create: `code/8-agent-routing/tests/test_client_logic.py`

**Interfaces:**
- Consumes: `routing_lab.py` (the LEARNER module — reloaded per request), `probe_unlocks`, receipt dict keys, `STRATEGIES`, `routing_verdict`.
- Produces HTTP API (consumed by `client.js`, Task 11): `GET /api/status` → `{"unlocks": {"ex1"..: bool}, "gateway_alive": bool, "key_present": bool, "sdk_available": bool}`; `POST /api/query` `{"text": str, "strategy": str}` → SSE events named `route_decision` (`{"lane","model","why"}`), `receipt` (the receipt dict + `"counterfactual_saved"`), `answer` (`{"text"}`), `error` (`{"message"}`); `POST /api/race` `{"strategies": [str]}` → SSE `race_row` (one verdict row dict per strategy), `race_receipt` (`{"receipt": str}`). Static files mounted at `/`.

- [ ] **Step 1: Failing tests** (FastAPI TestClient; monkeypatch the lab module with the ANSWERS module + FakeChat so no network):

```python
from fastapi.testclient import TestClient

def _client(monkeypatch, fake_chat):
    import routing_client.server as srv
    from routing_lab_answers_import_helper import answers
    monkeypatch.setattr(srv, "_load_lab", lambda: answers)
    monkeypatch.setattr(answers, "build_model_pool",
                        lambda: {"strong": fake_chat("big"), "efficient": fake_chat("small")})
    monkeypatch.setattr(answers, "build_classifier", lambda: fake_chat("COMMODITY"))
    return TestClient(srv.app)

def test_status_reports_unlocks(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    body = c.get("/api/status").json()
    assert body["unlocks"] == {"ex1": True, "ex2": True, "ex3": True, "ex5": True}
    assert set(body) >= {"unlocks", "gateway_alive", "key_present", "sdk_available"}

def test_query_streams_decision_then_receipt(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    r = c.post("/api/query", json={"text": "reformat this", "strategy": "manual_classifier"})
    events = [l for l in r.text.splitlines() if l.startswith("event:")]
    assert events[0] == "event: route_decision"
    assert "event: receipt" in events and "event: answer" in events

def test_locked_strategy_yields_error(monkeypatch, fake_chat):
    import routing_client.server as srv, importlib.util, pathlib
    p = pathlib.Path(srv.__file__).parents[1] / "routing_lab.py"
    spec = importlib.util.spec_from_file_location("blank_lab", p)
    blank = importlib.util.module_from_spec(spec); spec.loader.exec_module(blank)
    monkeypatch.setattr(srv, "_load_lab", lambda: blank)
    r = TestClient(srv.app).post("/api/query", json={"text": "x", "strategy": "manual_classifier"})
    assert "event: error" in r.text and "Exercise 2" in r.text
```

- [ ] **Step 2: Run → FAIL**, then implement `server.py`:

```python
"""Routing Client backend. WINDOW, NOT WIZARD: this file contains zero routing
logic — it reloads the learner's routing_lab.py and renders what it returns."""
import importlib, json, os, socket, sys, pathlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
app = FastAPI()

def _load_lab():
    import routing_lab
    return importlib.reload(routing_lab)

def _sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

def _gateway_alive():
    try:
        with socket.create_connection(("127.0.0.1", 4000), timeout=0.3): return True
    except OSError:
        return False

@app.get("/api/status")
def status():
    lab = _load_lab()
    import switchyard_shim as shim
    return {"unlocks": lab.probe_unlocks(lab), "gateway_alive": _gateway_alive(),
            "key_present": bool(os.environ.get("NVIDIA_API_KEY")),
            "sdk_available": shim.SDK_AVAILABLE}

@app.post("/api/query")
def query(body: dict):
    text, strategy = body["text"], body["strategy"]
    def gen():
        lab = _load_lab()
        bill = lab.RunningBill()
        try:
            pool = None
            if strategy in ("strong_only", "efficient_only", "manual_classifier", "switchyard_stage"):
                pool = lab.build_model_pool()
            if strategy == "strong_only":
                resp, receipt = lab.bill_call(lab.STRONG_MODEL, pool["strong"], text, bill)
            elif strategy == "efficient_only":
                resp, receipt = lab.bill_call(lab.EFFICIENT_MODEL, pool["efficient"], text, bill)
            elif strategy == "manual_classifier":
                resp, receipt = lab.route_call(text, pool, bill)
            elif strategy == "switchyard_stage":
                resp, receipt = lab.switchyard_call(text, pool, bill)
            elif strategy == "mock_demo":
                import switchyard_shim as shim
                resp, receipt = lab.switchyard_call(text, pool or lab.build_model_pool(),
                                                    bill, router=shim.MockRouter())
            elif strategy == "gateway":
                answer_text, receipt = lab.gateway_call(text, bill)
                resp = type("R", (), {"content": answer_text})
            else:
                raise ValueError(f"unknown strategy {strategy}")
            lane = "capable" if receipt["model"] == lab.STRONG_MODEL else "efficient"
            yield _sse("route_decision", {"lane": lane, "model": receipt["model"], "why": receipt["why"]})
            receipt["counterfactual_saved"] = receipt["counterfactual_cost"] - receipt["cost"]
            yield _sse("receipt", receipt)
            yield _sse("answer", {"text": resp.content})
        except NotImplementedError as e:
            yield _sse("error", {"message": f"Locked: {e} — fill that TODO in routing_lab.py and retry."})
        except Exception as e:
            yield _sse("error", {"message": f"{type(e).__name__}: {e}"})
    return StreamingResponse(gen(), media_type="text/event-stream")

@app.post("/api/race")
def race(body: dict):
    def gen():
        lab = _load_lab()
        results = {}
        try:
            for strategy in body["strategies"]:
                results[strategy] = lab.run_suite(strategy, lab.RunningBill())
                verdict = lab.routing_verdict(results)
                yield _sse("race_row", next(r for r in verdict["rows"] if r["strategy"] == strategy))
            yield _sse("race_receipt", {"receipt": lab.routing_verdict(results)["receipt"]})
        except NotImplementedError as e:
            yield _sse("error", {"message": f"Locked: {e}"})
    return StreamingResponse(gen(), media_type="text/event-stream")

app.mount("/", StaticFiles(directory=HERE / "static", html=True), name="static")
```

And `start_client.sh`:

```bash
#!/bin/bash
# Routing Client tile entry point. Usage: start_client.sh $PORT
set -euo pipefail
cd "$(dirname "$0")"
pip show fastapi uvicorn >/dev/null 2>&1 || pip install --quiet fastapi uvicorn
exec python3 -m uvicorn server:app --host 127.0.0.1 --port "${1:?port required}"
```

- [ ] **Step 3: Run → PASS** (`python3 -m pytest tests/test_client_logic.py -v`; add `pip install fastapi uvicorn httpx` if missing)
- [ ] **Step 4: Commit** — `git commit -am "feat(module-8): routing client backend — status probe, SSE query/race, reload-per-request"`

### Task 11: Client frontend — dx-themed yard UI

**Files:**
- Create: `code/8-agent-routing/routing_client/static/index.html`
- Create: `code/8-agent-routing/routing_client/static/client.css`
- Create: `code/8-agent-routing/routing_client/static/client.js`
- Create: `code/8-agent-routing/routing_client/static/yard.svg`

**Interfaces:**
- Consumes: Task 10's API exactly (`/api/status`, `/api/query` SSE events `route_decision|receipt|answer|error`, `/api/race` events `race_row|race_receipt`).

- [ ] **Step 1: `index.html`** — structure (link `client.css`; copy the dark background/typography variables OUT of `.devx/_static/css/devx-theme.css` into `client.css` rather than path-linking across dirs — the client must work standalone):

```html
<!doctype html><html><head><meta charset="utf-8"><title>Routing Client</title>
<link rel="stylesheet" href="client.css"></head><body>
<header>
  <h1>ROUTING CLIENT</h1>
  <div id="strategies"><!-- chips injected by client.js from /api/status --></div>
  <div id="meters">
    <span class="meter">session <b id="bill">$0.0000</b></span>
    <span class="meter save">saved vs frontier-only <b id="saved">$0.0000 (0%)</b></span>
    <span class="meter" id="online">systems online: 0/5</span>
  </div>
</header>
<main>
  <section id="yard-wrap"><object id="yard" data="yard.svg" type="image/svg+xml"></object></section>
  <aside id="receipts"><h2>RECEIPTS</h2><ol id="receipt-log"></ol></aside>
</main>
<footer>
  <div id="chips">
    <button class="ex commodity">Convert 2 hours to minutes.</button>
    <button class="ex commodity">Extract the email from: "mail ada@example.com now".</button>
    <button class="ex frontier">Plan a 5-step LLM migration with an eval gate.</button>
    <button class="ex frontier">A ships 3 features/sprint, 2 reviews each at 45min — review-hours per 4-sprint quarter?</button>
  </div>
  <form id="ask"><input id="q" placeholder="Ask anything — watch it route"><button>Send</button></form>
  <details id="race"><summary>🏁 Race mode (Exercise 5)</summary>
    <button id="run-race" disabled>Run the 12-task suite</button>
    <table id="race-table"><thead><tr><th>strategy</th><th>accuracy</th><th>cost</th><th>frontier %</th><th>tax %</th></tr></thead><tbody></tbody></table>
    <p id="race-receipt"></p>
  </details>
</footer>
<script src="client.js"></script></body></html>
```

- [ ] **Step 2: `yard.svg`** — hand-authored dark scene, functional skeleton (art polish later; ids are the contract with client.js):

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 320" font-family="monospace">
  <rect width="900" height="320" fill="#0e1116"/>
  <g id="dispatcher"><rect x="330" y="130" width="140" height="60" rx="8" fill="#1a2230" stroke="#76b900"/>
    <text x="400" y="155" fill="#e6edf3" text-anchor="middle" font-size="13">DISPATCHER</text>
    <text id="dispatcher-why" x="400" y="175" fill="#8b98a9" text-anchor="middle" font-size="10"></text></g>
  <path id="rail-in" d="M40 160 H330" stroke="#3a4657" stroke-width="4"/>
  <path id="rail-efficient" d="M470 160 C560 160 560 80 650 80 H860" stroke="#3a4657" stroke-width="4" fill="none"/>
  <path id="rail-capable"  d="M470 160 C560 160 560 240 650 240 H860" stroke="#3a4657" stroke-width="4" fill="none"/>
  <g id="loco-efficient"><rect x="700" y="55" width="160" height="50" rx="8" fill="#12281a" stroke="#76b900"/>
    <text x="780" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">LIGHTNING 30B</text>
    <text x="780" y="92" fill="#76b900" text-anchor="middle" font-size="10">efficient · open</text></g>
  <g id="loco-capable"><rect x="700" y="215" width="160" height="50" rx="8" fill="#2b1a12" stroke="#e07a2f"/>
    <text x="780" y="235" fill="#e6edf3" text-anchor="middle" font-size="11">SUPER 120B</text>
    <text x="780" y="252" fill="#e07a2f" text-anchor="middle" font-size="10">strong · frontier stand-in</text></g>
  <circle id="card" r="9" fill="#76b900" opacity="0"/>
</svg>
```

- [ ] **Step 3: `client.js`** — the full behavior (~120 lines): on load and every 3s `fetch('/api/status')` → render strategy chips (locked chips get `disabled` + `title="unlocks in Exercise N"`; mapping: strong_only/efficient_only→ex1, manual_classifier→ex2, switchyard_stage→ex3, gateway→`gateway_alive`, mock_demo→always on), set `systems online: N/5` (count ex1,ex2,ex3,gateway_alive,ex5), enable `#run-race` when ex5. On submit/chip-click: `fetch('/api/query', {method:'POST', body: JSON.stringify({text, strategy: selected})})`, parse the SSE stream manually (read `response.body` with a TextDecoder, split on `\n\n`, dispatch by `event:` line). Handlers: `route_decision` → animate `#card` along `#rail-in` then the chosen rail (SVG `getPointAtLength` sampling, ~900ms), set `#dispatcher-why`; `receipt` → prepend `<li>` to `#receipt-log` (`model · why · $cost · Xs · would-have-been $counterfactual_cost`), increment `#bill` and `#saved` running totals; `answer` → append the reply bubble under the form; `error` → toast the message. Race: same SSE pattern into `#race-table` rows + `#race-receipt`. No frameworks, no build step.

- [ ] **Step 4: `client.css`** — dark theme lifted from devx (`#0e1116` bg, `#76b900` accent, monospace headers), locked-chip style (`opacity:.35; cursor:not-allowed`), receipt list, toast. ~80 lines.

- [ ] **Step 5: Manual verify (both states)** — `bash routing_client/start_client.sh 8899` from `code/8-agent-routing`, open via JupyterLab proxy or `curl -s localhost:8899 | head`; check `/api/status` returns the BLANK module's all-false unlocks (chips greyed, `0/5`); then temporarily point `_load_lab` at answers (env var `ROUTING_LAB_MODULE=routing_lab.answers` supported in `_load_lab`: if set, load that path instead — add this ~3-line affordance to server.py; it's also how demos run) and confirm chips enable and a live query animates the yard and appends a receipt. Kill server.

- [ ] **Step 6: Commit** — `git commit -am "feat(module-8): routing client frontend — dx-dark yard animation, chips, receipts, race table"`

### Task 12: Client completion — gateway mode, GPU badge, launcher tile

**Files:**
- Modify: `code/8-agent-routing/routing_client/server.py` (GPU poll + gateway attribution note)
- Modify: `code/8-agent-routing/routing_client/static/{index.html,client.js,yard.svg}` (GPU locomotive)
- Modify: `jp_app_launcher.yaml`

- [ ] **Step 1:** Add `GET /api/gpu` to server.py: run `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader` via `subprocess` (returns `{"available": false}` on any failure); client.js polls it every 2s ONLY while gateway mode is on, showing/hiding a third locomotive group `#loco-gpu` (`YOUR GPU · nano 30B local`, badge text = `NN% util`). Add `#rail-gpu` path to yard.svg mirroring the efficient rail.
- [ ] **Step 2:** Gateway attribution: per Task 1's notes — if the response `model` field names the upstream target, `gateway_call` already attributes correctly (nothing to do); if NOT, set receipt `model` to `GATEWAY_ROUTE_ID` and `why` to `"gateway (upstream hidden — see api-notes)"`, and the yard parks the card AT the dispatcher labeled "external yard". Implement whichever branch is true; delete the other.
- [ ] **Step 3:** Register the tile — append to `jp_app_launcher.yaml` after the "NemoClaw Client" block, exactly:

```yaml
- title: "Routing Client"
  source: http://localhost:$PORT/
  cwd: /project/code/8-agent-routing
  type: local-server
  args:
    - bash
    - -c
    - bash routing_client/start_client.sh $PORT
  icon: /project/.devx/_static/img/chatbot.svg
  catalog: NVIDIA DevX Learning Path
```

- [ ] **Step 4:** Verify: `python3 -c "import yaml,sys; yaml.safe_load(open('jp_app_launcher.yaml'))" && echo OK`; relaunch client locally once more end-to-end (status → query → receipt).
- [ ] **Step 5:** Commit — `git commit -am "feat(module-8): gpu locomotive badge, gateway attribution, Routing Client launcher tile"`

---

## Phase 3 — Doc pages (`.devx/8-agent-routing/`)

**Shared page conventions for Tasks 13–17** (treat as steps of each task): copy the writing voice, widget usage, and `<!-- fold:break -->` cadence from the same-position M7 page; every expected-output number gets `<!-- CALIBRATE -->`; verify each page by `cd .devx/8-agent-routing && python3 -m http.server 8123` and loading it in a browser (hero renders, folds unfold, quiz feedback fires, no console errors); robots images: copy 2–3 suitable PNGs from other modules' `_static/robots/` (e.g. `relocate.png`, `finish.png`) — bespoke art deferred.

### Task 13: Module shell + secrets page + docs tile

**Files:**
- Create: `.devx/8-agent-routing/{index.html,_sidebar.md,secrets.md,theme/,_static/,img/}`
- Modify: `jp_app_launcher.yaml`

- [ ] **Step 1:** `cp .devx/7-agent-harnesses/index.html .devx/8-agent-routing/ && cp -r .devx/7-agent-harnesses/theme .devx/8-agent-routing/ && mkdir -p .devx/8-agent-routing/{_static/diagrams,img}`; copy `_static` shell items M7 carries (inspect first: `ls .devx/7-agent-harnesses/_static`) except module-specific images. Edit `index.html`: `<title>` → "Agent Routing", any module-name strings → module 8 equivalents (grep for `harness` in the copied file).
- [ ] **Step 2:** Write `_sidebar.md` — exactly the six lines from spec §3 (`Setting up Secrets` → `Wrapping Up`, files `secrets.md, intro_agent_routing.md, routing_decisions.md, meet_switchyard.md, routing_lab.md, evaluating_routing.md`).
- [ ] **Step 3:** Write `secrets.md` (~280 words) — mirror `.devx/7-agent-harnesses/secrets.md` structure (open it; reuse its verification curl), add the one module-specific dx-aside: *export `NVIDIA_API_KEY` in the same terminal you run `switchyard-server` from — the gateway reads it via `api_key_env`, and a missing env var here is this module's #1 predictable failure.*
- [ ] **Step 4:** Add the docs tile to `jp_app_launcher.yaml` — duplicate the "7. Agent Harnesses" block, title `"8. Agent Routing"`, cwd `/project/.devx/8-agent-routing`. Validate YAML again.
- [ ] **Step 5:** Serve + click through (shell loads, sidebar shows 6 entries, secrets page renders). Commit — `git commit -am "docs(module-8): module shell, sidebar, secrets page, docs launcher tile"`

### Task 14: Intro page + diagram 1

**Files:**
- Create: `.devx/8-agent-routing/intro_agent_routing.md`
- Create: `.devx/8-agent-routing/_static/diagrams/one_model_vs_routed.svg`

- [ ] **Step 1:** Write the page implementing every bullet of spec §3 "intro_agent_routing.md" (read that section first; it is the content contract). Required literal elements — copy exactly:
  - Hero: `<div class="dx-hero" data-eyebrow="MODULE 08 / 01 - THE TOKENOMICS PROBLEM" data-title="Your agent runs on tokens. Someone pays for every one." data-sub="Seven modules, seven agents, one hardwired brain — paying frontier prices for commodity work." data-meta="TAKEAWAY::use both, efficiently|NEXT::how routers decide"></div>`
  - The M7 continuity line verbatim: *"Module 7 taught you every token has a **cost** (the context tax). Module 8 teaches you every token has a **price** — and the price depends on who generates it."*
  - dx-island "TOKENOMICS, CONCRETELY" with the benchmark math ($11.45 vs $3.00/task; ~$4.2M vs ~$1.1M/yr at 1,000 tasks/day; 86.0%→80.0% giveback; cite the LangChain post).
  - The frontier-vs-open section with the pivot sentence bolded: **the debate silently assumes every call is equally hard — and your own agent transcripts prove it isn't** — plus the Team Frontier parenthetical *(the role Nemotron Super 120B will play in your lab — see the "stand-in" aside in Exercise 1)*.
  - dx-quiz: "Module 1 also had 'routing.' What did it decide?" — options `which model`, `which tool or step` (data-right, fb: "M1 routing = control flow. M8 completes the component: which brain."), `which user`, `which GPU`.
  - dx-bet: frontier-call-fraction question, options 75/40/20/**7%**.
  - `<img src="_static/diagrams/one_model_vs_routed.svg">` placement mid-page.
- [ ] **Step 2:** Author `one_model_vs_routed.svg` — dark (#0e1116 bg), two panels: left "TODAY" (agent loop node, 6 arrows all → one `120B · $$$` box), right "ROUTED" (same loop → dispatcher diamond → thick arrow to `30B · $` labeled `~93%`, thin arrow to `120B · $$$` labeled `~7%`). Text ≥11px, `#76b900` accent, `<!-- CALIBRATE: percentages -->` comment.
- [ ] **Step 3:** Serve, verify (quiz + bet interactive, SVG legible on dark). Commit — `git commit -am "docs(module-8): tokenomics intro page + one-model-vs-routed diagram"`

### Task 15: Routing-decisions page + diagram 2

**Files:**
- Create: `.devx/8-agent-routing/routing_decisions.md`
- Create: `.devx/8-agent-routing/_static/diagrams/routing_signals.svg`

- [ ] **Step 1:** Write the page from spec §3 "routing_decisions.md" — all five algorithm families in order (static / content-based / signal-based / escalation / learned), each with its config name in backticks (`random`, `llm_classifier` capability, `stage_router`, `llm_classifier` escalation + `confirmations`, prefill); the **router-tax** concept introduced inside the content-based section with the ~700ms / 21%-of-spend numbers cited; the M6 contrast section (policy vs performance routing — who MAY vs who SHOULD answer; explicitly note M8's classifier IS content classification, M6's Privacy Router is NOT); the specialists section (Boomi 59%→5× fine-tuned, M4 callback, "open models make owning a specialist possible"); the M4 learned-router callback ("train when tuning-free plateaus").
- [ ] **Step 2:** Required dx-quiz verbatim: "Your agent does long tool-heavy sessions and you can't afford an extra LLM call per turn — which algorithm?" — options `llm_classifier` (fb: "Reads content well, but that's an extra LLM call every turn."), `stage_router` (data-right, fb: "Routes on tool signals you already produce — no classifier call, no tax."), `random` (fb: "A baseline, not a decision."), `passthrough` (fb: "That's not routing at all.").
- [ ] **Step 3:** Author `routing_signals.svg` — horizontal axis "evidence used → cost of deciding": four family boxes placed left-to-right (`random`: none/free → `stage_router`: signals/free → `llm_classifier`: content/one small call → `prefill (learned)`: residual stream/training run).
- [ ] **Step 4:** Serve, verify, commit — `git commit -am "docs(module-8): how-routers-decide taxonomy page + signals diagram"`

### Task 16: Meet-Switchyard page + diagram 3

**Files:**
- Create: `.devx/8-agent-routing/meet_switchyard.md`
- Create: `.devx/8-agent-routing/_static/diagrams/switchyard_architecture.svg`

- [ ] **Step 1:** Write from spec §3 "meet_switchyard.md": libsy / server / launcher; the three-noun `routes.toml` teardown — embed `routes.toml.answers`' hosted config verbatim with per-line annotations; wire-format island ("the gateway is also an adapter": OpenAI Chat ⇄ Anthropic Messages ⇄ Responses; NIM/vLLM/Ollama backends); ecosystem paragraph (LangChain middleware, LiteLLM, Kong, Cognition, **Nous Hermes — the harness from your M7 lab — routes with it**); the **required version-stamp dx-aside** with the REAL pin from Task 1: *"This module was built and tested against Switchyard vX.Y, pinned in the lab… the concepts on this page are stable, but exact imports and flags may differ in the latest release."*; the portfolio-governability line (rebalancing = `routes.toml` edit + eval run, not a migration); the optional dx-peek: adding an Anthropic client (`format = "anthropic_messages"`, `api_key_env = "ANTHROPIC_API_KEY"`, swap `targets.strong`) — labeled optional, own key required.
- [ ] **Step 2:** dx-bet verbatim from spec: Cognition FrontierCode cost question → ~28% cheaper at 50.6% accuracy reveal, cited.
- [ ] **Step 3:** Author `switchyard_architecture.svg` — left-to-right: `your agent` → `route "switchyard" (algorithm)` → `targets weak/strong` → `llm_clients` → three provider boxes (`build.nvidia.com`, `local NIM`, `any OpenAI-compatible`); two bracket overlays labeled `in-process (libsy)` and `gateway (switchyard-server :4000)`.
- [ ] **Step 4:** Serve, verify, commit — `git commit -am "docs(module-8): meet-switchyard page, architecture diagram, version-stamp aside"`

### Task 17: Lab page + wrap-up page

**Files:**
- Create: `.devx/8-agent-routing/routing_lab.md`
- Create: `.devx/8-agent-routing/evaluating_routing.md`

- [ ] **Step 1:** Write `routing_lab.md` following `.devx/7-agent-harnesses/harness_lab.md`'s exact mechanics (hero with `data-meta="TIME::95 min|EXERCISES::5+client|FORMAT::.py (notebook alt)|ANSWERS::included"`; the two-track intro paragraph naming `routing_lab.py`/`routing_lab.ipynb` with `openOrCreateFileInJupyterLab` buttons; `goToLineAndSelect` buttons per TODO). Structure per spec §4: **Ex0 "Open the yard"** (client tile screenshot placeholder `img/client_dormant.png` `<!-- CAPTURE at Task 20 -->`, dormant-state description, env-check note) → Ex1–Ex5 sections, each with: instruction prose (from spec §4 bullets), per-blank 🆘 `dx-peek is-solution` containing the answer code copied EXACTLY from `routing_lab.answers.py` plus its gotcha paragraph, an **Unlock it** beat (what lights up, per spec §4 "Client unlock" bullets), and a **Run it** CLI fallback (`cd code/8-agent-routing && python routing_lab.py --exercise N`). Include the REQUIRED Ex1 dx-aside "A stand-in for the frontier" verbatim from spec §4. Ex4 embeds the template-vs-answers TOML flow (`--dry-run` before serve; `curl :4000/v1/models`), the 4b NIM detour in a dx-peek (mirroring M2's runbook + "no Docker/GPU → 4a is the full exercise"), and the terminal buttons. Ex5 ends with the 🧾 receipt expected-output block `<!-- CALIBRATE -->`.
- [ ] **Step 2:** Write `evaluating_routing.md` from spec §3: exercises→production table (Ex1 meter→cost observability; Ex2→`llm_classifier` internals; Ex3→LangChain middleware/LiteLLM; Ex4→Kong/Devin Desktop/Hermes; Ex5→the 145-task benchmark method); the decision framework list verbatim (*No router → passthrough … learned router (and you know how to train)*); honest-limits paragraph (workload-specific, saturated benchmarks, judge spend, "a 6-point giveback is a *choice*"); **The portfolio answer** block + honest coda ("sometimes the right mix IS 100% frontier — the router and the suite let you *know*"); the bigger-picture NVIDIA paragraph; the **8-cell dx-bento** (copy M7's bento from `evaluating_harnesses.md`, make Module 8 the `is-wide` "YOU ARE HERE" cell, demote M7's cell to normal); congratulations block ("all eight modules"); resources list (Switchyard GitHub + the four doc links, both NVIDIA blogs, LangChain + Boomi posts, Lightning model card).
- [ ] **Step 3:** Serve, click through every fold/quiz/button on both pages. Commit — `git commit -am "docs(module-8): routing lab page (unlock arc) + wrapping-up page with 8-module bento"`

---

## Phase 4 — Journey integration

### Task 18: Backward edits — M7 wrap-up, README, build pins

**Files:**
- Modify: `.devx/7-agent-harnesses/evaluating_harnesses.md`
- Modify: `README.md`
- Modify: `postBuild.bash`, `requirements.txt`

- [ ] **Step 1: M7 wrap-up** — three edits: (a) in the bento, change the M7 cell to a normal cell (`<div class="dx-cell"><h4>MODULE 7</h4><span class="dx-big">The harness layer</span>Context tax + portable, verified skills</div>`) and append `<div class="dx-cell is-wide"><h4>MODULE 8 - UP NEXT</h4><span class="dx-big">Agent routing</span>The right model for every call - tokenomics + NeMo Switchyard</div>`; (b) replace the final congratulations blockquote with: `> **Module 7 complete!** Your agents have engines, cars, and a garage full of verified parts. One thing is still welded in place: every call uses the same engine. [Module 8](../8-agent-routing/index.html) hands your harness a switchyard — the right model for every call.`; (c) add to More Resources: `- 🛤️ [NeMo Switchyard](https://github.com/NVIDIA-NeMo/Switchyard) — route every call to the right model; the subject of Module 8`.
- [ ] **Step 2: README** — module list: add `* **Module 8 - Agent Routing**: Tame agent tokenomics with NVIDIA NeMo Switchyard — route every call to the right model (frontier or open), visualized live in the Routing Client.`; change "seven progressive modules" → "eight progressive modules"; update the skills sentence `module-1..7` → `module-1..8` (both Claude `/` and Codex `$` mentions); scan for other "seven" occurrences (`grep -n seven README.md`).
- [ ] **Step 3: Build pins** — append to `postBuild.bash`: `bash /project/code/8-agent-routing/scripts/install_switchyard.sh` (guarded: `|| echo "⚠️ switchyard install deferred — lab falls back to MockRouter"`); add `fastapi`, `uvicorn`, `sse-starlette` to `requirements.txt` IF absent (`grep -i fastapi requirements.txt` first); jupytext is dev-only — do NOT add.
- [ ] **Step 4:** Verify README renders (`grep -c "Module 8" README.md` ≥ 2), M7 page serves with the new bento. Commit — `git commit -am "docs(module-8): M7 handoff hook, README module list, build pins"`

### Task 19: Skills — module-8 tutor + workshop hub + Codex sync

**Files:**
- Create: `.claude/skills/module-8/SKILL.md`, `.claude/skills/module-8/references/{diagrams.md,nvidia-tech.md,quizzes.md}`
- Modify: `.claude/skills/workshop/references/{map.md,connections.md,glossary.md,progress.md}`
- Modify: `.claude/skills/workshop/SKILL.md` (arc: seven→eight; routing shorthand)
- Run: `.agents/sync-codex-skills.sh`

- [ ] **Step 1: `module-8/SKILL.md`** — mirror `module-7/SKILL.md`'s frontmatter shape (open it; match description style: trigger phrases like "/module-8 what is model routing?", "why route between models?", "my switchyard-server won't start", "the Routing Client shows everything locked", "explain escalation vs capability mode", "router tax", "gateway vs in-process"). Body sections, matching the module-1..7 template: Role (M8 tutor; guide-don't-solve), **Non-negotiables** (never complete exercises; NEVER open `routing_lab.answers.*`, `routes.toml.answers`; graduated hints only), Module summary (the six pages + 5-exercise/client arc), Key concepts in workshop framing (tokenomics; frontier-vs-open false binary; "use both, efficiently"; Super = frontier STAND-IN never literally frontier; router tax; policy-vs-performance routing — M6's Privacy Router is NOT content classification, M8's llm_classifier IS; window-not-wizard), Troubleshooting (key-missing banner; locked chips = unfilled TODOs → point to `probe_unlocks`; SDK ImportError → `scripts/install_switchyard.sh`, MockRouter fallback is expected; gateway `--dry-run` first; port 4000 in use; Ex4b needs Docker+GPU else skip), and the **Environment & hardware block** (main path CPU-only hosted; Ex4b optional GPU/Docker; sandbox = hosted-only + mock/dry-run path).
- [ ] **Step 2: references/** — `nvidia-tech.md`: Switchyard (libsy/server/launcher, algorithms table with config names, pins location, api-notes pointer), Nemotron 3.5 Lightning, NIM, links (GitHub + 4 docs pages + 2 blogs). `diagrams.md`: describe the three SVGs + yard.svg so the tutor can reference them in words. `quizzes.md`: 8 Q&A with answers + misconception notes — the 2 page quizzes + 2 bets (with their feedback lines) + 4 new (e.g. "Why does the escalation router never de-escalate mid-task?", "Your routed accuracy dropped 6 points — is the router broken?", "Where does the ONLY SDK import live and why?", "What's the difference between M6's Privacy Router and M8's llm_classifier?").
- [ ] **Step 3: Hub updates** — `map.md`: append the Module 8 entry in the established format (Build: routed lab + Routing Client · Concepts: tokenomics, routing taxonomy, Switchyard, router tax, portfolio · Code: `code/8-agent-routing/` files · Prereq: M1+M7 concepts; M2 NIM for Ex4b · Time: 2–3h · Hardware: none for main path, GPU optional Ex4b) and update the routing-shorthand line to include `model routing/switchyard/tokenomics/cost → M8`. `connections.md`: add the seven M8 callbacks (spec §7 table, one line each). `glossary.md`: add tokenomics, model portfolio/mix, route/target/llm_client, capability vs escalation mode, session affinity, router tax, Pareto frontier. `progress.md`: add the M8 checkpoints (client 0/5→5/5 as the visible progress signal). `workshop/SKILL.md`: "seven-module arc" → "eight-module arc" (grep for `seven`).
- [ ] **Step 4:** Run `bash .agents/sync-codex-skills.sh`; verify `.agents/skills/module-8/` appears.
- [ ] **Step 5:** Commit — `git commit -am "feat(module-8): tutor skill + references, workshop hub integration, codex sync"`

---

## Phase 5 — Calibration & QA (requires the Brev A100 target)

### Task 20: End-to-end calibration pass

**Files:**
- Modify: every file containing `<!-- CALIBRATE -->` or `# CALIBRATE`; `.devx/8-agent-routing/img/` (screenshots)

- [ ] **Step 1:** On the Brev A100 image (not this GB10 box): fresh-ish run — `bash scripts/install_switchyard.sh && bash scripts/smoke_switchyard.sh`, then `python3 routing_lab.answers.py --exercise N` for N=1..5 (gateway up for 4). Record every printed number.
- [ ] **Step 2:** Replace ALL calibration placeholders: `grep -rn "CALIBRATE" code/8-agent-routing .devx/8-agent-routing` and update each (Ex1 scoreboard, Ex2 comparison, Ex5 receipt, intro/diagram percentages, PRICING source note). Re-run the affected `--exercise` commands and confirm the docs' expected output matches reality verbatim. If the efficient model passes 12/12 (saturation — spec's honesty caveat), harden 2–3 frontier tasks in `routing_tasks.jsonl` until it drops ≥2, then recalibrate.
- [ ] **Step 3:** Ex4b live check: `bash scripts/serve_local_nim.sh` on the A100 (Nano NIM), rerun gateway exercise with the local-NIM variant uncommented; attempt the Lightning NIM tag and record SM80 verdict in `switchyard-api-notes.md`.
- [ ] **Step 4:** Client screenshots for the lab page: dormant (`img/client_dormant.png`), routed query mid-animation (`img/client_routed.png`), race final (`img/client_race.png`) — capture in-browser, reference from `routing_lab.md`, delete the CAPTURE comments.
- [ ] **Step 5:** Full QA sweep: launch JupyterLab, click both new tiles (docs + client), work Ex1 as a learner would (fill blank from the 🆘, watch unlock), run `python3 -m pytest code/8-agent-routing/tests -v` (all green), `python3 -c "import yaml; yaml.safe_load(open('jp_app_launcher.yaml'))"`.
- [ ] **Step 6:** Sandbox notes (do NOT attempt live given the control-plane state): append to `docs/specs/switchyard-api-notes.md` a `## Sandbox TODO` — egress adds (PyPI already allowed; confirm `integrate.api.nvidia.com`; loopback :4000), the extra forwarded port for the client, and pointer to update `setup-workshop-nemoclaw(-operator)` skills in a follow-up.
- [ ] **Step 7:** Commit — `git commit -am "feat(module-8): A100 calibration — real numbers, screenshots, NIM verification, QA"`

---

## Self-review record

- **Spec coverage:** §0 grounding→T1; §2 identity→T2/T13; §3 pages→T13–T17 (secrets/intro/decisions/switchyard/lab/wrap); §4 exercises+unlocks→T3–T9 (+client beats in T17); §4c client→T10–T12; §5 tree→file structure + tasks; §6 matrix→fallbacks embedded (mock router T5, CLI-fallback T8, no-Docker guard T6, sandbox notes T20); §7 integration→T18–T19 (launcher in T12/T13); §8 risks→T1 (pins/API/model ids/attribution), T20 (calibration, NIM/SM80, sandbox); §8b churn→T1 (pins), T5 (shim+mock), T8 (README runbook), T16 (version-stamp); §9 settled decisions honored throughout.
- **Placeholder scan:** intentional deferred items are explicitly mechanized (`<!-- CALIBRATE -->` → Task 20; `<ADJUST per api-notes>` → Task 5 consumes Task 1's deliverable) — no unowned TBDs.
- **Type consistency:** receipt keys, TaskResult keys, strategy strings, probe keys (`ex1,ex2,ex3,ex5` + `gateway_alive`), SSE event names, and `routing_verdict` row keys are each defined once and reused verbatim across T3/T7/T8/T10/T11/T17.
