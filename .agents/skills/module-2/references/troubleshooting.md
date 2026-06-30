# Module 2 Troubleshooting — tutor reference

**Triage first.** Is this an **environment/runtime** problem (give direct fixes), an
**exercise** blank (guide, don't solve — see `exercises.md`), or **agent behavior** (a
teaching moment — see `concepts.md`)? Environment/runtime fixes below are fair to give
directly; they aren't the learning content.

Most Module 2 errors surface in the **`langgraph dev` terminal log** — read it with the
learner; the traceback's last frame usually points at the exact `rag_agent.py` line.

## Unfilled exercise blanks (the #1 cause)
A blank left as `...` (Python `Ellipsis`) fails when used:
- `AttributeError: 'ellipsis' object has no attribute 'split_documents'` → `splitter` (A1) unfilled.
- `'ellipsis' object is not callable` / `TypeError` around embeddings, reranker, llm, or `call_tool` → that blank (A2/A3/A4/B2) unfilled.
- `langgraph dev` fails to import the graph / "graph not found" → an unfilled blank or
  syntax error in `rag_agent.py`, or `AGENT` still `...`.
Identify *which* blank from the traceback line and **point them to it — don't fill it.**

## Running the agent (`langgraph dev`)
- Start **from the module dir**: `cd code/2-agentic-rag && langgraph dev`. The graph
  `rag_agent` and env files come from `langgraph.json`.
- It **hot-reloads** on save — after editing `rag_agent.py`, just re-test; no restart
  needed (a hard crash needs a restart).
- Reads keys from `../../secrets.env` + `../../variables.env` (per `langgraph.json`).
- If the command isn't found, the LangGraph CLI comes from `langgraph-cli[inmem]` in
  `requirements.txt`; confirm the right environment/kernel.

## Simple Agents Client (the chat UI)
- It's a Streamlit app launched from the Jupyter launcher ("Simple Agents Client").
  In its sidebar, select the **`rag_agent`** graph.
- "Can't connect" / no response → `langgraph dev` isn't running (or crashed — check its
  log), or the wrong graph is selected.

## API keys / models
- Keys load from repo-root **`secrets.env`** (gitignored). Needs **`NVIDIA_API_KEY`**
  (LLM + embeddings + rerank) and **`TAVILY_API_KEY`** (web search). LangSmith optional.
- **401 / auth** on any NVIDIA call → key missing/invalid; set it in `secrets.env`
  (https://build.nvidia.com) and restart `langgraph dev`.
- **404 / HTTP 410 on embeddings or rerank** → an out-of-date model id. The **current**
  models are `nvidia/llama-nemotron-embed-1b-v2` and `nvidia/llama-nemotron-rerank-1b-v2`
  (the older `*embedqa*` / `*rerankqa*` endpoints are retired and return 410). The repo
  already uses the current ids — if a learner changed them, restore the constants.
- Embeddings error about input length → ensure `truncate="END"` is set (A2).

## MCP web search
- **Remote (default):** uses `npx -y mcp-remote …`, so **Node/`npx` must be available**
  (the DevX-Lab container installs Node via `apt.txt` + `postBuild`). "Search failed" /
  spawn errors → `npx` missing, no network egress to `mcp.tavily.com`, or an invalid
  `TAVILY_API_KEY` in the URL. First call can be slow while `npx` fetches `mcp-remote`.
- **Local (optional, PART 2B):** run `cd code/2-agentic-rag && uvicorn mcp_server:app
  --reload --port 8000`; the agent connects via SSE at `http://localhost:8000/sse`.
  "Is the server running?" errors → the uvicorn server isn't up, or PART 2A wasn't
  swapped for PART 2B. `mcp_server.py` itself raises at startup if `TAVILY_API_KEY` is unset.

## Skills (Part 3)
- `get_skill` returning "Skill 'X' not found" → wrong skill name or `SKILLS_DIR` path.
  Available skills live in the **top-level `skills/`** dir: `code_review`,
  `technical_writing` (each is a folder with a `SKILL.md`).
- "what skills do you have?" returning nothing → `list_available_skills` (C2) still
  `...`, or `AGENT` not yet rebuilt to include the skills tools (C3).

## LangSmith observability (optional)
- Tracing/monitoring only work if `LANGSMITH_API_KEY` is set; traces land in the
  `nv-devx` project (`variables.env` sets `LANGSMITH_TRACING=true`). No key → the agent
  still runs; only the dashboard is empty. Not an error to fix unless they want tracing.

## Local NIM migration (`migrate.md`)
- **`docker login nvcr.io` fails** → the NGC/NVIDIA key is wrong; username must be the
  literal `$oauthtoken`, password is `$NVIDIA_API_KEY` via `--password-stdin`.
- **Container slow / seems stuck** → first run downloads the model into the `nim-cache`
  volume; wait for `Application startup complete`. Needs a GPU (`--gpus 1`) and the host
  docker socket (provided by the workshop's `/var/host-run/` mount).
- **Agent can't reach the NIM** → use `base_url="http://nemotron:8000/v1"` (the
  container name resolves only on the shared `--network workbench`); `localhost` won't
  work from the agent container. Include `/v1`; set `model="nvidia/nemotron-3-nano"`.
- **Out of memory / no GPU** → the Nano (30B-a3b) targets a single GPU; on a constrained
  box, staying on the hosted API Catalog model is fine — the migration is optional.

## Agent behavior (teaching moments, not bugs)
- **Retrieves on a greeting / always retrieves** → discuss agentic vs traditional RAG;
  the model *should* be free to skip retrieval. Check the system prompt and the trace.
- **Won't use web search for current info** → the agent only got `web_search` after the
  MCP section; confirm `AGENT` was rebuilt (B3) and the tool is wired.
- **Wrong/missing `[KB]` vs `[Web]` citation** → the system prompt asks for citations;
  inspect a LangSmith trace to see which tool actually fired.
- **Weak/irrelevant retrieval** → talk through chunking (size/overlap) and reranking;
  this previews Module 3 (evaluation). Treat as a tuning discussion, not a bug.
