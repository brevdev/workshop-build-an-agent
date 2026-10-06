# Workshop Progress & State Checks — tutor reference

Read-only signals to answer "what have I finished / what's broken / am I ready for the next
module?" **Every check here is non-destructive** (`blanks.py` / ls / curl / status). **Never
auto-fix, auto-fill a blank, run training, or change state** — inspect, report, classify,
then guide. Ask the learner before running checks. Run from the repo root.

Classify each module as **not-started** (blanks untouched) / **in-progress** (some blanks
filled, not running) / **done** (blanks filled + runs) / **needs diagnosis** (filled but erroring: inspect code, service and environment failures).

## Finding unfilled blanks (all modules)
`python code/workshop_support/blanks.py <N>` (module number 1–7; or pass file paths instead;
no argument checks every module). It only reads files, never runs them. Output, per exercise file:
- `✓ Module N: <path>: no blanks left`, or
- `• Module N: <path>: K blank(s) left`, then one line per blank: `line L: <text>` for `.py`
  files, `code cell C, line L: <text>` for notebooks (C counts **code cells only**, from 1;
  L is the line inside that cell — the `cell N` numbers in `exercises.md` count all cells from 0).

Exit status: 0 = no blanks; 1 = blanks remain (or a listed file is missing); 2 = bad module number.
It recognizes `...` (including `{...}` in f-strings), a `" ... "` string, a `TODO: ...` line in a
prompt template, and `raise NotImplementedError("Complete Exercise ...")`. Counts are lines, not
placeholders. A blank means *exercise* (guide); never fill one. Per-module gaps are noted below.

## Setup (all modules)
- **Workshop Utilities → Workshop Health** shows key presence, endpoint checks and service status without printing keys. `secrets.env` is gitignored and absent on a fresh clone.
- Environment up: see the **setup-workshop** skill (is DevX-Lab reachable / the nvwb app running).

## Starting a module over (the learner runs it)
`python code/workshop_support/reset.py <N>` copies the module's exercise files to
`~/workshop-backups/`, restores them from git, and stops the module's servers (Module 2 also
removes the local NIM container; its image and model cache stay). It prints the plan and asks
first. It changes files, so it is not a check: suggest it when a learner wants a clean start,
but never run it yourself. The learner should close the module's notebooks first.

## Per-module signals
### Module 1
- Remaining blanks: `python code/workshop_support/blanks.py 1` — checks `intro_to_agents.ipynb`
  and `docgen_client.ipynb` (21 blank lines when untouched: 18 + 3).
- "Done" = both notebooks run top-to-bottom without error (no persistent build artifact).

### Module 2
- Remaining blanks: `python code/workshop_support/blanks.py 2` (`rag_agent.py`). An `AGENT = ...`
  line still listed → not finished. (Note the three-stage `AGENT` rebuild — which tools are wired tells you how far they are.)
- Server running: `curl -s http://localhost:2024/ok` (the `langgraph dev` API; needed by the Simple Agents Client).

### Module 3
- **Prereq:** `python code/workshop_support/blanks.py 2` reports `rag_agent.py` blank-free; the M1 agent importable. If not, the workshop lets the *learner* copy the M2 answer key (linked from `running_evaluations.md`); you don't open or paste it.
- Remaining blanks: `python code/workshop_support/blanks.py 3` — the `FAITHFULNESS_PROMPT` rubric line in `evaluation_framework.py` plus the blanks in `evaluate_rag_agent.ipynb` and `evaluate_report_agent.ipynb`.
- Outputs are under `code/3-agent-evaluation/runs/`; inspect measurement coverage, not just file existence.

### Module 4
- Remaining blanks: `python code/workshop_support/blanks.py 4` — covers `bash_agent.ipynb`,
  `01_synthetic_data_generation.ipynb`, `02_grpo_training.ipynb` and `03_run_agent.ipynb`.
