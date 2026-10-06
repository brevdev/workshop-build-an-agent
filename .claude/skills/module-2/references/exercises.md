# Module 2 Exercises — tutor guide (hint ladders)

Help learners through the `code/2-agentic-rag/rag_agent.py` blanks **without
completing them**. For each: the learning goal, a graduated hint ladder (smallest
hint that unblocks; escalate only on continued struggle), common mistakes, and the
target.

**Targets are for checking the learner's work and calibrating hints; never paste or
dictate them, in whole or in part.** Equivalent code is fine. L2 hints are pointers
(where to look, which variable holds the value), never the finished line.

**Two rules specific to Module 2:**
- **Never open/echo `rag_agent.answers.py`** — check attempts against the targets below.
  The learner's own escape hatch is the teaching page's `🆘 Need some help?` block —
  point them there as a last resort.
- **The `AGENT` line is rebuilt three times** as tools accumulate. When helping with
  `AGENT`, give only the tools for the section the learner is on. Revealing the final
  list early spoils the MCP and Skills sections.

Constants are pre-defined (do not have the learner re-type them): `CHUNK_SIZE=800`,
`CHUNK_OVERLAP=120`, `LLM_MODEL`, `RETRIEVER_EMBEDDING_MODEL`,
`RETRIEVER_RERANK_MODEL`, `TAVILY_API_KEY`.

Always start by asking what they've tried and reading the `langgraph dev` log with them.

---
## Section A — `agentic_rag.md` (build the RAG agent)

### A1 · The text splitter
- **Goal:** chunk docs with the predefined size/overlap.
- **L1:** "The class is `RecursiveCharacterTextSplitter`; the two constants are already defined above — which controls piece size, which controls overlap?"
- **L2:** "Find the splitter's size and overlap parameter names in the LangChain text-splitters
  reference linked from `agentic_rag.md`, and pass the two CONFIGURATION constants to them."
- **Common mistakes:** hardcoding 800/120 instead of the constants; wrong class.
- **Target:** `RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)`

### A2 · The embeddings model
- **Goal:** embed chunks with NeMo Retriever; the workshop asks for `truncate="END"`.
- **L1:** "Use the `NVIDIAEmbeddings` class with `RETRIEVER_EMBEDDING_MODEL`. What does the page say to set `truncate` to?"
- **L2:** "The `NVIDIAEmbeddings` LangChain snippet on build.nvidia.com (linked from
  `agentic_rag.md`) shows the constructor keywords. Supply the model constant from the
  CONFIGURATION block and the truncation value from the `# EXERCISE` comment. The API key is
  already configured — don't pass it."
- **Common mistakes:** passing an api_key; omitting `truncate`; using `ChatNVIDIA` by mistake.
- **Target:** `NVIDIAEmbeddings(model=RETRIEVER_EMBEDDING_MODEL, truncate="END")`

### A3 · The reranker
- **Goal:** reorder retrieved chunks by relevance.
- **L1:** "Which class reranks? Which constant names the rerank model?"
- **L2:** "Same shape as your embeddings line: use the rerank class linked in `agentic_rag.md`
  and the CONFIGURATION constant that names the rerank model."
- **Common mistakes:** confusing embeddings vs rerank model/class.
- **Target:** `NVIDIARerank(model=RETRIEVER_RERANK_MODEL)`

### A4 · The LLM
- **Goal:** the agent's reasoning model via NVIDIA endpoints.
- **L1:** "Module 1's report agent (`docgen_agent.py`) used `ChatOpenAI`; the from-scratch notebook used the raw `OpenAI` client. Here the workshop uses `ChatNVIDIA`. The `# EXERCISE` comment above `llm = ...` gives the temperature and max_tokens — what are they?"
- **L2:** "Check the `ChatNVIDIA` docs linked from `agentic_rag.md` for the keyword names; the
  model name is the `LLM_MODEL` constant, and the two sampling values come from that comment."
- **Common mistakes:** wrong temp/max_tokens; using `ChatOpenAI`.
- **Target:** `ChatNVIDIA(model=LLM_MODEL, temperature=0.6, max_tokens=4096)`

