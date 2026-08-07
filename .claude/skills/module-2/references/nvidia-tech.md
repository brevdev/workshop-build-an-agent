# Module 2 NVIDIA technologies — tutor reference

What each NVIDIA (and adjacent third-party) technology is and its role here. Be precise
about NVIDIA vs not.

## NVIDIA
- **Nemotron 3 Super (120B)** — `nvidia/nemotron-3-super-120b-a12b`, via **`ChatNVIDIA`**
  (temp 0.6, max_tokens 4096). The agent's reasoning LLM.
- **NVIDIA NeMo Retriever** — NVIDIA's retrieval-model family. Two are used:
  - **Embeddings:** `nvidia/llama-nemotron-embed-1b-v2` (`NVIDIAEmbeddings`, `truncate="END"`).
  - **Reranking:** `nvidia/llama-nemotron-rerank-1b-v2` (`NVIDIARerank`).
  These are the **current** ids; older `*embedqa*`/`*rerankqa*` endpoints are retired (HTTP
  410). Resource: https://developer.nvidia.com/nemo-retriever, https://build.nvidia.com.
- **NIM (NVIDIA Inference Microservices)** — the hosted catalog (default) *and* the **local
  NIM container** in the optional migrate step (`nvcr.io/nim/nvidia/nemotron-3-nano`, served
  at `http://nemotron:8000`). Resource: https://docs.nvidia.com/nim.
- **NGC** — `docker login nvcr.io` (user `$oauthtoken`) to pull the NIM container; API keys.
- **`langchain-nvidia-ai-endpoints`** — NVIDIA's official LangChain integration providing
  `ChatNVIDIA` / `NVIDIAEmbeddings` / `NVIDIARerank`.

## Third-party (NOT NVIDIA)
- **LangChain / LangGraph** — `create_react_agent` (LangGraph prebuilt); `langchain_classic`
  (text splitter, `ContextualCompressionRetriever`, `create_retriever_tool`); the `langgraph
  dev` server.
- **MCP (Model Context Protocol)** — an open standard from **Anthropic** (not NVIDIA).
  `langchain_mcp_adapters` (`MultiServerMCPClient`); `mcp-remote` (the `npx` stdio↔HTTP bridge).
- **FAISS** — Meta's vector-similarity library (the in-memory vector DB).
- **Tavily** — web search, via its hosted MCP server (default) or the local `mcp_server.py`.
- **Voila / uvicorn / Starlette** — the Secrets Manager (Voila) and the local MCP server.

> Clarifications learners ask: *"Is MCP an NVIDIA thing?"* → no, it's Anthropic's open
> standard (NVIDIA/NemoClaw use it too). *"Embedding vs rerank model?"* → embeddings
> index/search by similarity; reranking reorders the top-k by relevance — both are NeMo
> Retriever. *"Is this the same model as Module 1?"* → same LLM (Nemotron 3 Super), but M2
> uses the native `ChatNVIDIA` client instead of M1's OpenAI-compatible `ChatOpenAI`.
