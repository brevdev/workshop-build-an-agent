# Module 5 Quizzes — tutor deep-dive

Richer "Check Your Understanding" feedback than the in-page two-liner. Encourage an attempt
first; then explain the answer, the principle, why each distractor is tempting, and how to
go deeper.

## `intro_deep_agents.md` — "What actually makes an agent deep rather than shallow?"
- **Correct:** *It adds planning, delegation, memory, and skills around the loop.*
- **Why:** depth is **architecture, not raw model size** — the *same* model becomes a deep
  agent by wrapping the ReAct loop with the four pillars (the middleware pipeline).
- **Distractors:** *bigger model* / *longer context* → both help but don't make it deep (a
  deep agent on the same model still beats a shallow one; a longer window just delays
  overflow); *more tools* → a shallow agent can have many tools too.
- **Principle:** the four pillars; shallow vs deep is structural (`concepts.md`).
- **Go deeper:** map each pillar to its middleware node in `diagrams.md` (TodoList, SubAgent,
  Filesystem/Summarization, Tools/Skills).

## `deep_agents.md` — "Analyze 20 sources without overflowing the context window."
- **Correct:** *Delegate clusters of sources to sub-agents with isolated context.*
- **Why:** each sub-agent works in its *own* clean window and returns only a short summary,
  so no single context holds all 20 sources. That's Pillar 2 (hierarchical delegation).
- **Distractors:** *summarization* → helps, but still funnels everything through one context;
  *bigger model / longer window* → 20 full sources still pile up — architecture, not size,
  prevents overflow.
- **Principle:** context isolation via delegation (the `hierarchical_delegation` diagram).
- **Go deeper:** contrast with a shallow agent doing the same task (all 20 summaries in one
  window) — why it degrades around step 50.

## `sandboxing_security.md` — "Agent keeps generating dangerous shell commands. Contain it how?"
- **Correct:** *Run it in a sandbox with no host mounts and resource limits.*
- **Why:** once an agent passes control to a **subprocess**, only **OS-level enforcement**
  contains it. A sandbox with no host mounts means a dangerous command has nothing to destroy.
- **Distractors:** *a system-prompt rule* → the model can hallucinate past it and a subprocess
  bypasses it entirely; *lower temperature* → reduces randomness, not capability — one bad
  command is still catastrophic; *bigger model* → still a model, still hallucinates. **Safety
  comes from the boundary around the agent, not the agent's judgment.**
- **Principle:** *trust the sandbox, not the model* — the module's thesis (`concepts.md`).
- **Go deeper:** this sets up Module 6 — kernel-level enforcement (Landlock/seccomp) and
  deny-by-default egress when even container isolation leaves gaps.
