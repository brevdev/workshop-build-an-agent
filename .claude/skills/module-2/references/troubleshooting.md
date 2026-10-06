# Module 2 Troubleshooting — tutor reference

**Triage first.** Is this an **environment/runtime** problem (give direct fixes), an
**exercise** blank (guide, don't solve — see `exercises.md`), or **agent behavior** (a
teaching moment — see `concepts.md`)? Environment/runtime fixes below are fair to give
directly; they aren't the learning content.

Most Module 2 errors surface in the **`langgraph dev` terminal log** — read it with the
learner; the traceback's last frame usually points at the exact `rag_agent.py` line.

## Unfilled exercise blanks (the #1 cause)
`python code/workshop_support/blanks.py 2` lists every blank still left in `rag_agent.py`.
A blank left as `...` (Python `Ellipsis`) fails where it is first used. PART 1 blanks fail
when `langgraph dev` imports the file, in file order:
- `AttributeError: 'ellipsis' object has no attribute 'split_documents'` → `splitter` (A1).
- `AttributeError: 'ellipsis' object has no attribute 'embed_documents'` → `embeddings` (A2);
  raised by `FAISS.from_documents` after the `retry` helper's three attempts (a few seconds).
- `ValidationError ... ContextualCompressionRetriever` / `base_compressor` / `input_value=Ellipsis`
  → `reranker` (A3).
- `AttributeError: 'ellipsis' object has no attribute 'bind_tools'` → `llm` (A4), raised by
  `create_react_agent`.
- `ValueError: Variable 'AGENT' in module '…rag_agent.py' is not a Graph or Graph factory
  function` → `AGENT` still `...` (A5/B3/C3).

Tool blanks do **not** raise; the agent receives a tool result instead:
- `MCP_CONFIG = ...` (B1) → `web_search` returns **"Search failed (TypeError). Check the
  Tavily key and Workshop Health."** Its `try/except` catches everything, so there is no
  traceback in the log; check the blank before the key.
- `result = ...` (B2) with a working connection → the same message with `(AttributeError)`.
  Connection or credential failures produce the same message format too, so read the
  exception name and rule out the blanks first.
- `get_skill` / `list_available_skills` still `return ...` (C1/C2) → the tool result is the
  text `Ellipsis`.
Identify *which* blank from the traceback line or tool result and **point them to it — don't fill it.**

## Running the agent (`langgraph dev`)
- Start **from the module dir**: `cd code/2-agentic-rag && langgraph dev`. The graph
  `rag_agent` and env files come from `langgraph.json`.
- It **hot-reloads** on save — after editing `rag_agent.py`, just re-test; no restart
  needed (a hard crash needs a restart).
- Reads keys from `../../secrets.env` (the `env` entry in `langgraph.json`; `rag_agent.py`
  also calls `load_secrets()`).
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
  models are `nvidia/nemotron-3-embed-1b` and `nvidia/llama-nemotron-rerank-vl-1b-v2`
  (the older `*embedqa*` / `*rerankqa*` endpoints are retired and return 410). The repo
  already uses the current ids — if a learner changed them, restore the constants.
- Embeddings error about input length → ensure `truncate="END"` is set (A2).

## MCP web search
- **Remote (default):** direct `streamable_http` to `https://mcp.tavily.com/mcp/`,
  with the key in the Authorization header. Check network egress, the key in
  `secrets.env`, and Workshop Health. Do not print headers or put the key in a URL.
- **Local (optional, PART 2B):** run `cd code/2-agentic-rag && uvicorn mcp_server:app
  --reload --port 8000`; the agent connects via SSE at `http://localhost:8000/sse`.
  "Is the server running?" errors → the uvicorn server isn't up, or PART 2A wasn't
  swapped for PART 2B. `mcp_server.py` itself raises at startup if `TAVILY_API_KEY` is unset.

## Skills (Part 3)
- `get_skill` returning "Skill 'X' not found" → wrong skill name or `SKILLS_DIR` path.
  Available skills live in the **top-level `skills/`** dir: `code-review`,
  `technical-writing` (each is a folder with a `SKILL.md`).
- "what skills do you have?" returning no skill names → `list_available_skills` (C2) still
  `...` (its tool result is the text `Ellipsis`), or `AGENT` not yet rebuilt to include the
  skills tools (C3).

## LangSmith observability (optional)
- Tracing/monitoring only work if `LANGSMITH_API_KEY` is set; traces land in the
  `nv-devx` project (`variables.env` sets `LANGSMITH_TRACING=true`). No key → the agent
  still runs; only the dashboard is empty. Not an error to fix unless they want tracing.

## Local NIM migration (`migrate.md`)
- **Missing key / registry login fails** → save the key in Workshop Secrets Manager,
  then run `python code/2-agentic-rag/nim_setup.py --check` from `/project`. The helper
  loads `secrets.env`; a new terminal does not inherit notebook environment changes.
  It passes the key through stdin/environment, not command arguments. If the saved
  key is present but registry access is denied, check its NGC permissions.
- **Driver preflight fails** → the pinned NIM 2.0.13 image uses CUDA 13. On data-center
  GPUs (A100, H100, L40S, …) with an older driver (R535+), the helper adds the image's CUDA
  forward-compatibility libraries automatically (tested on an A100 with R565). Other GPUs
  need an R580+ driver; do not change host drivers from the workshop. The hosted path
  remains available.
- **"Not enough disk space" / "needs at least 63 GB of GPU memory"** → the default BF16
  profile on an A100 needs about 64 GB of downloads plus the 32 GB image. Rerun with
  `--profile nvfp4` (about 19 GB, 21 GB of GPU memory; emulated and not NIM-validated before
  Blackwell, but the smoke test checks tool calling), or free disk (e.g. the Module 4
  merged model in `code/4-agent-customization/outputs/`).
- **"Only N GB of GPU memory is free"** → the NIM reserves 80% of the GPU. Shut down
  other notebook kernels (Kernel > Shut Down Kernel), especially Module 4 training.
- **Container already exists** → `python code/2-agentic-rag/nim_setup.py --stop` removes it
  (keeps the image and model cache); `--teardown` removes everything for a clean retry.
- **Container slow / seems stuck** → first run downloads the model into the `nim-cache`
  volume; wait for `Application startup complete` (about 3 minutes once downloaded). If the
  log ends with `driver too old` or CUDA error 804, the forward-compatibility path does not
  support this GPU: the host needs an R580+ driver. Needs a GPU (`--gpus 1`) and the host
  docker socket (provided by the workshop's `/var/host-run/` mount).
- **Plain chat works, but agent returns an automatic-tool-choice HTTP 400** → use the
  pinned launch in `nim_setup.py`, including `--enable-auto-tool-choice`,
  `--tool-call-parser qwen3_coder`, and `--reasoning-parser nemotron_v3`.
  Run `python code/2-agentic-rag/nim_smoke_test.py`: it verifies a real tool call,
  sends back a newly generated result with its matching ID, and checks the final answer.
  A chat-only HTTP 200 is insufficient. Visible `<think>`/tool markup also fails this check.
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
- **Wrong/missing `[KB:source_id]` vs `source URLs` citation** → the system prompt asks for citations;
  inspect a LangSmith trace to see which tool actually fired.
- **Weak/irrelevant retrieval** → talk through chunking (size/overlap) and reranking;
  this previews Module 3 (evaluation). Treat as a tuning discussion, not a bug.
