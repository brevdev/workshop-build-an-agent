# Workshop Progress & State Checks — tutor reference

Read-only signals to answer "what have I finished / what's broken / am I ready for the next
module?" **Every check here is non-destructive** (grep / ls / curl / status). **Never
auto-fix, auto-fill a blank, run training, or change state** — inspect, report, classify,
then guide. Ask the learner before running checks. Run from the repo root.

Classify each module as **not-started** (blanks untouched) / **in-progress** (some blanks
filled, not running) / **done** (blanks filled + runs) / **needs diagnosis** (filled but erroring: inspect code, service and environment failures).
TODO comments locate exercises; inspect their bodies before deciding whether blanks remain.

## Setup (all modules)
- **Workshop Utilities → Workshop Health** shows key presence, endpoint checks and service status without printing keys. `secrets.env` is gitignored and absent on a fresh clone.
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
- Framework blank: inspect `FAITHFULNESS_PROMPT` in `code/3-agent-evaluation/evaluation_framework.py` for its rubric blank.
- Notebook TODOs: `grep -n 'TODO:' code/3-agent-evaluation/evaluate_*_agent.ipynb`. Outputs are under `code/3-agent-evaluation/runs/`; inspect measurement coverage, not just file existence.

### Module 4
- Data ready: `ls code/4-agent-customization/data/langgraph_cli/train.jsonl` (213 reviewed training examples plus 25 validation examples; generated data uses a separate folder).
- Reward server up: `curl -s http://localhost:8001/health` (NeMo Gym `/verify` on the same port) — must be running before GRPO.
- Training: inspect `code/4-agent-customization/outputs/grpo_langgraph_cli/held_out_comparison.json` and test the merged export in a fresh process. A directory alone does not establish successful training or quality improvement.
- GPU: `nvidia-smi` (check capability and free memory; GB10 shares memory with the system). Notebook TODOs marked `# TODO: Exercise`.

### Module 5
- Remaining blanks: `grep -nE '=\s*\.\.\.|\.\.\.\s' code/5-deep-agents/deep_agent.py` (5 exercises; `agent = ...` last).
- Demo backend up: `curl -s http://localhost:8000/api/health` (`uvicorn server:app` in `demo/backend`). Docker: `docker ps`.
- Dry-run success prints "🎉 Your deep agent is working!".

### Module 6
- Control plane: `python3 code/6-agent-safety/scripts/diagnose-nemoclaw.py` — reports CLI/gateway/sandbox state (it can legitimately be down; see the module's troubleshooting).
- Code sidekicks: `grep -n '# TODO: Exercise' code/6-agent-safety/agent_safety.py` lists the four (`classify_sensitivity`/`run_redteam_probes`/`evaluate_safety`/`run_safety_suite`); check whether each body is still a stub.
- The Python eval runs against the **mock agent + `test_data/` fixtures even if the live stack is down** — so concept/code progress isn't blocked by a broken control plane.
- Docker: `docker ps`; kernel: check Landlock support with the Module 6 setup checks; version alone is insufficient.

### Module 7
- Remaining blanks: `grep -nE 'NotImplementedError\("Complete Exercise' code/7-agent-harnesses/harness_lab.py` — any hits → that exercise's blank is still a stub (`build_bare_agent` 1a/1b, `harness_overhead` 2a, `load_skills_lazily` 2b, `self_evolve_skill` 5).
- Authored skill (Ex3): `ls code/7-agent-harnesses/skills/dataset-profiler/SKILL.md`. Verified skill (Ex4): `ls code/7-agent-harnesses/skills/accelerated-computing-cudf/SKILL.md` (run `scripts/install_nvidia_skill.sh` first).
- GPU (Ex4 comparison only): `nvidia-smi` — absent is fine (the exercise falls back to pandas + prints a skip message). "Done" = `python harness_lab.py --exercise N` runs for each completed exercise.

## Readiness gates (for "am I ready for module N?")
- **→ M3:** M1 + M2 agents built (or paste the M2 answer key — sanctioned).
- **→ M4:** a capable NVIDIA GPU (else do SDG + concepts only; the training run needs the GPU).
- **→ M5:** Docker (for sandbox mode).
- **→ M6:** Docker + Landlock enabled for live hardening (the eval code works without).
- **→ M7:** M1–M6 concepts (the capstone — it names the harness layer used throughout). NVIDIA key only; Exercise 4's cuDF comparison needs a GPU (skips cleanly without). No successor module.

## Reminder
Read-only only. If a blank is unfilled → it's an *exercise* (guide, don't fill it). If it is filled but errors, distinguish learner-code, service and environment failures using the module's `troubleshooting.md`. Report what you find, classify, and suggest the next step.
