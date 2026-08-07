# Module 2 Concepts — tutor reference

Answer conceptual questions accurately and in the workshop's own voice. For the
authoritative narrative, read the teaching pages in `.devx/2-agentic-rag/`. Keep
answers concise; lead the learner to the source for depth.

## From RAG to agentic RAG (`intro.md`)
- **Plain LLM:** prompt in, answer out — limited to training-time knowledge.
- **Traditional RAG:** retrieve relevant docs from a vector DB, then generate. More
  accurate, but the path is **fixed** — it retrieves *every* time, the model has no
  say in how/whether retrieval happens, and multiple sources get unwieldy.
- **Agentic RAG:** give a ReAct agent the retrieval chain **as a tool**. The model
  decides *when and how* to retrieve — and can choose among multiple sources. A bare
  greeting ("Hi there!") needs no lookup, so the agent simply responds. (That's the
  `intro.md` quiz's point: agentic RAG can *skip* retrieval; traditional RAG can't.)

## The ingestion pipeline: chunk → embed → insert (`agentic_rag.md`)
Documents must be turned into searchable vectors before query time:
- **Chunk** — `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)`
  splits docs into overlapping pieces. Overlap keeps context from being severed at a
  boundary. Sizes are tunable for production; these are sane defaults.
- **Embed** — `NVIDIAEmbeddings(model="nvidia/llama-nemotron-embed-1b-v2",
  truncate="END")` turns each chunk into a vector; semantically similar text lands
  close together. `truncate="END"` drops overflow past the model's context limit.
  (The API key is already configured via env — it isn't passed explicitly.)
- **Insert** — `FAISS.from_documents(chunks, embeddings)` builds an **in-memory**
  vector DB (fast to spin up; fine for a workshop, not the production design).

## Retrieval + reranking (`agentic_rag.md`)
- **Similarity search:** `vectordb.as_retriever(search_type="similarity",
  search_kwargs={"k": 6})` returns the 6 nearest chunks to the query embedding.
- **Reranking:** `NVIDIARerank(model="nvidia/llama-nemotron-rerank-1b-v2")` reorders
  those candidates by true relevance to the query — embeddings get you *close*,
  reranking gets the *order* right. Combined via
  `ContextualCompressionRetriever(base_retriever=kb_retriever, base_compressor=reranker)`.
- **Expose as a tool:** `create_retriever_tool(...)` wraps the retrieval chain as the
  `company_llc_it_knowledge_base` tool; its `name`/`description` are how the agent
  decides when to call it.

## The agent (`agentic_rag.md`)
- **Model:** `ChatNVIDIA(model="nvidia/nemotron-3-super-120b-a12b", temperature=0.6,
  max_tokens=4096)` — note this is `ChatNVIDIA` (NVIDIA endpoints), not Module 1's
  `ChatOpenAI`.
- **Graph:** `create_react_agent(model, tools, prompt)` (LangGraph prebuilt) wires the
  model + tools + system prompt into a ReAct loop — no manual routing. The workshop
  notes "graphs" (dynamic, non-linear) vs "chains" (fixed, linear).
- The `AGENT` is rebuilt as tools are added (RAG → +web_search → +skills). See
  `references/exercises.md`.

## MCP — Model Context Protocol (`mcp.md`)
- An **open standard** (from Anthropic) for connecting agents to external tools/data —
  "a universal adapter." Solves tight coupling, duplication, and no-ecosystem problems
  of in-code tools.
- **Architecture:** *hosts* (apps like Claude Desktop, Cursor, or your agent),
  *clients* (protocol handlers), *servers* (expose capabilities). Three primitives:
  **tools** (callable functions), **resources** (readable data), **prompts** (templates).
- **Key idea (the quiz):** the tool's code runs **on the MCP server**, not in your
  agent and not in the LLM. Your agent discovers and calls it over the protocol.
- **In this module:** add a `web_search` tool backed by Tavily's MCP server.
  - *Remote* (`mcp.tavily.com`): `MultiServerMCPClient` with `transport: "stdio"`,
    `command: "npx"`, `args: ["-y", "mcp-remote", "https://mcp.tavily.com/mcp/?tavilyApiKey=…"]`.
    `mcp-remote` bridges a stdio client to the remote HTTP server (needs Node/`npx`).
  - *Local* (optional): run `mcp_server.py` (a Starlette + SSE MCP server wrapping
    Tavily) with `uvicorn mcp_server:app --port 8000`, connect via `transport: "sse"`,
    `url: "http://localhost:8000/sse"`.
- **Why it matters here:** it replaces Module 1's hand-written Tavily tool — "build
  once, use anywhere."

## Skills — dynamic expertise (`skills.md`)
- A **Skill** is a folder with a `SKILL.md` (YAML frontmatter `name`+`description`
  always loaded; markdown body loaded on use) — *instructions/know-how*, not tools.
- **MCP vs Skills:** MCP provides *tools to **do*** things; Skills provide
  *instructions on **how*** to do them well. Complementary: LLM (brain) + MCP
  (capabilities) + Skills (domain knowledge).
- **In this module:** `get_skill(name)` reads a `SKILL.md`; `list_available_skills()`
  lists what's in the top-level `skills/` dir (`code_review`, `technical_writing`).
  The agent loads a skill on demand (e.g. "review this code" → loads `code_review`).
- **Skills vs system prompt:** modularity, reusability, organization, versioning,
  discoverability — load only what's needed instead of bloating one giant prompt.
- *(Nice connection: this is the same Agent Skills format that powers Claude Code's
  skills — including this very tutor. Module 7 goes deeper.)*

## Observability (`running.md`)
LangSmith is auto-integrated with LangGraph (no code changes). **Tracing** = inspect
every step of a single run (best for debugging). **Monitoring** = trends across many
runs (cost, latency, quality). Requires `LANGSMITH_API_KEY`; traces land in the
`nv-devx` project (`variables.env` sets `LANGSMITH_TRACING=true`).

## Local NIM migration (`migrate.md`)
- **API Catalog** (build.nvidia.com): free, instant, huge model selection — great for
  starts/experiments. **Local NIM:** unlimited performance, control, and data privacy
  — for production.
- Migrate the LLM to a local **NIM container** (`nvcr.io/nim/nvidia/nemotron-3-nano`,
  the smaller Nemotron 3 Nano 30B-a3b that fits one GPU): NGC `docker login`, create a
  `nim-cache` volume, `docker run … --network workbench -p 8000:8000`, then repoint the
  agent: `ChatNVIDIA(base_url="http://nemotron:8000/v1", model="nvidia/nemotron-3-nano", …)`.
- Embeddings + rerank can also be moved local with a second GPU (same pattern,
  per-model `base_url`).

## Source map
- Concepts → `intro.md` (RAG), `mcp.md` (MCP), `skills.md` (Skills), `migrate.md` (NIM)
- Build/run → `agentic_rag.md`, `running.md`; code in `rag_agent.py`, `mcp_server.py`, `simple_client.py`
