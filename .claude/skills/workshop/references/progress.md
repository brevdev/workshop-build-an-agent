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

### Module 7
- Remaining blanks: `grep -nE 'NotImplementedError\("Complete Exercise' code/7-agent-harnesses/harness_lab.py` — any hits → that exercise's blank is still a stub (`build_bare_agent` 1a/1b, `harness_overhead` 2a, `load_skills_lazily` 2b, `self_evolve_skill` 5).
- Authored skill (Ex3): `ls code/7-agent-harnesses/skills/dataset_profiler/SKILL.md`. Verified skill (Ex4): `ls code/7-agent-harnesses/skills/accelerated-computing-cudf/SKILL.md` (run `scripts/install_nvidia_skill.sh` first).
- GPU (Ex4 speedup only): `nvidia-smi` — absent is fine (the exercise falls back to pandas + prints a skip message). "Done" = `python harness_lab.py --exercise N` runs for each completed exercise.

### Module 8
- Remaining blanks: `grep -nE 'raise NotImplementedError\("Exercise' code/8-agent-routing/routing_lab.py` —
  any hits → that blank is still a stub. Seven of them, in order: `1a` (`build_model_pool`),
  `1b` (`bill_call`), `2a` (`classify_difficulty`), `2b` (`route_call`), `3a` (`make_lab_router`),
  `3b` (`switchyard_call`), `5` (`routing_verdict`).
- **The learner's own progress signal is the Routing Client's `systems online: N/5` strip** — it
  is `probe_unlocks(module)` in `routing_lab.py` rendered as chips, grouped by who runs the
  decision (*no router · Ex 1* / *your code · Ex 2* / *NeMo Switchyard · Ex 3–4*) and labeled
  by algorithm, with the canonical ids in each chip's hover: Ex1 lights `strong_only` /
  `efficient_only` (the baseline chips) + the meter, Ex2 `manual_classifier` (the "llm
  classifier" chip), Ex3 `switchyard_stage` ("stage router"), Ex4 the `gateway` chip (when
  `:4000` answers), Ex5 the strip's fifth light ("the verdict" — no chip of its own).
  Asking "what does your header say?" is faster than any grep.
- Exercise 4's blank is a config file, so it isn't probed: `ls code/8-agent-routing/routes.toml`
  (git-ignored copy of `routes.toml.template` — absent = Ex4 not started) and gateway liveness
  `curl -s localhost:4000/v1/models` (returns the one route id `switchyard`);
  `curl -s localhost:4000/v1/stats` is the gateway's own meter (tier split + router tax).
- Switchyard SDK present (Ex3 runs a loud `MockRouter` without it — degraded, not broken):
  `python3 -c 'import switchyard; print(switchyard.__version__)'` or
  `ls ~/.local/share/module8-switchyard-venv/bin/python`. ⚠️ Don't "check" with
  `install_switchyard.sh --print-python` — on a cold box that call performs the install.
- Optional Ex4b only: `docker ps` + `nvidia-smi` (absent is fine — 4a is the full exercise).
- "Done" = each completed exercise runs (`python3 routing_lab.py --exercise N`). ⚠️ **Never run
  one to check** — the suites cost real money (~26–51 live calls each).

## Readiness gates (for "am I ready for module N?")
- **→ M3:** M1 + M2 agents built (or paste the M2 answer key — sanctioned).
- **→ M4:** a capable NVIDIA GPU (else do SDG + concepts only; the training run needs the GPU).
- **→ M5:** Docker (for sandbox mode).
- **→ M6:** Docker + Linux kernel ≥ 5.13 for the live hardening (the eval code works without).
- **→ M7:** M1–M6 concepts (it names the harness layer used throughout). NVIDIA key only; a GPU helps *only* for Exercise 4's cuDF speedup (skips cleanly without).
- **→ M8:** M1 + M7 concepts (the four components; the harness loop whose tool results a stage router reads); M2's local-NIM runbook only for the optional Ex4b. NVIDIA key only, Python ≥ 3.12 for the Switchyard install, and a network path to PyPI + `integrate.api.nvidia.com`. Budget a few cents of live calls. **Last module — no successor.**

## Reminder
Read-only only. If a blank is unfilled → it's an *exercise* (guide, don't fill it). If it's
filled but erroring → it's an *environment* problem (diagnose via the module's
`troubleshooting.md`). Report what you find, classify, and suggest the next step.