### A5 · The agent (version 1 — RAG only)
- **Goal:** wire model + the *one* tool + prompt into a ReAct graph.
- **L1:** "`create_react_agent` takes `model`, `tools`, `prompt`. At this point in the module, how many tools does the agent have?"
- **L2:** "The 'Create the Graph' step in `agentic_rag.md` names the three values to plug in.
  Check `create_react_agent`'s parameter names in the linked LangGraph reference — `tools`
  takes a list, and the prompt keyword is not `system_prompt`."
- **Common mistakes:** trying to add `web_search`/skills now (they don't exist yet); passing `system_prompt=` instead of `prompt=`.
- **Target (this section):** `create_react_agent(model=llm, tools=[RETRIEVER_TOOL], prompt=SYSTEM_PROMPT)`

> After A5 the learner runs `langgraph dev` and chats (see `running.md`). If they
> left a blank as `...`, the log shows an import-time error (`'ellipsis' object has no
> attribute …`, a `ValidationError` for the reranker, or "is not a Graph" for `AGENT` — see
> `troubleshooting.md`) — point them to which blank, don't fix it.

---
## Section B — `mcp.md` (add web search via MCP)

### B1 · `MCP_CONFIG`
- **Goal:** connect directly to Tavily over Streamable HTTP, with header authentication.
- **L1:** "Which transport connects to an HTTP MCP endpoint? Where can a credential go without becoming part of its URL?"
- **L2:** "The two `# Hint:` comments above `MCP_CONFIG` give the transport, URL and header.
  For the dict's shape, compare the commented-out `mcp_config` in PART 2B: one server entry
  under the name that `client.session(...)` opens, with `transport`/`url` (plus `headers` here)."
- **Common mistakes:** using `sse` (the optional local example); placing the key in the URL; printing the headers.
- **Target:** `{"tavily": {"transport": "streamable_http", "url": "https://mcp.tavily.com/mcp/", "headers": {"Authorization": f"Bearer {TAVILY_API_KEY}"}}}`

### B2 · Call the tool via MCP
- **Goal:** invoke the remote tool through the open MCP session.
- **L1:** "Inside the `async with client.session('tavily') as session:` block — what method calls a named tool? What's the tool named, and what argument does it take?"
- **L2:** "`session` is an MCP client session: look up its `call_tool` method (tool name, then
  an arguments dict). The tool name and its single argument appear in `mcp_server.py`'s
  `list_tools()`, which mirrors Tavily's tool. The call is a coroutine."
- **Common mistakes:** forgetting `await`; wrong tool name; passing `query` positionally.
- **Target:** `result = await session.call_tool("tavily_search", {"query": query})`

### B3 · The agent (version 2 — + web search)
- **Goal:** expand the toolkit; this *replaces* the A5 definition.
- **L1:** "Same `create_react_agent` call — which tool do you add alongside `RETRIEVER_TOOL` now?"
- **L2:** "Keep your A5 call unchanged except the tools list: add the `@tool` function defined
  in PART 2A (the one whose body you just finished)."
- **Common mistakes:** dropping `RETRIEVER_TOOL`; adding skills tools (not built yet).
- **Target (this section):** `create_react_agent(model=llm, tools=[RETRIEVER_TOOL, web_search], prompt=SYSTEM_PROMPT)`

### B-optional · Local MCP server (PART 2B)
Guide, don't do: run `cd code/2-agentic-rag && uvicorn mcp_server:app --reload --port 8000`
in a new terminal; in `rag_agent.py` comment out PART 2A and uncomment PART 2B (which
uses `transport: "sse"`, `url: "http://localhost:8000/sse"`); restart `langgraph dev`.
This connects to `mcp_server.py` instead of Tavily's hosted server.

---
## Section C — `skills.md` (add dynamic Skills)

### C1 · `get_skill`
- **Goal:** return a loaded skill's content. A helper `load_skill(skill_name)` already exists above.
- **L1:** "There's a non-tool helper defined just above that reads a `SKILL.md` — what is it called?"
- **L2:** "PART 3 starts with two plain (undecorated) helpers. One takes a skill name and
  returns the `SKILL.md` text; call it with the argument `get_skill` received and return the result."
