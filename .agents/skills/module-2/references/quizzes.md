# Module 2 Quizzes — tutor deep-dive

Richer "Check Your Understanding" feedback than the in-page two-liner. If the learner
hasn't attempted the quiz, encourage a guess first; then explain the answer, the principle,
why each distractor is tempting, and how to go deeper.

## `intro.md` — "A user sends a simple greeting 'Hi there!'. What happens?"
- **Correct:** *The model can skip retrieval entirely and just respond.*
- **Why:** in agentic RAG, retrieval is a **tool the model chooses to call** — a greeting
  needs no outside context, so the agent answers directly. This is the exact difference from
  traditional RAG.
- **Distractors:** *runs KB retrieval as it does for every query* → that's **traditional**
  RAG's fixed path; *must embed the greeting and search first* → embeddings are computed to
  *store* docs at ingestion, not to answer every turn.
- **Principle:** "who decides whether to retrieve?" (the agentic-RAG thesis; `concepts.md`).
- **Go deeper:** have them watch the agent skip the retriever tool on a greeting in the
  Simple Agents Client trace, then call it on an IT question.

## `mcp.md` — "Where does the Tavily MCP tool's code actually run?"
- **Correct:** *On the MCP server; your agent discovers and calls it over the protocol.*
- **Why:** MCP decouples tools from the agent — the tool lives/runs on the server (Tavily's
  hosted one here); your agent just calls it. "Build once, use anywhere."
- **Distractors:** *inside your agent's process after MCP copies the code* → that's the
  pre-MCP, bundled-tool approach MCP exists to replace; *the LLM runs it directly* → the LLM
  never executes tool code (same menu-not-kitchen idea as Module 1).
- **Principle:** MCP = tools as separate, reusable services (`concepts.md` → MCP).
- **Go deeper:** contrast with Module 1's hand-written `search_tavily` tool — MCP eliminates
  that bundling.

## `skills.md` — "Code-review standards: MCP or a Skill?"
- **Correct:** *A Skill — it loads the standards as instructions the agent follows.*
- **Why:** MCP provides **tools (to *do* things)**; Skills provide **instructions (*how* to
  do them well)**. Coding standards are guidance, not a callable API — that's a Skill.
- **Distractors:** *MCP exposes the standards as a callable tool* → conflates instructions
  with tools; *hardcode into the system prompt* → exactly what Skills improve on (modularity,
  reuse, on-demand loading vs a bloated prompt).
- **Principle:** MCP vs Skills (the `concepts.md` table) — complementary: LLM (brain) + MCP
  (capabilities) + Skills (know-how).
- **Go deeper (nice connection):** the Agent Skills format the learner is reasoning about is
  the *same* format that powers Claude Code skills — including this tutor. Module 7 goes deeper.
