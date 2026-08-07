# Module 7 Diagrams — tutor reference

Help a learner understand a figure they're looking at: what it depicts, what each part
means, the takeaway, and common confusions. Figures live in the teaching pages under
`.devx/7-agent-harnesses/` (rendered by docsify — Mermaid graphs + HTML widgets).

## The harness flowchart — "engine vs car" (`intro_agent_harnesses.md`)
- **Depicts:** a `THE HARNESS` box wrapping the agentic loop. Five capability nodes —
  **Memory**, **Skills**, **Tool calling**, **Self-evolution**, **Token efficiency** — feed an
  inner `The Agentic Loop` containing the **LLM** ("stateless, tokens in → tokens out"). The
  **User** sits outside, talking to the whole harness, not the model.
- **Takeaway:** the model is one stateless node *inside* a larger machine; everything that
  persists, executes, and budgets lives in the harness around it. That's why *same model +
  different harness = a different agent*.
- **Common confusions:** the LLM box is the *engine*, not the agent — the agent is the whole
  diagram. The `Token efficiency` node connects with a dotted "budgets" line because it isn't a
  capability the loop *calls*; it's the constraint that governs how much of everything else
  enters context each turn.
- **Paired animation:** the `dx-term` "the agentic loop" panel shows one turn from the
  harness's side — prompt → think → `[tool] read_file` → `tokens: …/128,000` → answer. The
  model only ever sees tokens; the harness does the reading, running, and counting.

## The Context Tax Meter (`harness_landscape.md`)
- **Depicts:** horizontal bars of **permanent per-turn overhead** (system prompt + always-loaded
  tool schemas): pi ~1k (*minimal*) → OpenCode ~3.5k → LangChain Deep Agents ~4.5k → Hermes ~6k
  → OpenClaw ~7.5k → Claude Code / Codex 7–10k (*maximal*).
- **Takeaway:** a ~10× spread in what different designers consider "necessary" before the user
  says a word. The *shape* is the lesson.
- **Common confusions:** this is a **bet axis, not a quality ranking** — a higher tax is not
  "worse"; maximal harnesses spend those tokens on built-in capability, minimal ones bet the
  model loads capability on demand. And the numbers are **order-of-magnitude estimates that
  shift every release** — which is exactly why the learner measures their own in Exercise 2
  (the `PLACE YOUR BET` widget primes this).

## SKILL.md → every harness — portability (`agent_skills.md`)
- **Depicts:** one `SKILL.md` node fanning out to **OpenClaw, Hermes, Claude Code, Codex,
  Cursor** — one portable skill, many harnesses.
- **Takeaway:** the harness market is fiercely competitive (open vs. closed, minimal vs.
  maximal), yet capability packaged as a skill is portable across *all* of it. Write once,
  supercharge any agent — the open [agentskills.io](https://agentskills.io) spec at work.
- **Common confusions:** the arrows flow *outward from* the skill — it's "one skill → many
  harnesses," not a harness aggregating skills. (Meta-note: these tutoring skills are that same
  format.)

## GPU division of labor (`gpu_skills.md`)
- **Depicts:** a sequence diagram — **You** → **Harness (local)** → **LLM (cloud)** writes
  `cudf.pandas` code → **Harness** executes it on **Your GPU (local)** → results back to the
  model → analysis to you.
- **Takeaway:** the cloud model never touches your data at GPU scale — it writes a few hundred
  tokens of code; **your local GPU does the heavy compute.** True in every harness. A
  subscription buys the brain; the muscles are yours.
- **Common confusions:** learners assume a cloud/subscription harness means the GPU is idle —
  the opposite is the page's whole point. The skill is what makes the model reach for the GPU
  *correctly* (right library/API/patterns); without it the model just writes CPU pandas.

## Supporting widgets
- **Gauges** (`intro`, `landscape`, `harness_lab` "YOUR TARGETS") — the same tax expressed as a
  fraction of a 32K budget (e.g. minimal ~400, maximal ~3,922 tokens). They visualize Exercise
  2's targets; treat them as illustrative, not exact.
- **The verified skill card** (`agent_skills.md`) — `accelerated-computing-cudf` with
  `NVIDIA VERIFIED ✓`, SkillSpector checks (prompt injection / tool poisoning / dangerous
  code), the `skill.oms.sig` signature, and a skill card (use case, risks, deps, eval agents).
  It's the visual of *capability governance* — verify, don't just publish.
