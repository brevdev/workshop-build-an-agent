# Cross-Module Connections — tutor reference

Concept *threads* that span modules. Use for synthesis questions ("how does X relate to
Y?", "what's the difference between MCP, Skills, and deep-agent skills?") and to help a
learner see the workshop as one arc rather than eight islands. Don't spoil a module the
learner hasn't reached — give a one-line teaser and point forward.

## Thread 1 — The agent core (ReAct everywhere)
The ReAct loop is the spine. **M1** builds it from scratch (LLM ↔ tools until done). **M2**'s
agentic RAG is *the same loop* with a retrieval chain exposed as a tool (`create_react_agent`).
**M5**'s deep agent is *the same loop* wrapped in a middleware pipeline (planning, sub-agents,
filesystem). Same idea, increasing structure. (The `react_agent` diagram literally recurs in
M1 and M2.)

## Thread 2 — Tools → Skills (capability vs know-how)
- **M1:** a tool is a Python function the model *requests* and your code runs.
- **M2:** **MCP** = tools as reusable external services; **Agent Skills** = `.md` instructions
  loaded on demand. MCP provides *tools to do things*; Skills provide *know-how*.
- **M4:** **Superpowers** skills give the bash agent structured workflows.
- **M5:** deep-agent **skills** are thousands-of-token operating procedures injected into the prompt.
- **M7:** the **open Agent Skills spec** — the portable format that runs unchanged in every harness, plus NVIDIA Verified Skills. *(Nice: the very
  skills powering this tutor are that format.)*

## Thread 3 — The model thread (hosted → local → trained)
- **Hosted Nemotron** via NIM is the default everywhere (M1–M3, M5, M6).
- **Local NIM** appears as an *option*: M2's "Migrate to Local NIM" (`nemotron-3-nano` container)
  and M6's local Privacy-Router backend.
- **Trained model:** M4 fine-tunes `Nemotron-Nano-9B-v2` with GRPO into a CLI expert.
- M5 also shows **non-NVIDIA models served via NVIDIA's endpoints** (llama, deepseek in `MODEL_MAP`).
- **A portfolio, not a pick:** M8 stops treating the model as a constant — Lightning 30B (efficient/open)
  and Super 120B (the frontier **stand-in**) both in play, chosen per call; Ex4b puts the efficient
  tier back on a local NIM.

## Thread 4 — The safety arc (the workshop's spine)
Each module adds capability *and* a stronger control — *trust the model → trust the container
→ trust the kernel*:
- **M1** tool scoping · **M2** data-access boundaries · **M3** adversarial test cases ·
  **M4** HITL + command allowlists (application level) · **M5** container isolation + resource
  limits (Docker) · **M6** kernel enforcement (Landlock/seccomp), deny-by-default network, and
  the Privacy Router (data routing).
- The M6 `enforcement_spectrum` / `defense_layers_comparison` diagrams *are* this thread, drawn out.

## Thread 5 — The evaluation thread (quality ↔ safety)
**M3** asks *"is the agent helpful?"* (faithfulness, relevancy, RAGAS). **M6** asks *"is the
agent controlled?"* (red-team + defense-in-depth). They share the *same* machinery —
rubric → LLM-judge chain → JSON parse → aggregate — and the same judge model (Nemotron, temp 0).
M6's `safety_eval_framework.py` is M3's pattern, retargeted to safety.

## Thread 6 — The NVIDIA-tech thread
- **NIM / API Catalog** — hosted inference, all modules.
- **NeMo Retriever** (embed + rerank) — M2 (RAG), M3 (RAGAS uses embeddings).
- **NeMo Data Designer** (SDG) — M3 (eval datasets), M4 (training data).
- **NeMo Gym** (verifiable rewards) — M4.
- **NemoClaw + OpenShell** (kernel enforcement + Privacy Router) — M6.
- **NVIDIA Verified Skills** (portable, signed capability) — M7.
- **NeMo Switchyard** (open-source model router: library / gateway / launcher) — M8.
- **NeMo Agent Toolkit / NeMo Evaluator / AI-Q Blueprint** — explore-next pointers in M3/M5/M6.
- Per-module specifics + the NVIDIA-vs-third-party split: each module's `references/nvidia-tech.md`.

