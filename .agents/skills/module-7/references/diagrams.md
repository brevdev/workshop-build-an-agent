# Module 7 Diagrams — tutor reference

Help a learner understand a figure they're looking at: what it depicts, what each part
means, the takeaway, and common confusions. Figures live in the teaching pages under
`.devx/7-agent-harnesses/` (rendered by docsify — Mermaid graphs + HTML widgets).

## The harness flowchart — "engine vs car" (`intro_agent_harnesses.md`)
- **Depicts:** a `THE HARNESS` box wrapping the agentic loop. Five possible capability nodes —
  **State / Memory**, **Skills**, **Tool calling**, **Optional self-evolution**, **Token efficiency** — feed an
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

## Comparing context overhead (`harness_landscape.md`)
The page compares design choices without a numerical vendor ranking. Exercise 2 estimates the two bundled configurations with one tokenizer and serialization method. Counts exclude model-specific formatting and are not billing measurements.

## SKILL.md → compatible harnesses — portability (`agent_skills.md`)
- **Depicts:** one `SKILL.md` node fanning out to **OpenClaw, Hermes, Claude Code, Codex,
  Cursor** — one skill format, multiple compatible harnesses; runtime dependencies remain separate.
- **Takeaway:** the file format is portable between compatible harnesses. Tool names, dependencies, permissions, and model behavior still matter.
- **Common confusions:** the arrows flow *outward from* the skill — it's "one skill → many
  harnesses," not a harness aggregating skills. (Meta-note: these tutoring skills are that same
  format.)

## GPU division of labor (`gpu_skills.md`)
- **Depicts:** a sequence diagram — **You** → **Harness (local)** → **LLM (cloud)** writes
  `cudf.pandas` code → **Harness** executes it on **Your GPU (local)** → results back to the
  model → analysis to you.
- **Takeaway:** in this lab, the tool backend executes the proposed code on the workshop machine. Other backends may run remotely. Tool outputs can reach the hosted model, so local compute alone does not ensure privacy.
- **Common confusions:** a skill can guide GPU use; it neither guarantees correctness nor makes every workload faster. Check the generated code and compare results and timings.

## Supporting widgets
- **Gauges** (`intro`, `landscape`, `harness_lab` "YOUR TARGETS") — the same tax expressed as a
  fraction of a 32K budget (e.g. minimal ~400, maximal ~3,922 tokens). They visualize Exercise
  2's targets; treat them as illustrative, not exact.
- **The verified skill card** (`agent_skills.md`) — `accelerated-computing-cudf` with
  `NVIDIA VERIFIED ✓`, SkillSpector checks (prompt injection / tool poisoning / dangerous
  code), the `skill.oms.sig` signature, and a skill card (use case, risks, deps, eval agents).
  It's the visual of *capability governance* — verify, don't just publish.
