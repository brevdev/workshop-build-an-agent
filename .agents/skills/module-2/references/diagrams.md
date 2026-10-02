# Module 2 Diagrams — tutor reference

The figures form a deliberate **progression** (plain LLM → traditional RAG → agentic RAG)
plus retrieval-chain detail. Diagrams in `.devx/2-agentic-rag/img/`.

## The progression (`intro.md`)
1. **basic_llm** (`basic_llm_dark.svg`) — `Prompt → LLM → Response`. A plain call: no
   outside lookup shown; the prompt itself may contain fresh context.
2. **basic_rag** (`basic_rag_dark.svg`) — `Prompt → Embedding → Vector DB Search →
   Reranking → LLM → Response`. **Traditional RAG**: the retrieval chain *always* runs
   before the LLM. The path is fixed; the model has no say in whether to retrieve.
3. **react_agent** (`react_agent_dark.svg`) — the Module 1 ReAct loop (LLM ↔ tools until done).
4. **agentic_rag** (`agentic_rag_dark.svg`) — the ReAct loop where a **tool call routes
   into the Retrieval Chain**, whose reranked chunks return through the tool to the LLM. The model *decides when* to retrieve. **This is the module's
   payoff:** retrieval is a tool, not a mandatory step (a greeting → no retrieval).

## Retrieval-chain detail (`agentic_rag.md`)
- **simple_retrieval_chain** (`simple_retrieval_chain_dark.svg`) — `Embedding → Vector DB
  Search`. The basic retriever (embed the query, FAISS similarity, k=6) → code `kb_retriever`.
- **retrieval_chain** (`retrieval_chain_dark.svg`) — `Embedding → Vector DB Search →
  Reranking`. Adds the reranker that reorders by relevance → code `RETRIEVER`
  (`ContextualCompressionRetriever` = `kb_retriever` + `NVIDIARerank`), exposed to the agent
  via `create_retriever_tool`.

## What each node represents
- *Embedding Model* = `NVIDIAEmbeddings` (`nemotron-3-embed-1b`): text → vector.
- *Vector DB Search* = FAISS similarity over the ingested chunks.
- *Reranking Model* = `NVIDIARerank` (`llama-nemotron-rerank-vl-1b-v2`): reorders candidates by
  estimated relevance (evaluate whether the new ordering helps).
- *LLM* = `ChatNVIDIA` (Nemotron 3 Super).

## Common confusions
- basic_rag "always retrieves" vs agentic_rag "retrieves when the model chooses" — that
  contrast *is* the module thesis (and the `intro.md` quiz).
- The retrieval chain is the **same** in traditional vs agentic RAG; what changes is **who
  triggers it** — a fixed pipeline vs the agent calling it as a tool.
- Reranking ≠ embedding: two different NeMo Retriever models doing two different jobs.