- Data ready: `ls code/4-agent-customization/data/langgraph_cli/train.jsonl` (155 reviewed training examples plus 50 held-out examples in `val.jsonl`, 10 per command; generated data uses a separate folder).
- Reward server up: `curl -s http://localhost:8001/health` (NeMo Gym `/verify` on the same port) — must be running before GRPO.
- Training: inspect `code/4-agent-customization/outputs/grpo_langgraph_cli/held_out_comparison.json` and test the merged export in a fresh process. A directory alone does not establish successful training or quality improvement.
- GPU: `nvidia-smi` (check capability and free memory; GB10 shares memory with the system).

### Module 5
- Remaining blanks: `python code/workshop_support/blanks.py 5` (`deep_agent.py`, 5 exercises; the `agent = ...` line in `create_agent` is last).
- Demo backend up: `curl -s http://localhost:8000/api/health` (`uvicorn server:app` in `demo/backend`). Docker: `docker ps`.
- Dry-run success prints "🎉 Your deep agent is working!".

### Module 6
- Control plane: `bash code/6-agent-safety/scripts/nemoclaw-health.sh` — read-only check of the socat tunnel, `nemoclaw` CLI install, gateway and sandbox `Phase: Ready`; prints the recovery command (it can legitimately be down; see the module's troubleshooting). `python3 code/6-agent-safety/scripts/diagnose-nemoclaw.py` is narrower: it shows what the NemoClaw Client's detection sees (why "Live NemoClaw Agent" isn't its default).
- Code sidekicks: `python code/workshop_support/blanks.py 6` — `agent_safety.py` blanks belong to `# TODO: Exercise 2`–`5` (`classify_sensitivity`/`run_redteam_probes`/`evaluate_safety`/`run_safety_suite`). It also lists three rubric `TODO: ...` lines in `safety_eval_framework.py`; no lesson or `agent_safety.py` uses that file, so treat them as optional.
- The Python eval runs against the **mock agent + `test_data/` fixtures even if the live stack is down** — so concept/code progress isn't blocked by a broken control plane.
- Docker: `docker ps`; kernel: check Landlock support with the Module 6 setup checks; version alone is insufficient.

### Module 7
- Remaining blanks: `python code/workshop_support/blanks.py 7` — checks both tracks (`harness_lab.py` and its notebook twin `harness_lab.ipynb`; a learner works in one of them) and lists the `model = ...` blank (1a) and each `NotImplementedError("Complete Exercise …")` stub (1b, 2a, 2b(i), 2b(ii), 5).
- Authored skill (Ex3): `ls code/7-agent-harnesses/skills/dataset-profiler/SKILL.md`. Verified skill (Ex4): `ls code/7-agent-harnesses/skills/accelerated-computing-cudf/SKILL.md` (run `scripts/install_nvidia_skill.sh` first).
- GPU (Ex4 comparison only): `nvidia-smi` — absent is fine: `run_gpu_task` prints a no-GPU (or no-cuDF) warning and the agent must use an available stack, e.g. pandas. "Done" = `python harness_lab.py --exercise N` runs for each completed exercise.

## Readiness gates (for "am I ready for module N?")
- **→ M3:** M1 + M2 agents built (or the learner copies the M2 answer key — sanctioned by the M3 lesson; you don't open or paste it).
- **→ M4:** a capable NVIDIA GPU (else do SDG + concepts only; the training run needs the GPU).
- **→ M5:** Docker (for sandbox mode).
- **→ M6:** Docker + Landlock enabled for live hardening (the eval code works without).
- **→ M7:** M1–M6 concepts (the capstone — it names the harness layer used throughout). NVIDIA key only; Exercise 4's cuDF path needs a GPU (without one, `run_gpu_task` warns and the agent should use pandas). No successor module.

## Reminder
Read-only only. If a blank is unfilled → it's an *exercise* (guide, don't fill it). If it is filled but errors, distinguish learner-code, service and environment failures using the module's `troubleshooting.md`. Report what you find, classify, and suggest the next step.
