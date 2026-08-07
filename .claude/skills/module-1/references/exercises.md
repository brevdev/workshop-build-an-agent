# Module 1 Exercises — tutor guide (hint ladders)

Use this to help learners through the exercises **without completing them**. For
each blank: the learning goal, a graduated hint ladder (give the smallest hint that
unblocks; escalate only on continued struggle), common mistakes, and the target.

**The "target" is what the learner should arrive at — it is already in the
notebook's own `💡 NEED SOME HELP?` block. Never paste it. Guide them to write it,
or as a last resort point them to that block.** The targets are listed here only so
you can calibrate hints and recognize a correct attempt.

Always start by asking what they've tried, and read the error/output *with* them.

---
## Notebook A — `intro_to_agents.ipynb` ("Agents the Hard Way")
A from-scratch build whose sections map one-to-one onto the four components. Config
(cell 5, given): `API_KEY = os.environ["NVIDIA_API_KEY"]`,
`MODEL_URL = "https://integrate.api.nvidia.com/v1"`,
`MODEL_NAME = "nvidia/nemotron-3-super-120b-a12b"`.

### A1 · Part 1 / The Model — create the client (cell 7)
- **Goal:** instantiate the OpenAI-compatible client pointing at NVIDIA's catalog.
- **L1:** "The two constants you need were defined just above — which is the URL, which is the key?"
- **L2:** "`OpenAI(...)` takes `base_url` and `api_key`. Pass the constants themselves, not new string literals."
- **L3:** "Open the `💡 NEED SOME HELP?` block right below the cell and compare."
- **Common mistakes:** re-typing the URL/key as literals; swapping the two; quoting the constant names.
- **Target:** `client = OpenAI(base_url=MODEL_URL, api_key=API_KEY)`

### A2 · Part 2 / Tools — write the `add` tool (cell 11)
- **Goal:** see that a "tool" is just a Python function.
- **L1:** "What should `add(a, b)` give back?"
- **L2:** "One line — return the sum."
- **Common mistakes:** `print`ing instead of `return`ing; adding type checks it doesn't need.
- **Target:** `def add(a, b): return a + b`
- The tool **schema** (cell 14) is provided — point out it mirrors the function (name, description, typed params). That schema is "the menu" the model reads.

### A3 · Part 4 / Routing — call the model (cell 18)
- **Goal:** invoke `call_llm` with the four pieces, then append the reply to memory.
- **L1:** "The markdown lists four arguments and what each maps to — which variable is your short-term memory? Your tool menu?"
- **L2:** "`model_client`→`client`, `model_name`→`MODEL_NAME`, `message_history`→`memory`, `tool_list`→`tools`. Don't forget `memory.append(llm_response)`."
- **Common mistakes:** passing `messages` (it's named `memory` here); forgetting the append.
- **Target:** `call_llm(model_client=client, model_name=MODEL_NAME, message_history=memory, tool_list=tools)`

### A4 · Part 4 / Routing — parse the tool request (cell 21)
- **Goal:** extract name/args/id; learn that `arguments` is a JSON **string**.
- **L1:** "Print `llm_response` — the tool call is a nested dict. Where's the function name? The arguments? The id?"
- **L2:** "`tool_call['function']['name']`, `json.loads(tool_call['function']['arguments'])`, `tool_call['id']`. The tip in the cell says why `json.loads` is needed."
- **Common mistakes:** forgetting `json.loads` (args arrive as a string); indexing the wrong nesting level.
- **Target:** `tool_name = tool_call["function"]["name"]`; `tool_args = json.loads(tool_call["function"]["arguments"])`; `tool_id = tool_call["id"]`

### A5 · Part 4 / Routing — execute the tool (cell 24) — *the punchline*
- **Goal:** realize **your code** runs the tool, not the model.
- **L1:** "You have `tool_args` as a dict of keyword arguments. How do you pass a dict as kwargs into `add`?"
- **L2:** "Unpack it: `add(**tool_args)`."
- **Common mistakes:** `add(tool_args)` (passes the whole dict as one positional arg).
- **Target:** `tool_out = add(**tool_args)`

### A6 · Part 4 / Routing — append the tool result (cell 27)
- **Goal:** feed the result back as a `tool` message so the model can use it next turn.
- **L1:** "You extracted three values earlier — which belongs in `tool_call_id`? In `name`? And what type must `content` be?"
- **L2:** "`tool_call_id`→`tool_id`, `name`→`tool_name`, `content`→`str(tool_out)`."
- **Common mistakes:** not stringifying `content`; mixing up `id` vs `name`.
- **Target:** `{"role":"tool","tool_call_id":tool_id,"name":tool_name,"content":str(tool_out)}`

### A7 · Close the loop — call the model again (cell 32)
- **Goal:** see that the second model call is identical to A3 — the loop repeats with the tool result now in memory.
- **L1:** "The hint says it's the exact same call as before. What did you write in cell 18?"
- **Target:** same as A3.

> **Teaching beat:** after A6, have them inspect `memory` (cell 30). The user
> message, the assistant's tool *request*, and the tool *result* are all there —
> that list **is** short-term memory and the ReAct trace.

---
## Notebook B — `docgen_client.ipynb` ("Document Generator")
The learner writes the client that drives the prebuilt `agent` (imported from
`docgen_agent.py`). Only two blanks.

### B1 · Define the query and initial state (cell 6)
- **Goal:** initialize the agent's state with a user message — same message shape as Notebook A.
- **L1:** "What shape is a message? You used it from scratch — role + content. What's the agent's *starting* state?"
- **L2:** "`state = {'messages': [{'role': 'user', 'content': user_query}]}`, with `user_query` a string describing the report you want."
- **Common mistakes:** key `message` vs `messages`; passing a bare string instead of a message dict; forgetting the list.
- **Target (in the cell's `💡` block):** `user_query = "…"` ; `state = {"messages": [{"role": "user", "content": user_query}]}`

### B2 · Invoke the agent (cell 9)
- **Goal:** run the agent asynchronously and grab the final message.
- **L1:** "The agent is async — how do you call an async method in a notebook? And where in the returned state does the final reply live?"
- **L2:** "`state = await agent.ainvoke(state)`, then `response = state['messages'][-1]`."
- **Common mistakes:** forgetting `await`; using `.invoke` instead of `.ainvoke`; indexing `[0]` instead of `[-1]`.
- **Target (in the cell's `💡` block):** `state = await agent.ainvoke(state)` ; `response = state["messages"][-1]`

> **Extra credit (from the teaching page):** print the whole `state["messages"]` to
> see every step — searches, observations, the final report. Great for connecting
> the run to the loop and to the "what to watch for" checklist (empty searches,
> repeated queries, missing citations).

---
## Escalation protocol
1. Ask what they've tried / read the error together.
2. **L1** — conceptual nudge.
3. **L2** — specific pointer (name the function / shape / variable).
4. **Last resort** — "there's a `💡 NEED SOME HELP?` block right below that cell; open it and compare with your attempt." Never paste it yourself.

Between levels, invite them to try and report back. Always acknowledge the attempt
before the next hint.
