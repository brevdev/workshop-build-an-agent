# Module 3 NVIDIA technologies — tutor reference

NVIDIA vs third-party for the evaluation module.

## NVIDIA
- **Nemotron judge** — the shared `judge` role selects the current model. The factory uses JSON mode, temperature 0, request pacing, and bounded retries. Temperature 0 reduces sampling variation; judge quality still needs human agreement checks. By default the judge is the same model as the `chat` agent role (Nemotron 3 Super), so self-preference is possible; `WORKSHOP_JUDGE_MODEL` selects a different judge without code changes. The report notebook checks the judge's quotations and the report's numbers in code. Each run records the actual models.
- **NeMo Data Designer** — NVIDIA's synthetic-data-generation tool, used in
  `generate_*_eval_dataset.ipynb` to build evaluation datasets (the `data-designer` package).
  Resource: build.nvidia.com.
- **NeMo Retriever embeddings** — `nvidia/nemotron-3-embed-1b` (`EMBEDDING_MODEL` in
  the framework); RAGAS uses embeddings for Answer Relevancy.
- **NeMo Agent Toolkit** and **NeMo Evaluator** — NVIDIA's production eval offerings,
  mentioned in the wrap-up as where to go next. Toolkit: github.com/NVIDIA/NeMo-Agent-Toolkit;
  Evaluator: developer.nvidia.com/nemo-evaluator.
- **NIM / NGC** — hosted inference + `NVIDIA_API_KEY`.

## Third-party (NOT NVIDIA)
- **RAGAS** — the open-source RAG-evaluation framework (`ragas` package): Context Precision,
  Context Recall, Faithfulness, Answer Relevancy. Calls NVIDIA models under the hood, but
  RAGAS itself is community-maintained.
- **HuggingFace `datasets`** — RAGAS wraps test rows in a HF `Dataset`.
- **LangSmith** (LangChain), **Arize Phoenix**, **DeepEval** — alternative
  tracing/eval frameworks named in the wrap-up; not NVIDIA.
- **LangChain** — `ChatPromptTemplate`, chains (`PROMPT | judge_llm`).

> Clarifications learners ask: *"Is RAGAS an NVIDIA thing?"* → no, it's an open-source
> framework; here it's pointed at NVIDIA models. *"Is the judge a special model?"* → no, it's
> the configured Nemotron judge with a rubric prompt and JSON output mode. *"NeMo Data
> Designer vs RAGAS?"* → Data Designer *generates* the test data; RAGAS *scores* the agent on it.
