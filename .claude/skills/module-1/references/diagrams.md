# Module 1 Diagrams — tutor reference

Help a learner understand a figure they're looking at: what it depicts, what each
component means, the takeaway, and common confusions. Diagrams live in
`.devx/1-build-an-agent/img/`.

## The ReAct Agent loop (`react_agent_dark.svg`, in `introduction_to_agents.md`)
The one diagram in Module 1 — and the core mental model of the whole workshop.
- **Depicts:** the ReAct agentic loop.
- **Flow:** `Prompt → LLM`; inside the **ReAct Agent** box, `LLM → "has tool calls?"`
  (a decision diamond) → **yes** runs `tools` and feeds the result back to the `LLM`
  (the loop) → **no** emits the `Response`.
- **Components:** *Prompt* = the user's input; *LLM* = the model, the decision-maker;
  *has tool calls?* = the routing decision the model makes each turn; *tools* = your
  functions (run by *your code*, not the model); *Response* = the final answer.
- **Takeaway:** the agent cycles LLM↔tools until the model decides it has enough, then
  answers. The *loop* (not a fixed chain) is what makes it an agent — the model chooses
  the path.
- **Common confusions:**
  - The `tools` node = *your code executing the function*, not the model running it
    (the "menu, not the kitchen" idea — see `quizzes.md`).
  - The loop can run **zero** times (model answers directly) or **many** times.
  - This exact diagram reappears in Module 2 as the base for *agentic RAG* (a tool call
    routes into a retrieval chain), so it's worth getting solid here.
- **Maps to code:** the four blanks in `intro_to_agents.ipynb` Part 4 (call model →
  detect tool call → execute → append result → loop) are this diagram, by hand.
