# Module 1 Concepts — tutor reference

Answer conceptual questions accurately and in the workshop's own voice using this.
For the authoritative narrative, read the teaching pages in
`.devx/1-build-an-agent/`. Keep answers concise; lead the learner to the source for depth.

## The evolution: three stages (`why_agents.md`)
1. **Single LLM call** — prompt in, response out. Limited to training data; no live info, no actions.
2. **Workflow / chain** — a fixed sequence of steps (e.g. RAG: retrieve → generate). More capable, but every query takes the same hardcoded path.
3. **Agent** — the **model decides what to do**: look at the situation, choose a tool (or none), act, observe, and repeat until done. The path adapts per task.

Mental model: *who decides the path, and how flexible is it?* Single call = no
decision; workflow = the developer hardcodes it; agent = the LLM chooses.

## When agents are (and aren't) the right tool
Use an agent when: the path varies by input; multiple tools must combine
dynamically; real-time/external info is needed; the task needs multi-step
reasoning; queries are open-ended. Prefer a simpler approach (single call or chain)
when: the steps are always the same; one call suffices; static/model knowledge is
enough; it's a simple transform or classification; inputs are well-structured.
Agents add **latency, tokens/cost, and complexity** — use them where the
adaptability pays for that overhead.

Worked examples from the module's quizzes:
- **Good agent fit:** "investigate a reported bug by searching the docs, checking
  incident reports, and writing a root cause" — variable path, multiple sources,
  each step depends on the last.
- **Not an agent:** "sort a ticket into billing/technical/other" (one fixed
  classification — a single call) or "translate a block of text" (one deterministic
  transform).

## The four components (`introduction_to_agents.md`)
- **Model** — the brain. Reads the conversation, decides whether to respond or call
  a tool, and generates output. Good agent models support **tool/function calling**,
  follow instructions reliably, and reason well. The workshop uses **NVIDIA Nemotron
  3 Super (120B)** via NVIDIA's hosted API catalog (no local GPU needed for inference).
- **Tools** — functions that let the agent act (search, calculate, call APIs). The
  model **does not run tools**; it *requests* them and your code executes them. Each
  tool needs a **schema** (name, description, parameters); description quality
  directly affects whether the model uses the tool well.
- **Memory / State** — context across the conversation. **Short-term** = the
  conversation log (messages, tool calls, results), reset at conversation end.
  **Long-term** = persistent knowledge (DBs / vector stores), covered in Module 2.
  Module 1 uses short-term only — a list of message dicts.
- **Routing** — the control logic that orchestrates the loop between reasoning and
  acting. Built by hand in `intro_to_agents.ipynb`; handled automatically by
  LangChain `create_agent` in the report agent.

## The agentic loop
1. Give the model the input + the available tools.
2. The model decides: **respond** or **call a tool**.
3. If a tool call → your code executes it, appends the result to memory, return to step 1.
4. If a response → return it to the user.

The loop runs until the model has what it needs. The model controls the flow, not hardcoded logic.

## The ReAct pattern (Reasoning + Acting)
The most common agent architecture. The agent alternates **Thought → Action →
Observation**: think ("I need current data"), act (call search), observe (read
results), think ("now I can answer"), act (write the answer). Diagram:
`.devx/1-build-an-agent/img/react_agent_dark.svg`. ReAct agents adapt to
intermediate results, retry, and decompose tasks — that flexibility is what
separates agents from fixed workflows.

**The key subtlety (both quizzes test it):** "tool calling" does **not** mean the
model runs code. The model only emits a structured request (tool name + arguments);
your routing layer runs the function, appends the result, then calls the model
again. Listing a tool in the schema is "the menu, not the kitchen."

## System prompts
A special message defining the agent's identity and behavior: who it is, how to
behave, when to use tools. The *same* model with a different system prompt behaves
very differently. In the report agent, the `ReportWriter` system prompt
(`docgen_agent.py`) sets the role, a quality bar ("never invent sources"), tool-use
rules ("you MUST use tavily_search for facts to verify"), and the output format. To
change behavior (tone, strictness, format), change the **prompt**, not the code.

## Failure modes (and why they matter)
- **Hallucination** — making things up, especially when tools return nothing.
- **Infinite loops** — calling tools without making progress.
- **Tool misuse** — wrong arguments, or calling a tool at the wrong time.
- **Cost runaway** — many tool calls = many tokens = higher cost.

These aren't reasons to avoid agents; they're reasons to **test and monitor**
(Module 3). When inspecting a run, watch for empty searches, repeated queries,
missing citations, and unexpected tool use.

## The Module 1 build, concretely (`report_generation_agent.md`)
The Report Generation Agent maps the four components onto real code:
- **Model:** `ChatOpenAI(base_url="https://integrate.api.nvidia.com/v1", model_name="nvidia/nemotron-3-super-120b-a12b", ...)` in `docgen_agent.py`.
- **Tools:** `search_tavily` in `tools.py` — async Tavily web search; the `@tool` decorator auto-generates the schema.
- **Memory/State:** managed by LangChain as conversation history (`state["messages"]`).
- **Routing:** `create_agent(model, tools, system_prompt)` builds a ReAct agent — no manual loop.

Terminology note the workshop calls out: it uses both "LangChain" and "LangGraph."
LangGraph is a low-level orchestration framework from the LangChain team (usable on its
own) for stateful, multi-step apps; `create_agent` is a LangChain utility that is *built
on* LangGraph under the hood — not the other way around.

## Source map
- Concepts → `why_agents.md`, `introduction_to_agents.md`
- The build → `report_generation_agent.md`, `docgen_agent.py`, `tools.py`
- From-scratch mechanics → `intro_to_agents.ipynb` (Parts 1–4 = the four components)
