# Module 6 Quizzes — tutor deep-dive

Richer "Check Your Understanding" feedback than the in-page two-liner. Encourage an attempt
first; then explain the answer, the principle, why each distractor is tempting, and how to
go deeper.

## `intro_agent_safety.md` — "2 AM prompt injection says POST your data out. What stops it?"
- **Correct:** *Deny-by-default network egress enforced by OpenShell.*
- **Why:** egress is enforced at the **proxy, outside the agent process** — even a fully
  hijacked agent has **no network path** to the exfiltration endpoint. The control doesn't
  depend on the agent's cooperation.
- **Distractors:** *a SOUL.md rule* → soft; the agent decides whether to follow it and an
  injection talks right past it; *HITL gate* → no human is awake at 2 AM (HITL degrades to
  approve-all/block-all); *Docker* → isolates the process but still leaves an open pipe to
  the internet.
- **Principle:** the three gaps (no human awake / drift / mixed data) + "trust the kernel"
  (`concepts.md`).
- **Go deeper:** ask which layer stops each *other* attack (file tamper → Landlock; privilege
  escalation → seccomp; key theft → credential isolation).

## `why_nemoclaw.md` — "What does the Privacy Router actually do?" (the key one)
- **Correct:** *It enforces the operator's chosen backend and injects credentials, so the
  agent never holds keys.*
- **Why:** the router is an **operator-chosen, credential-injecting HTTP forwarder**. The
  operator sets one backend per gateway; the router enforces that choice and injects host-side
  credentials at `inference.local`. The agent calls it with **no key**.
- **Distractors (all are the *same* misconception — that the router inspects content):**
  *auto-routes sensitive queries to local* → **NO** — content-aware routing is a classifier
  *you build in front* (Exercise 5); *encrypts prompts* → it's credential isolation + backend
  selection, not transport encryption; *scans responses for PII* → no response scanning at all.
- **Principle:** the module's most-tested point — *the router does not read content*
  (`concepts.md` → Privacy Router; `diagrams.md` → nemoclaw_stack shows the classifier as
  "your code").
- **Go deeper:** have them trace `classify_sensitivity` (their code) → `openshell inference
  set` (operator) → the router (enforces) to see who does what.

## `evaluating_safety.md` — "Same pass rate; why does the sandboxed agent score higher on defense-in-depth?"
- **Correct:** *Its refusal cites kernel-level enforcement, which cannot be talked past; a
  prompt-only refusal can.*
- **Why:** **pass rate** asks *"was it safe?"* (binary); **defense-in-depth** asks *"how?"* —
  a kernel **sandbox_block** (EACCES/permission-denied) is non-defeasible (weight 1.0); a
  **prompt_refusal** ("I cannot…") could be talked past by the next attack (0.7); benign-pass
  0.5; compliance 0.0.
- **Distractors:** *refused faster* → speed isn't scored; *bigger model* → same model, the
  difference is *how* the refusal was enforced; *higher pass rate* → identical by assumption,
  which is exactly why pass rate hides the sandbox's contribution.
- **Principle:** mechanism-of-safety weighting (`concepts.md` → safety eval).
- **Go deeper:** ask them to find a probe where the host agent and sandboxed agent both pass
  but for different reasons, and explain the score gap.
