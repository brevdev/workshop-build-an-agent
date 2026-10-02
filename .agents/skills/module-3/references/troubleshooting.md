# Module 3 Troubleshooting — tutor reference

Distinguish environment failures (give direct help), unfinished exercise blanks (guide), and interpretation (ask for evidence).

## Setup and prerequisites

Start with Workshop Health for credentials, packages, and endpoint availability. Setup cells discover the project root and load `secrets.env`; LangSmith is optional. Missing/invalid keys commonly produce HTTP 401/403. HTTP 410 can mean a retired endpoint: inspect the shared model registry rather than treating it as an exercise error.

The RAG notebook imports Module 2’s splitter, embeddings, reranker, model, retriever tool, and prompt. Its KB-only evaluation graph is separate from the four-tool app. MCP and Skills are optional for evaluation. An ellipsis-related exception generally means an unfinished blank; provider errors require separate diagnosis. Restart the kernel after editing imported Python files.

The report agent also needs Tavily. An agent failure or empty answer has a separate status and is skipped by the judge. It must not be treated as a low-quality answer.

## Judge and RAGAS

Complete the faithfulness rubric before grading. The provided judge uses JSON mode, disables reasoning for these short rubrics, and paces requests. A malformed score, missing explanation, or score outside 1–5 becomes a measurement error, not zero. A null value means no valid measurement: inspect its status and explanation. Valid low scores deserve content review; failed calls deserve runtime diagnosis. HTTP 429 means the provider is limiting requests; bounded backoff helps, but a quota limit may require waiting before another run.

The pinned RAGAS environment requires the notebook’s compatibility shim before import. RAGAS failures are saved in `ragas.json` while custom scores remain available. The notebook runs one RAGAS worker with bounded retries; many judge calls can take several minutes. Each mean is accompanied by its successful count. Do not upgrade individual packages blindly.

RAGAS needs question, answer, contexts, and reference. Contexts come from actual tool artifacts; an empty list can mean the agent did not retrieve. Do not retrieve again to fill them in. The judge uses a configured token cap and disables Nemotron 3 thinking mode for structured output. Truncated output is a measurement failure. Temperature zero reduces sampling variation but does not guarantee identical scores.

## Synthetic data and saved results

Both generators run without code blanks, but human review remains a task. RAG cases whose supporting quote is absent are saved separately for correction. A matched quote still requires checking the complete reference and any qualifiers. `reviewed_indices` records only reviews the learner actually performed.

Evaluation selects `synthetic_*_test_cases.json` only when all included cases are recorded as reviewed; otherwise it explains the fallback to the provided file. Verify the selected filename and reference review status. Run outputs are checkpointed under unique `runs/` directories; different runs no longer overwrite each other. `compare_runs` rejects different dataset hashes and omits unpaired or failed cases; also inspect coverage before drawing a conclusion.
