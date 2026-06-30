# AGENTS.md

Instructions for coding agents (Codex, Claude Code, …) working in this repository.
This is the **Build-an-Agent workshop** (a.k.a. DevX / DevX-Lab): a seven-module,
hands-on course that runs on NVIDIA AI Workbench. Learners work through Jupyter
notebooks under `code/` and lessons under `.devx/`.

## The workshop tutor (Agent Skills)

This repo ships its tutor as **Agent Skills** — the cross-harness `SKILL.md` format.
They auto-load when an agent runs from the project root and trigger by description:

- `/workshop` — overview + router across the 7 modules
- `/module-1` … `/module-7` — one tutor per module
- `/setup-workshop` — local install helper
- `/nvwb`, `/nvwb-project` — NVIDIA AI Workbench CLI + in-container project awareness

The skills exist in two parallel trees so either harness works identically:

- `.claude/skills/` — read by **Claude Code**
- `.agents/skills/` — read by **Codex** (auto-discovered from `<repo>/.agents/skills/`)

When acting as the tutor (i.e. a learner invokes a `/module-N` or `/workshop` skill),
follow the skill's own rules: **guide, don't solve** — give graduated hints, never
complete a learner's exercise, and never reveal or open answer-key files
(`*answer*`, `answer_key/`, `*.answers/`). The canonical tutoring policy lives in
`.agents/skills/workshop/references/tutor-policy.md`. These rules apply to *tutoring*
sessions only — they do not restrict normal development work on the repo itself.

## Contributor convention: skills are a synced pair

`.claude/skills/` is the **canonical source**. `.agents/skills/` is **generated** from
it by `.agents/sync-codex-skills.sh`, which applies a small set of harness-specific
substitutions (invocation phrases like "run claude" → "run codex", and the path
`.claude/skills/` → `.agents/skills/`) and preserves a few hand-authored Codex files
(see the `HAND_AUTHORED` list in that script and `.agents/skills/VENDORED.md`).

**Edit skills in `.claude/skills/`, then run `bash .agents/sync-codex-skills.sh`** to
regenerate the Codex tree. Run `bash .agents/sync-codex-skills.sh --check` to verify the
two trees are in sync (CI-friendly: non-zero exit on drift). Do not hand-edit generated
files in `.agents/skills/` — your changes will be overwritten on the next sync.

## Environment notes

- The workshop targets NVIDIA AI Workbench containers (Linux, x86_64 and aarch64).
- `postBuild.bash` preinstalls both `claude` and `codex` (non-fatal if npm hiccups).
- `~/.claude/` and `~/.codex/` are persisted across container rebuilds (see `.project/spec.yaml`).
- API keys load from `secrets.env` (NVIDIA, optional Tavily/LangSmith); the harness
  itself needs its own credential (`codex login` or `OPENAI_API_KEY`; an Anthropic key for `claude`).
