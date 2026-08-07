# Module 7 Troubleshooting — tutor reference

**Triage first.** Environment/runtime (give direct fixes), exercise blank (guide — see
`exercises.md`), or a concept/behavior question (teaching — see `concepts.md`)? The lab is
light on infrastructure — most issues are an unfilled blank, a missing key, or the optional
Hermes/verified-skill/GPU setup. Runtime fixes below are fair to give directly.

## Unfilled exercise blanks (the #1 cause)
Each blank raises `NotImplementedError("Complete Exercise N…")` until filled — the message
names the exact exercise. `python harness_lab.py --exercise N` will surface it. That's the
signal of an untouched blank (guide via `exercises.md`), **not** a bug to fix for them.
- `--exercise 1` raises in `build_bare_agent` → 1a/1b unfilled.
- `--exercise 2` raises in `harness_overhead` (2a) or `load_skills_lazily` (2b) → that blank.
- `--exercise 5` raises in `self_evolve_skill` → Ex 5 unfilled.

## Keys, imports, dependencies
- **`NVIDIA_API_KEY`** in repo-root `secrets.env` (gitignored) — every harness + the lab call
  `nvidia/nemotron-3-super-120b-a12b` through `integrate.api.nvidia.com`. **401** → key
  missing/invalid (set it via the Secrets Manager / https://build.nvidia.com).
- **`ModuleNotFoundError: tiktoken`** (Ex 2) or `langchain_nvidia_ai_endpoints` → install the
  workshop deps: `pip install -r requirements.txt` (run from the repo root). `tiktoken` uses
  the `cl100k_base` encoding — it downloads the encoding file on first use (needs network once).
- The lab is **CPU + hosted** for Ex 1/2/3/5; no Docker, no GPU needed there.

## Hermes (Exercise 1's "full harness" comparison — optional)
Hermes is one option; the **Module 6 OpenClaw** agent works too — the point is *a* full
harness, not a specific one.
- **Install:** `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`, then
  `hermes setup` → choose **Custom OpenAI-compatible endpoint**.
- **Point it at Nemotron** (`~/.hermes/config.yaml`): `provider: custom`,
  `default: nvidia/nemotron-3-super-120b-a12b`, `base_url: https://integrate.api.nvidia.com/v1`,
  `api_key: ${NVIDIA_API_KEY}`.
- **"Hermes can't reach the model" / auth errors** → the `base_url` is missing `/v1`, the
  `api_key` env var isn't exported in that shell, or the model name is wrong. Same Nemotron
  endpoint the minimal harness uses.
- **Skills:** Hermes auto-discovers everything in `~/.hermes/skills/`; `cp -r` a skill folder
  there (Ex 3) or `hermes skills install NVIDIA/skills/<name>` (agentskills.io-compatible).

## The verified-skill install (Exercise 4)
- `bash code/7-agent-harnesses/scripts/install_nvidia_skill.sh accelerated-computing-cudf`
  clones [`NVIDIA/skills`](https://github.com/NVIDIA/skills), checks the `skill.oms.sig`
  signature, prints the skill card, and installs into the lab `skills/` dir. Needs **network +
  git** (and, for `npx skills add`, **Node/`npx`** — already in the DevX-Lab container).
- **Signature/verification fails** → don't bypass it; that's the governance point. Re-clone /
  check network; a failed signature means *don't trust the skill*.
- **`run_gpu_task` says "Skill not installed"** → the install script hasn't run (or installed
  elsewhere); it looks for `skills/accelerated-computing-cudf/SKILL.md`.

## GPU / cuDF (Exercise 4)
- **GPU util stays at 0** → the dataset must cross the **100K-row size gate** the skill teaches
  (the generator makes ~1M rows by default); confirm cuDF imported GPU-side:
  `python -c "import cudf; print(cudf.__version__)"`.
- **No GPU on the box** → expected and handled: `run_gpu_task` detects `nvidia-smi` is absent,
  prints a clear fallback message, and runs pandas instead; the answers notebook shows the
  expected GPU output. The *concept* (local execution, the division of labor) still lands.
- **Test data missing** → `run_gpu_task`/`run_self_evolution_demo` auto-run
  `scripts/make_test_data.py` to create `test_data/sensor_readings.csv`; you can run it manually.

## Self-evolution (Exercise 5)
- **The second run breaks the loader** → the agent wrote a malformed `SKILL.md`. The fix the
  exercise teaches: `parse_frontmatter()` to **validate before saving** (a bad frontmatter
  breaks the next `load_skills_lazily` glob). This is the self-evolution failure mode Module 6
  warned about — in production NemoClaw write-policies the skills directory.
- **Skill written but not picked up next run** → it landed outside `skills/<name>/SKILL.md`
  (the loader globs `skills/*/SKILL.md`), or the body still has ``` fences breaking the parse.

## Optional closed-harness track (no fix needed, just framing)
Claude Code / Codex are **subscription** and entirely optional — the whole lab runs in open
harnesses on Nemotron. If a learner wants to verify portability:
`npx skills add nvidia/skills --skill accelerated-computing-cudf --agent claude-code` (or
`--agent codex`). Same `SKILL.md`, same GPU, different harness.

## "Just build/run it for me" (policy reminder, not a bug)
Decline and explain (rules 1–2): the blanks, the authored skills (Ex 3/5), and the runs are
the learner's. Offer the next-smallest hint or the `🆘` block. Fixing the environment
(keys, imports, Hermes endpoint, the install script) you *can* do directly.
