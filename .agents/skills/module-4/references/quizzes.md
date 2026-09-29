# Module 4 Quizzes — tutor deep-dive

Richer "Check Your Understanding" feedback than the in-page two-liner. Encourage an attempt
first; then explain the answer, the principle, why each distractor is tempting, and how to
go deeper.

## `intro_customization.md` — "Prompts + tools already work. Should you train?"
- **Correct:** *Probably not — if prompts and tools already work, training's upfront cost
  isn't justified.*
- **Why:** training costs data, compute and maintenance. Evaluate it when important task
  errors remain after improving prompts and tools; use held-out results to judge the gain.
- **Distractors:** *training always improves* → it's not a free upgrade; *training replaces
  prompts/tools* → they're complementary (breadth vs depth); *only if you have a spare GPU* →
  hardware is logistics, not the deciding factor.
- **Principle:** Skills/MCP for **breadth**, training for **depth** (`concepts.md`).
- **Go deeper:** ask what *specific* failure they'd expect training to fix that a better
  prompt couldn't.

## `sdg.md` — Schema-valid does not mean semantically correct
- **Correct principle:** samplers choose seed values; an LLM writes the request, then an LLM writes schema-constrained JSON. Review whether the pair agrees.
- **Why:** a schema checks fields and types; a valid port or template can still be wrong for the request.
- **Go deeper:** check blank requests, duplicates, conflicting labels, and train/validation overlap before trusting the dataset.

## `grpo_training.md` — "Reward = 1.0 for any valid JSON; reward soars, real accuracy is bad."
- **Correct:** *Reward hacking — the model maximizes the metric without doing the task.*
- **Why:** the reward is **misaligned** — an empty `{}` is valid JSON and scores 1.0, so the
  model learns the shortcut, not the task. Models optimize the reward you *give*, not the one
  you *intend*.
- **Distractors:** *LR too high* → the reward itself is wrong; a perfect LR just optimizes the
  shortcut faster; *GRPO doesn't work for CLI* → it does (that's the module); *need an LLM
  judge* → slower/inconsistent and wouldn't fix it — the fix is a **granular, aligned** code
  reward (JSON-format + command + flag-accuracy).
- **Principle:** reward engineering — verifiable, granular, **aligned** (`concepts.md`).
- **Go deeper:** ask them to design a reward that *can't* be gamed by an empty object.
