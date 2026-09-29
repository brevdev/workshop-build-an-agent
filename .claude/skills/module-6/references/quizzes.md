# Module 6 Quizzes — tutor deep-dive

Richer "Check Your Understanding" feedback than the in-page two-liner. Encourage an attempt
first; then explain the answer, the principle, why each distractor is tempting, and how to
go deeper.

## `intro_agent_safety.md` — "Which control enforces a per-destination allowlist?"
- **Correct:** *Deny-by-default network egress enforced by OpenShell.*
- **Why:** egress is enforced at the **proxy, outside the agent process** — when no matching allow rule exists, even a fully
  hijacked agent cannot use that endpoint through the enforced network path. The control doesn't
  depend on the agent's cooperation.
- **Distractors:** *a SOUL.md rule* → guidance, not an enforced boundary;
  *HITL gate* → waits for a person, without itself defining allowed destinations;
  *Docker* → network behavior depends on configuration; Module 5
  explicitly disables container networking, while its web/RAG tools run in the application.
- **Principle:** the three gaps (no human awake / drift / mixed data) + "trust the kernel"
  (`concepts.md`).
- **Go deeper:** ask which layer stops each *other* attack (file tamper → Landlock; privilege
  escalation → seccomp; key theft → credential isolation).

## `why_nemoclaw.md` — "What does the Privacy Router actually do?" (the key one)
- **Correct:** *It enforces the chosen backend and injects inference credentials at the gateway.*
- **Why:** the router is an **operator-chosen, credential-injecting HTTP forwarder**. The
  operator sets one backend per gateway; the router enforces that choice and injects host-side
  credentials at `inference.local`. The agent calls it with **no key**.
- **Distractors:**
  *auto-routes sensitive queries to local* → **NO** — Exercise 5 builds a separate
  classifier that only proposes a route; *encrypts prompts* → it's credential isolation + backend
  selection; *scans responses for PII* → it does not classify or redact PII.
- **Principle:** *the router does not classify sensitivity or redact PII*
  (`concepts.md` → Privacy Router; `diagrams.md` → nemoclaw_stack shows the classifier as
  "your code").
- **Go deeper:** distinguish classifier output from actual routing. Explain why changing a
  shared gateway per prompt can send another request to the wrong destination.

## `evaluating_safety.md` — “The agent says permission denied. What can you conclude?”
- **Correct:** inspect the tool result and operator-side logs before attributing the denial.
- **Why:** the model can say those words without attempting a tool call. Even a real error
  may come from POSIX permissions, Landlock, a proxy, or another layer.
- **Distractors:** the text does not prove a kernel block or establish deployment safety.
- **Principle:** keep evidence of enforcement separate from quality of the answer.
- **Go deeper:** compare a canary leak after a refusal, a refused benign request, and a
  timeout. The first two fail screening; the timeout is a missing measurement. None can be
  averaged into a passing result. Offline screening alone is not a full rubric review.
