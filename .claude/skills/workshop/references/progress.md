# Workshop Progress & State Checks — tutor reference

Read-only signals to answer "what have I finished / what's broken / am I ready for the next
module?" **Every check here is non-destructive** (grep / ls / curl / status). **Never
auto-fix, auto-fill a blank, run training, or change state** — inspect, report, classify,
then guide. Ask the learner before running checks. Run from the repo root.

Classify each module as **not-started** (blanks untouched) / **in-progress** (some blanks
filled, not running) / **done** (blanks filled + runs) / **broken** (filled but erroring →
that's environment, route to the module's `troubleshooting.md`).

## Setup (all modules)
- API key present: `grep -q '^NVIDIA_API_KEY=nvapi-' secrets.env && echo set || echo MISSING`
  (M1/M2/M3/M5 also want `TAVILY_API_KEY`). `secrets.env` is gitignored — absent on a fresh clone.
- Environment up: see the **setup-workshop** skill (is DevX-Lab reachable / the nvwb app running).

## Per-module signals
### Module 1
- Remaining blanks: `grep -RnE '"\s*\.\.\.\s*"|\(\s*\.\.\.\s*\)' code/1-build-an-agent/*.ipynb`
  (the `" ... "` / `( ... )` placeholders). None → blanks filled.
- "Done" = both notebooks run top-to-bottom without error (no persistent build artifact).

### Module 2
- Remaining blanks: `grep -nE '=\s*\.\.\.|\.\.\.\)' code/2-agentic-rag/rag_agent.py`. `AGENT = ...`
  still present → not finished. (Note the three-stage `AGENT` rebuild — which tools are wired tells you how far they are.)
- Server running: `curl -s http://localhost:2024/ok` (the `langgraph dev` API; needed by the Simple Agents Client).

### Module 3
- **Prereq:** M2 `rag_agent.py` complete (no `...`); the M1 agent importable. If not, the workshop sanctions pasting the M2 answer key.
- Framework blank: `grep -n 'TODO: ...' code/3-agent-evaluation/evaluation_framework.py` present → `FAITHFULNESS_PROMPT` unfilled.
- Notebook TODOs: `grep -n 'TODO: load in the dataset as json' code/3-agent-evaluation/evaluate_*_agent.ipynb`. Eval outputs land in `code/3-agent-evaluation/artifacts/`.

### Module 4
- Data ready: `ls code/4-agent-customization/data/langgraph_cli/train.jsonl` (SDG output or the provided 225-example set).
- Reward server up: `curl -s http://localhost:8000/` (NeMo Gym `/verify`) — must be running before GRPO.
- Training done: `ls code/4-agent-customization/outputs/grpo_langgraph_cli/merged_model/` → exists = trained.
- GPU: `nvidia-smi` (capable GPU? A100/H100 ideal; GB10 slow). Notebook TODOs marked `# TODO: Exercise`.

### Module 5
- Remaining blanks: `grep -nE '=\s*\.\.\.|\.\.\.\s' code/5-deep-agents/deep_agent.py` (5 exercises; `agent = ...` last).
- Demo backend up: `curl -s http://localhost:8000/` (`uvicorn server:app` in `demo/backend`). Docker: `docker ps`.
- Dry-run success prints "🎉 Your deep agent is working!".

### Module 6
- Control plane: `python3 code/6-agent-safety/scripts/diagnose-nemoclaw.py` — reports CLI/gateway/sandbox state (it can legitimately be down; see the module's troubleshooting).
- Code sidekicks: `grep -n '# TODO: Exercise' code/6-agent-safety/agent_safety.py` lists the four (`classify_sensitivity`/`run_redteam_probes`/`evaluate_safety`/`run_safety_suite`); check whether each body is still a stub.
- The Python eval runs against the **mock agent + `test_data/` fixtures even if the live stack is down** — so concept/code progress isn't blocked by a broken control plane.
- Docker: `docker ps`; kernel: `uname -r` (≥ 5.13 for Landlock).

## Readiness gates (for "am I ready for module N?")
- **→ M3:** M1 + M2 agents built (or paste the M2 answer key — sanctioned).
- **→ M4:** a capable NVIDIA GPU (else do SDG + concepts only; the training run needs the GPU).
- **→ M5:** Docker (for sandbox mode).
- **→ M6:** Docker + Linux kernel ≥ 5.13 for the live hardening (the eval code works without).

## Reminder
Read-only only. If a blank is unfilled → it's an *exercise* (guide, don't fill it). If it's
filled but erroring → it's an *environment* problem (diagnose via the module's
`troubleshooting.md`). Report what you find, classify, and suggest the next step.
