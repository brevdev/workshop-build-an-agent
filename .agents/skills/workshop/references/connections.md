# Cross-Module Connections — tutor reference

Concept *threads* that span modules. Use for synthesis questions ("how does X relate to
Y?", "what's the difference between MCP, Skills, and deep-agent skills?") and to help a
learner see the workshop as one arc rather than six islands. Don't spoil a module the
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
- **NeMo Agent Toolkit / NeMo Evaluator / AI-Q Blueprint** — explore-next pointers in M3/M5/M6.
- Per-module specifics + the NVIDIA-vs-third-party split: each module's `references/nvidia-tech.md`.

## Common cross-module questions
- *"MCP vs Skills vs deep-agent skills?"* → MCP = tools/services (do); Skills = instructions
  (how); deep-agent skills = longer operating procedures. Threads 2.
- *"How do M4 HITL, M5 sandbox, M6 kernel enforcement relate?"* → escalating safety layers;
  HITL is soft/app-level, sandbox is container-level, kernel enforcement is irrevocable. Thread 4.
- *"Is M3 eval the same as M6 eval?"* → same pattern, different question (quality vs safety). Thread 5.
- *"Which Nemotron is which?"* → Super (120B) for reasoning/judge; Nano (9B/30B/4B) for
  local/SDG/training. Thread 3 + the module `nvidia-tech.md` files.