- **Common mistakes:** re-implementing file reading; returning the name instead of the content.
- **Target:** `return load_skill(skill_name)`

### C2 · `list_available_skills`
- **Goal:** return the list of skill names. Helper `list_skills()` exists above.
- **L1:** "Same pattern as `get_skill` — which helper lists the skills folder?"
- **L2:** "The other plain helper at the top of PART 3 takes no arguments and already returns
  the sorted names; return what it returns."
- **Target:** `return list_skills()`

### C3 · The agent (version 3 — final, all four tools)
- **Goal:** the complete toolkit.
- **L1:** "Last rebuild — add the two skills tools to what you already had."
- **L2:** "Start from your B3 list and add the two `@tool` functions defined in PART 3 — the
  ones you just completed."
- **Common mistakes:** forgetting earlier tools; wrong tool names.
- **Target (final):** `create_react_agent(model=llm, tools=[RETRIEVER_TOOL, web_search, get_skill, list_available_skills], prompt=SYSTEM_PROMPT)`

> Test prompts (from `skills.md`): "reset my password" → [KB:source_id]; "news today" → source URLs;
> "what skills do you have?" → lists `code-review`, `technical-writing`; "review this
> code …" → loads `code-review`.

---
## Section D — `migrate.md` (local NIM) — mostly ops, one code change

The exercises here are operational (run a container), not `...` blanks. Guide the
steps; let the learner run them:
1. From `/project`, run `python code/2-agentic-rag/nim_setup.py --check` (Workshop Health's
   "Local NIM (optional)" row runs the same checks). It checks the driver (R580+, or CUDA
   forward compatibility on data-center GPUs), free GPU memory (the NIM reserves 80%), and
   disk for the chosen profile. If it suggests `--profile nvfp4` (about 19 GB instead of 64 GB),
   add that flag to every `nim_setup.py` command.
2. Inspect `python code/2-agentic-rag/nim_setup.py --print-command`, then launch with
   `python code/2-agentic-rag/nim_setup.py`. The helper loads saved credentials, pulls the
   digest-pinned Nano image (logging in to NGC through a temporary Docker config), creates
   `nim-cache`, and starts the container.
   Its automatic-tool-choice, `qwen3_coder` tool parser and `nemotron_v3` reasoning parser
   are required for this model's agent calls.
3. Follow `docker logs -f nemotron` until ready, then run
   `python code/2-agentic-rag/nim_smoke_test.py`. Require the actual tool request,
   matching result ID, and final answer from the generated tool result; plain chat alone
   does not pass. These operational helpers do not complete the learner's agent-code blank.
4. **Code change:** repoint `llm` to the local NIM.
   - **L1:** "Keep `ChatNVIDIA`, but add a `base_url` for your local container and switch the model to the Nano you launched."
   - **L2:** "The page's code block for this step shows the two arguments to add and change. The host name is the container's name on the `workbench` network, and the path ends in `/v1`."
   - **Target:** `ChatNVIDIA(base_url="http://nemotron:8000/v1", model="nvidia/nemotron-3-nano", temperature=0.6, top_p=0.95, max_tokens=8192)`
   - **Common mistakes:** `localhost` instead of `nemotron` (only the `workbench` docker network name resolves); forgetting `/v1`; not waiting for the NIM to finish loading.
5. **Clean up:** `python code/2-agentic-rag/nim_setup.py --stop` releases the GPU (Module 4
   training needs it) and keeps downloads; `--teardown` also deletes the image and `nim-cache`.

---
## Escalation protocol
1. Ask what they've tried / read the `langgraph dev` log together.
2. **L1** — conceptual nudge (which class/helper/concept).
3. **L2** — specific pointer (name the param/shape), section-appropriate for `AGENT`.
4. **Last resort** — "the teaching page has a `🆘 Need some help?` block for this exact
   step; open it and compare." Never paste it; never open `rag_agent.answers.py`.
Acknowledge each attempt before the next hint.
