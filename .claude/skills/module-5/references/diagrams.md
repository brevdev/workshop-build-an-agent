# Module 5 Diagrams — tutor reference

Help a learner read the deep-agent figures. Diagrams in `.devx/5-deep-agents/img/`.

## shallow_agent_pattern (`shallow_agent_pattern_dark.svg`, `deep_agents.md`)
- **Depicts:** `User → Model → (ReAct Loop: Model ↔ Tool) → Response`.
- **Takeaway:** the baseline from Modules 1–2 — a single loop, everything in one context.
  Deep agents *extend* this; a deep agent's sub-agents are themselves shallow agents.

## middleware_pipeline (`middleware_pipeline_dark.svg`, `deep_agents.md`)
- **Depicts:** the deep-agent "batteries-included" stack — `User Message → Summarization →
  PatchToolCalls → Model → TodoList → {Filesystem, Execute, Tools/Skills}`, where Tools/Skills
  can spawn a `SubAgent` (`task`), all passing through an optional `HITL` gate, then looping.
- **Takeaway:** `create_deep_agent` builds *this* — each middleware adds a capability
  (planning/filesystem/shell/sub-agents/context-management) without you writing orchestration.
  The four pillars are visible: TodoList (planning), SubAgent (delegation), Filesystem +
  Summarization (memory), Tools/Skills (skills).

## hierarchical_delegation (`hierarchical_delegation_dark.svg`, `deep_agents.md`)
- **Depicts:** an `Orchestrator` ↔ specialized sub-agents (`Researcher`, `Analyst`, `Writer`),
  each with its own clean context.
- **Takeaway:** Pillar 2 — decompose, delegate to isolated sub-agents, only synthesized
  results return. This is how 20 sources don't overflow one context (the `deep_agents.md` quiz).

## agent_in_sandbox vs sandbox_as_tool (`sandboxing_security.md`) — the two patterns
- **agent_in_sandbox** (`agent_in_sandbox_dark.svg`): `Sandbox { Agent Process { Tools,
  FileSystem, API Keys } } ↔ External Services`. **Pattern 1** — the agent runs *inside* the
  sandbox; **API keys live inside it** (a risk), and updates need a rebuild.
- **sandbox_as_tool** (`sandbox_as_tool_dark.svg`): `Your Server { Agent, Keys, Orchestration }
  ↔ Remote Sandbox { Sandbox API, Code Execution, Isolated Env }`. **Pattern 2** — the agent
  runs on your server and **delegates execution** to an isolated sandbox; **keys stay out**,
  updates are instant, failures isolated. **deepagents uses Pattern 2** (Docker).
- **Takeaway:** the contrast is a security/ops trade-off table — where do credentials live,
  how fast can you update, what happens on failure. Pattern 2 wins for production.

## Common confusions
- The middleware pipeline is *not* a fixed chain — the loop + sub-agents make it dynamic;
  the diagram just shows the available stages.
- "Sandbox-as-tool" doesn't mean the sandbox is a Python function tool — it means execution
  is *delegated* to an isolated environment the agent calls, keeping keys/state separate.
