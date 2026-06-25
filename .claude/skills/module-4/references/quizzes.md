# Module 4 Quizzes — tutor deep-dive

Richer "Check Your Understanding" feedback than the in-page two-liner. Encourage an attempt
first; then explain the answer, the principle, why each distractor is tempting, and how to
go deeper.

## `intro_customization.md` — "Prompts + tools already work. Should you train?"
- **Correct:** *Probably not — if prompts and tools already work, training's upfront cost
  isn't justified.*
- **Why:** training costs data + compute and bakes knowledge into weights. Reach for it only
  when the model **fundamentally lacks the domain** that prompts/tools can't supply (the
  "~90%" rule of thumb).
- **Distractors:** *training always improves* → it's not a free upgrade; *training replaces
  prompts/tools* → they're complementary (breadth vs depth); *only if you have a spare GPU* →
  hardware is logistics, not the deciding factor.
- **Principle:** Skills/MCP for **breadth**, training for **depth** (`concepts.md`).
- **Go deeper:** ask what *specific* failure they'd expect training to fix that a better
  prompt couldn't.

## `sdg.md` — "Why does NeMo Data Designer generate the OUTPUT first?"
- **Correct:** *Sampling outputs from the schema guarantees every example is valid; LLM-first
  can hallucinate invalid commands.*
- **Why:** schema-first means every output conforms to `CLIToolCall` *by construction*, and
  samplers guarantee coverage; the LLM only writes the matching user request. Ask an LLM for
  input/output pairs directly and it can invent commands/flags that don't exist.
- **Distractors:** *JSON is faster than NL* → both call an LLM, speed isn't the point;
  *LLMs can't write requests* → they can, that's exactly the second step; *avoid a schema* →
  backwards, the schema is the foundation.
- **Principle:** validity + coverage by construction (`concepts.md` → SDG).
- **Go deeper:** connect to Module 3's synthetic *eval* data — same tool, same "validate
  before trusting" caution.

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