## Thread 7 — The economics thread (M8 closes the loop M1 opened)
Module 8 is a callback module: every exercise reuses something the learner already has.
- **M1 — the fourth component, full circle.** M1 named four components (model / tools / memory /
  routing) and then pinned the first to a constant at the top of the file. **M8 unpins it:** the
  model becomes a per-call decision. (And M1's "routing" meant *control flow* — which step runs
  next — a different sense of the same word.)
- **M2 — the NIM runbook, parameterized.** Optional Exercise 4b's `scripts/serve_local_nim.sh`
  *is* M2's "Migrate to Local NIM" runbook with the model swapped: `docker login nvcr.io`, a
  cached model volume, a container on the workbench network — now serving the router's **weak
  tier** on the learner's own GPU while hard turns escalate to the hosted 120B.
- **M3 — the eval suite is what earns the claim.** Exercise 5 is M3's rule applied to routing:
  *no claim without a suite*. Same machinery, second role — the LLM-judge pattern grades the one
  un-checkable task **and** (as Switchyard's `llm_classifier`) becomes the router itself, which
  is where judging acquires a **price** (the router tax). Closing beat: *the router didn't earn
  the savings claim; the eval suite did.*
- **M4 — specialists as routing targets, and RLVR again.** M4's fine-tuned model was a capability
  argument; routing supplies the missing **economic** one — *customize small, then route to it*
  (Boomi: 59% of production traffic on a 5× faster fine-tuned model). 11 of the lab's 12 tasks
  carry **verifiable checks** rather than a judge — M4's RLVR reflex pointed at routing. And
  **learned/prefill routers are M4's train-vs-prompt decision one level up:** train the router
  when tuning-free routing plateaus on your workload.
- **M5 — the deep agent is the shape routing was benchmarked on.** LangChain's 145-task
  deep-agent run is the benchmark M8 quotes throughout, and any loop that appends `ToolMessage`s
  can feed a `stage_router`. In-process routing is where a **middleware** would live — NVIDIA's
  launch coverage names LangChain, LiteLLM and Kong as surfaces — but ⚠️ **there is no Switchyard
  middleware package to install today**; treat it as direction, and the honest version is the
  shim the learner writes in Exercise 3.
- **M6 — policy routing vs performance routing.** *Who **may** answer* (the operator's
  Privacy Router: one chosen backend + credential injection, **never** content inspection) vs
  *who **should*** (a judge reading each request to pick the cheapest capable target). Same
  English word, opposite mechanisms, and **they compose** — policy outside, performance inside.
  This is the workshop's most-corrected confusion; see M6's and M8's `nvidia-tech.md`.
- **M7 — the context tax becomes the model bill.** M7: every token has a **cost** (per-turn
  overhead you measure). M8: every token has a **price**, and the price depends on who generates
  it. The harness M7 built is exactly what emits the tool-result trajectory a stage router reads
  — and `switchyard launch claude|codex|openclaw` points M7's harnesses at a router directly.

## Common cross-module questions
- *"MCP vs Skills vs deep-agent skills?"* → MCP = tools/services (do); Skills = instructions
  (how); deep-agent skills = longer operating procedures. Threads 2.
- *"How do M4 HITL, M5 sandbox, M6 kernel enforcement relate?"* → escalating safety layers;
  HITL is soft/app-level, sandbox is container-level, kernel enforcement is irrevocable. Thread 4.
- *"Is M3 eval the same as M6 eval?"* → same pattern, different question (quality vs safety). Thread 5.
- *"Which Nemotron is which?"* → Super (120B) for reasoning/judge; Nano (9B/30B/4B) for
  local/SDG/training. Thread 3 + the module `nvidia-tech.md` files.
- *"Isn't M6's Privacy Router the same as M8's router?"* → No. M6 = **policy** routing (who *may*
  answer: the operator's chosen backend + credential injection, **never** content inspection);
  M8 = **performance** routing (who *should*: a judge reads the request). They compose. Thread 7.
- *"Which module covers M1's 'routing'?"* → three different senses: **M1** control flow (which
  step), **M6** policy (which backend), **M8** model routing (which brain). Thread 7.
