# Cross-Module Connections — tutor reference

Concept *threads* that span modules. Use for synthesis questions ("how does X relate to
Y?", "what's the difference between MCP, Skills, and deep-agent skills?") and to help a
learner see the workshop as one arc rather than seven separate modules. Don't spoil a module the
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
- **M5:** deep-agent **skills** provide task procedures; their bodies load when selected.
- **M7:** the **open Agent Skills spec** — a shared format with harness-specific tool and runtime requirements, plus NVIDIA Verified Skills. *(Nice: the very
  skills powering this tutor are that format.)*

## Thread 3 — The model thread (hosted → local → trained)
- **Hosted Nemotron** is the default for model calls across the workshop, including M4 SDG. Shared roles select the endpoints.
- **Local NIM** is optional in M2. M6 explains operator routing but does not start a local model server.
- **Trained model:** M4 fine-tunes `Nemotron-Nano-9B-v2` with GRPO into a CLI expert.
- M5 offers the two configured Nemotron chat roles; the UI uses the backend's actual model list.

## Thread 4 — The safety arc (the workshop's spine)
The controls address different risks and can be combined:
- **M1** tool scoping · **M2** retrieval and evidence · **M3** behavior and quality checks ·
  **M4** HITL + command allowlists (application level) · **M5** container isolation + resource
  limits (Docker) · **M6** kernel enforcement (Landlock/seccomp), deny-by-default network, and
  the Privacy Router (operator-controlled inference routing).
- The M6 `enforcement_spectrum` / `defense_layers_comparison` diagrams *are* this thread, drawn out.

## Thread 5 — The evaluation thread (quality ↔ safety)
**M3** asks *"is the agent helpful?"* (faithfulness, relevancy, RAGAS). **M6** checks supplied safety cases and runtime boundaries. Both use rubrics and a configured judge, with missing measurements kept separate. M6 also uses explicit violation checks; text scores do not prove kernel enforcement.

## Thread 6 — The NVIDIA-tech thread
- **NVIDIA API Catalog** — hosted model calls across the course; local NIM is optional in M2.
- **NeMo Retriever** (embed + rerank) — M2 (RAG), M3 (RAGAS uses embeddings).
- **NeMo Data Designer** (SDG) — M3 (eval datasets), M4 (training data).
- **NeMo Gym** (verifiable rewards) — M4.
- **NemoClaw + OpenShell** (kernel enforcement + Privacy Router) — M6.
- **NeMo Agent Toolkit / NeMo Evaluator / AI-Q Blueprint** — explore-next pointers in M3/M5/M6.
- Per-module specifics + the NVIDIA-vs-third-party split: each module's `references/nvidia-tech.md`.

## Common cross-module questions
- *"MCP vs Skills vs deep-agent skills?"* → MCP = tools/services (do); Skills = instructions
  (how); deep-agent skills = longer operating procedures. Threads 2.
- *"How do M4 HITL, M5 sandbox, M6 kernel enforcement relate?"* → complementary controls;
  HITL gates actions, Docker restricts execution, and Landlock limits a running process's filesystem access. Thread 4.
- *"Is M3 eval the same as M6 eval?"* → same pattern, different question (quality vs safety). Thread 5.
- *"Which Nemotron is which?"* → Super/Lightning for hosted calls and Nano 9B v2 for M4 training. Thread 3 + the module `nvidia-tech.md` files.
