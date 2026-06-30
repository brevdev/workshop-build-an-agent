# Module 2 Exercises — tutor guide (hint ladders)

Help learners through the `code/2-agentic-rag/rag_agent.py` blanks **without
completing them**. For each: the learning goal, a graduated hint ladder (smallest
hint that unblocks; escalate only on continued struggle), common mistakes, and the
target.

**Two rules specific to Module 2:**
- **Never paste the target, and never open/echo `rag_agent.answers.py`.** The targets
  below are for *your* calibration. The learner's own escape hatch is the teaching
  page's `🆘 Need some help?` block — point them there as a last resort.
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
- **L2:** "Pass `chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP`."
- **Common mistakes:** hardcoding 800/120 instead of the constants; wrong class.
- **Target:** `RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)`

### A2 · The embeddings model
- **Goal:** embed chunks with NeMo Retriever; the workshop asks for `truncate="END"`.
- **L1:** "Use the `NVIDIAEmbeddings` class with `RETRIEVER_EMBEDDING_MODEL`. What does the page say to set `truncate` to?"
- **L2:** "`NVIDIAEmbeddings(model=RETRIEVER_EMBEDDING_MODEL, truncate='END')`. The API key is already configured — don't pass it."
- **Common mistakes:** passing an api_key; omitting `truncate`; using `ChatNVIDIA` by mistake.
- **Target:** `NVIDIAEmbeddings(model=RETRIEVER_EMBEDDING_MODEL, truncate="END")`

### A3 · The reranker
- **Goal:** reorder retrieved chunks by relevance.
- **L1:** "Which class reranks? Which constant names the rerank model?"
- **L2:** "`NVIDIARerank(model=RETRIEVER_RERANK_MODEL)`."
- **Common mistakes:** confusing embeddings vs rerank model/class.
- **Target:** `NVIDIARerank(model=RETRIEVER_RERANK_MODEL)`

### A4 · The LLM
- **Goal:** the agent's reasoning model via NVIDIA endpoints.
- **L1:** "Module 1's report agent (`docgen_agent.py`) used `ChatOpenAI`; the from-scratch notebook used the raw `OpenAI` client. Here the workshop uses `ChatNVIDIA`. The page gives the temperature and max_tokens — what are they?"
- **L2:** "`ChatNVIDIA(model=LLM_MODEL, temperature=0.6, max_tokens=4096)`."
- **Common mistakes:** wrong temp/max_tokens; using `ChatOpenAI`.
- **Target:** `ChatNVIDIA(model=LLM_MODEL, temperature=0.6, max_tokens=4096)`

