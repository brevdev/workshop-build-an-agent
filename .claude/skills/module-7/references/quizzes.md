# Module 7 Quizzes — tutor deep-dive

Use this to give richer "Check Your Understanding" feedback than the in-page two-liner. If the
learner hasn't attempted the quiz yet, encourage a guess first (the struggle is the learning);
once they've engaged, explain the correct answer, the underlying principle, why each distractor
is *tempting* but wrong, and how to go deeper.

## `intro_agent_harnesses.md` — "Lazy skill loading belongs to which harness responsibility?"
- **Correct:** *Token efficiency.*
- **Why:** descriptions enter the initial context; full instructions arrive on demand.
  Token counts depend on the actual text and tokenizer.
- **Distractors (the misconception each encodes):**
  - *Memory* → retains information within or across sessions; this question focuses on
    initial context size.
  - *Tool calling* → tool schemas are part of the tax, but lazy loading is a *budget* decision,
    not an execution mechanism.
  - *Self-evolution* → that's the agent rewriting its own scaffolding; lazy loading is the
    harness managing what *enters* context.
- **Principle:** context overhead is one measurable harness design choice (`concepts.md` → the context tax).
- **Go deeper:** ask them to predict their Exercise 2 eager-vs-lazy numbers before running it.

## `harness_landscape.md` — "Which always-on assistant did Module 6 configure?"
- **Correct:** *OpenClaw.*
- **Why:** Module 6 uses OpenClaw with NemoClaw and a configurable compatible model endpoint. No community-size ranking is implied.
- **Distractors:**
  - *Claude Code* → not the assistant configured in Module 6.
  - *pi* → Module 7 borrows its minimal design; Module 6 configured OpenClaw.
  - *OpenCode* → it has its own runtime and server options; Module 6 configured OpenClaw.
- **Principle:** the 3-question chooser — model flexibility → always-on vs task-shaped →
  community/defaults. (Prefer stronger defaults + a curated skill hub? → Hermes.)
- **Go deeper:** have them run the chooser on a project they actually have.

## `agent_skills.md` — "New conversation, 30 lazy skills, no body loaded — what's in context?"
- **Correct:** *Thirty one-line descriptions* — the trigger surface; bodies load
  on demand.
- **Why:** lazy loading keeps the `name: description` lines resident so the model knows what
  *could* be loaded, and pulls a full body (~1,500 tokens) only when a task matches.
- **Distractors:**
  - *All 30 full bodies* → eager loading; the page's 45,000 initial tokens are illustrative.
  - *Nothing at all* → then the model could never know when to load one.
  - *Only the most recently used* → recency isn't the trigger; the *descriptions* match against
    the task.
- **Principle:** the lab initially exposes descriptions; the model can request full bodies.
- **Go deeper:** this is exactly what they implement in Exercise 2b — connect the answer to their loader.

## `gpu_skills.md` — "This workshop harness executes cuDF code on the GPU machine — where does aggregation run?"
- **Correct:** *On your local GPU.*
- **Why:** this harness executes the generated cuDF code on the workshop GPU.
- **Distractors:**
  - *In Anthropic's datacenter* → the model proposes code; the configured tool backend runs it.
  - *Nowhere — subscriptions can't use local hardware* → tools execute where the backend is configured.
  - *Split 50/50* → it's a clean division: cloud writes code, your GPU runs it.
- **Principle:** execution location depends on the tool backend, not the instruction format.
- **Go deeper:** inspect executed code and validate numerical output alongside GPU activity.

> No in-page quiz on `harness_lab.md` / `evaluating_harnesses.md` — those are the hands-on lab
> and the wrap-up. For a recap, ask the learner to name the five responsibilities and which one
> sorts the landscape, or to map each lab exercise to its production counterpart (the wrap-up table).
