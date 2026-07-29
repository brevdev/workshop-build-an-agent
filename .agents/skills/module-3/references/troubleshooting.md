# Module 3 Troubleshooting — tutor reference

**Triage first.** Environment/runtime problem (give direct fixes), exercise blank
(guide — see `exercises.md`), or interpretation (a teaching moment — see `concepts.md`)?
Runtime fixes below are fair to give directly; they aren't the learning content.

## Prerequisite agents (Modules 1 & 2)
Module 3 evaluates the M1 and M2 agents, so they must be **built and importable**.
- The RAG notebook imports Module 2's *components* (`llm`, `RETRIEVER`, `RETRIEVER_TOOL`)
  and assembles its own retrieval-only agent from them; the report notebook imports the
  Module 1 `agent`. A `RuntimeError` naming an unfilled blank → that module's code is
  incomplete.
- Only Module 2's **RAG** exercises are required (`splitter`, `embeddings`, `reranker`,
  `llm`). MCP and Skills are optional for Module 3.
- **Do not tell them to strip tools out of their Module 2 agent** — that used to be the
  advice and it is no longer needed. The eval notebook never edits `rag_agent.py`; it
  builds a separate one-tool agent so faithfulness / context precision / context recall are
  measured against knowledge-base context only. Their four-tool agent keeps working in the
  Simple Agents Client.
- It's still fine to tell a stuck learner to paste `code/2-agentic-rag/rag_agent.answers.py`
  into `rag_agent.py` to get a runnable agent-under-test (the workshop says to).

## API keys
Keys load from repo-root **`secrets.env`** (gitignored). Needs **`NVIDIA_API_KEY`** (the
judge `nemotron-3-super-120b-a12b`, the embeddings, and both agents) and **`TAVILY_API_KEY`**
(the report agent's web search runs during report generation). LangSmith optional.
- **401 / auth** on the judge or agents → key missing/invalid; set it and restart the kernel.

## RAGAS
- The RAG notebook guards the import: if `ragas`/`datasets` aren't importable it sets
  `RAGAS_AVAILABLE = False` and **continues with LLM-as-judge metrics only** — so a
  missing RAGAS isn't fatal, just narrower. `ragas` and `datasets` ship in
  `requirements.txt`, so RAGAS is installed.
- **Compat shim (important):** every current `ragas` (through 0.4.x) hard-imports
  `langchain_community.chat_models.vertexai`, a path that was **removed** when
  langchain-community split into standalone packages (0.4+, which the workshop's
  langchain 1.x stack requires). Without a fix, `import ragas` raises
  `ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'`
  even though ragas is installed. The RAGAS cell registers a lightweight `sys.modules`
  stub for that unused path **before** importing ragas — that's the shim at the top of
  the cell; it must run before `from ragas import evaluate`. The workshop never uses
  VertexAI, so the stub is safe. If a learner sees the vertexai ModuleNotFoundError,
  they deleted/skipped the shim — restore it, don't "pip install ragas".
- RAGAS needs each row to have **question, answer, contexts, and ground_truth** — if
  context_recall/precision error, a field is missing/empty (often empty
  `retrieved_contexts` because the agent didn't actually retrieve).
- RAGAS calls the judge/embeddings under the hood, so it also needs the NVIDIA key and is
  **slow** (many model calls); a few minutes is normal.

## The judge
- `create_judge_llm()` uses `nvidia/nemotron-3-super-120b-a12b` at **temperature 0** for
  consistent grading — don't raise the temperature "to be creative"; that makes scores noisy.
- Judge returns a score + explanation; if scores look random, suspect the **prompt** (e.g.
  the `FAITHFULNESS_PROMPT` rubric left as the `TODO` placeholder) before blaming the model.

## Synthetic data generation (`generate_*_eval_dataset.ipynb`)
- Uses **NVIDIA NeMo Data Designer** (`data-designer` / `nemo-microservices`). If SDG
  errors or the service is unreachable, the learner can **skip it and use the pre-made
  datasets** (`data/evaluation/rag_agent_test_cases.json`, `report_agent_test_cases.json`)
  — the eval notebooks fall back to these when `synthetic_*` files are absent.
- Generated files are written as `data/evaluation/synthetic_*_test_cases.json`; the eval
  notebooks prefer those if present, else the pre-made ones.

## Long run times
- "Run Agent on Test Cases" / "Generate Reports" call the agents live (the report agent
  even web-searches per topic) — **the report eval can take ~30 minutes**. This is
  expected, not a hang; watch the per-item progress prints.

## Data paths
- Notebooks run from `code/3-agent-evaluation/` and reference `../../data/evaluation/…`.
  `FileNotFoundError` → wrong working dir, or they expected a `synthetic_*` file they
  never generated (it falls back to the pre-made file only if the code path matches).

## Interpretation confusion (teaching moments, not bugs)
- "All my scores are low" → first check the judge prompt is complete and the agent
  actually ran/retrieved (empty contexts tank RAGAS); then localize retrieval vs generation.
- "Faithfulness high, relevancy low" → the faithful-but-irrelevant trap (see `concepts.md`).
- "The judge seems too lenient/harsh" → calibration; compare to human reads on a few samples.
- "Which metric should I trust?" → none alone; combine retrieval + generation signals.
These are learning conversations — guide with questions, don't hand the conclusion.