### A5 · The agent (version 1 — RAG only)
- **Goal:** wire model + the *one* tool + prompt into a ReAct graph.
- **L1:** "`create_react_agent` takes `model`, `tools`, `prompt`. At this point in the module, how many tools does the agent have?"
- **L2:** "Just the retriever: `tools=[RETRIEVER_TOOL]`, plus `model=llm, prompt=SYSTEM_PROMPT`."
- **Common mistakes:** trying to add `web_search`/skills now (they don't exist yet); passing `system_prompt=` instead of `prompt=`.
- **Target (this section):** `create_react_agent(model=llm, tools=[RETRIEVER_TOOL], prompt=SYSTEM_PROMPT)`

> After A5 the learner runs `langgraph dev` and chats (see `running.md`). If they
> left any blank as `...`, the log shows `'ellipsis' object has no attribute …` —
> point them to which blank, don't fix it.

---
## Section B — `mcp.md` (add web search via MCP)

### B1 · `MCP_CONFIG`
- **Goal:** configure a stdio MCP client that bridges to Tavily's remote server.
- **L1:** "The page hints: `transport` is `stdio`, `command` is `npx`. What does `npx` run to bridge to a remote MCP server?"
- **L2:** "`args` runs `mcp-remote` against Tavily's URL with your key: `['-y', 'mcp-remote', f'https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}']`, under a top-level `"tavily"` key."
- **Common mistakes:** wrong transport (`sse` is for the *local* server); forgetting the `-y`; dropping the f-string for the key.
- **Target:** `{"tavily": {"transport": "stdio", "command": "npx", "args": ["-y", "mcp-remote", f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"]}}`

### B2 · Call the tool via MCP
- **Goal:** invoke the remote tool through the open MCP session.
- **L1:** "Inside the `async with client.session('tavily') as session:` block — what method calls a named tool? What's the tool named, and what argument does it take?"
- **L2:** "`await session.call_tool('tavily_search', {'query': query})`."
- **Common mistakes:** forgetting `await`; wrong tool name; passing `query` positionally.
- **Target:** `result = await session.call_tool("tavily_search", {"query": query})`

### B3 · The agent (version 2 — + web search)
- **Goal:** expand the toolkit; this *replaces* the A5 definition.
- **L1:** "Same `create_react_agent` call — which tool do you add alongside `RETRIEVER_TOOL` now?"
- **L2:** "`tools=[RETRIEVER_TOOL, web_search]`."
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
- **L2:** "`return load_skill(skill_name)`."
- **Common mistakes:** re-implementing file reading; returning the name instead of the content.
- **Target:** `return load_skill(skill_name)`

### C2 · `list_available_skills`
- **Goal:** return the list of skill names. Helper `list_skills()` exists above.
- **L1:** "Same pattern as `get_skill` — which helper lists the skills folder?"
- **L2:** "`return list_skills()`."
- **Target:** `return list_skills()`

### C3 · The agent (version 3 — final, all four tools)
- **Goal:** the complete toolkit.
- **L1:** "Last rebuild — add the two skills tools to what you already had."
- **L2:** "`tools=[RETRIEVER_TOOL, web_search, get_skill, list_available_skills]`."
- **Common mistakes:** forgetting earlier tools; wrong tool names.
- **Target (final):** `create_react_agent(model=llm, tools=[RETRIEVER_TOOL, web_search, get_skill, list_available_skills], prompt=SYSTEM_PROMPT)`

> Test prompts (from `skills.md`): "reset my password" → [KB]; "news today" → [Web];
> "what skills do you have?" → lists `code_review`, `technical_writing`; "review this
> code …" → loads `code_review`.

---
## Section D — `migrate.md` (local NIM) — mostly ops, one code change

The exercises here are operational (run a container), not `...` blanks. Guide the
steps; let the learner run them:
1. NGC login: `echo $NVIDIA_API_KEY | docker login nvcr.io --username '$oauthtoken' --password-stdin`
2. `docker volume create nim-cache`
3. `docker run … --network workbench --gpus 1 -p 8000:8000 nvcr.io/nim/nvidia/nemotron-3-nano:latest` (wait for "Application startup complete")
4. **Code change:** repoint `llm` to the local NIM.
   - **L1:** "Keep `ChatNVIDIA`, but add a `base_url` for your local container and switch the model to the Nano you launched."
   - **L2:** "`base_url='http://nemotron:8000/v1'`, `model='nvidia/nemotron-3-nano'` (the page also sets `top_p=0.95`, `max_tokens=8192`)."
   - **Target:** `ChatNVIDIA(base_url="http://nemotron:8000/v1", model="nvidia/nemotron-3-nano", temperature=0.6, top_p=0.95, max_tokens=8192)`
   - **Common mistakes:** `localhost` instead of `nemotron` (only the `workbench` docker network name resolves); forgetting `/v1`; not waiting for the NIM to finish loading.

---
## Escalation protocol
1. Ask what they've tried / read the `langgraph dev` log together.
2. **L1** — conceptual nudge (which class/helper/concept).
3. **L2** — specific pointer (name the param/shape), section-appropriate for `AGENT`.
4. **Last resort** — "the teaching page has a `🆘 Need some help?` block for this exact
   step; open it and compare." Never paste it; never open `rag_agent.answers.py`.
Acknowledge each attempt before the next hint.
