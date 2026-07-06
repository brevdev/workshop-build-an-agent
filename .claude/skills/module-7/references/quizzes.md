# Module 7 Quizzes — tutor deep-dive

Use this to give richer "Check Your Understanding" feedback than the in-page two-liner. If the
learner hasn't attempted the quiz yet, encourage a guess first (the struggle is the learning);
once they've engaged, explain the correct answer, the underlying principle, why each distractor
is *tempting* but wrong, and how to go deeper.

## `intro_agent_harnesses.md` — "Lazy skill loading belongs to which harness responsibility?"
- **Correct:** *Token efficiency.*
- **Why:** keeping skills as one-line descriptions until invoked is a deliberate spend of the
  **context budget** — you pay ~25 tokens for a skill's existence and the full body only when
  used. That's the token-efficiency responsibility doing its job.
- **Distractors (the misconception each encodes):**
  - *Memory* → memory is cross-*session* persistence; lazy loading happens within a single
    turn's context.
  - *Tool calling* → tool schemas are part of the tax, but lazy loading is a *budget* decision,
    not an execution mechanism.
  - *Self-evolution* → that's the agent rewriting its own scaffolding; lazy loading is the
    harness managing what *enters* context.
- **Principle:** four responsibilities are table stakes; **token efficiency is the axis that
  sorts the landscape** (`concepts.md` → the context tax).
- **Go deeper:** ask them to predict their Exercise 2 eager-vs-lazy numbers before running it.

## `harness_landscape.md` — "Always-on, on-prem models mandatory, largest community → which harness?"
- **Correct:** *OpenClaw.*
- **Why:** it's open source (so on-prem/any model), built for always-on heartbeat operation, and
  has the biggest community — and NemoClaw hardens it (Module 6).
- **Distractors:**
  - *Claude Code* → closed source; no on-prem model choice.
  - *pi* → model-flexible but the *minimal* pole — smallest batteries-included assistant story.
  - *OpenCode* → you *could* build it, but you inherit all five responsibilities yourself.
- **Principle:** the 3-question chooser — model flexibility → always-on vs task-shaped →
  community/defaults. (Prefer stronger defaults + a curated skill hub? → Hermes.)
- **Go deeper:** have them run the chooser on a project they actually have.

## `agent_skills.md` — "30 skills installed, none in use — what's in context?"
- **Correct:** *Thirty one-line descriptions* (~750 tokens) — the trigger surface; bodies load
  on demand.
- **Why:** lazy loading keeps the `name: description` lines resident so the model knows what
  *could* be loaded, and pulls a full body (~1,500 tokens) only when a task matches.
- **Distractors:**
  - *All 30 full bodies* → that's **eager** loading — ~45,000 tokens of tax every turn (the
    anti-pattern).
  - *Nothing at all* → then the model could never know when to load one.
  - *Only the most recently used* → recency isn't the trigger; the *descriptions* match against
    the task.
- **Principle:** descriptions are the trigger surface; this is pi's design, now standard.
- **Go deeper:** this is exactly what they implement in Exercise 2b — connect the answer to their loader.

## `gpu_skills.md` — "Claude Code (cloud model) aggregates a 10M-row CSV with the cuDF skill — where's the heavy compute?"
- **Correct:** *On your local GPU.*
- **Why:** the cloud model only writes a few hundred tokens of `cudf` code; the **harness
  executes it locally**, so the aggregation runs on your GPU — watch `nvidia-smi`.
- **Distractors:**
  - *In Anthropic's datacenter* → the model never touches your data at GPU scale; it writes code.
  - *Nowhere — subscriptions can't use local hardware* → tools/skills execute locally by design.
  - *Split 50/50* → it's a clean division: cloud writes code, your GPU runs it.
- **Principle:** the division of labor — a subscription buys the brain; the muscles (your GPU)
  are yours. The skill makes the model reach for the GPU correctly.
- **Go deeper:** in Exercise 4 they watch this happen with `watch -n 0.5 nvidia-smi`; the GPU spike
  *is* the proof.

> No in-page quiz on `harness_lab.md` / `evaluating_harnesses.md` — those are the hands-on lab
> and the wrap-up. For a recap, ask the learner to name the five responsibilities and which one
> sorts the landscape, or to map each lab exercise to its production counterpart (the wrap-up table).
