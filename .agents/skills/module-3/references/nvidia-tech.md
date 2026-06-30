# Module 3 NVIDIA technologies — tutor reference

NVIDIA vs third-party for the evaluation module.

## NVIDIA
- **Nemotron 3 Super (120B)** — `nvidia/nemotron-3-super-120b-a12b`, used as the
  **LLM-as-a-judge** (`create_judge_llm`, **temperature 0** for consistent grading). Also
  the agent-under-test's model.
- **NeMo Data Designer** — NVIDIA's synthetic-data-generation tool, used in
  `generate_*_eval_dataset.ipynb` to build evaluation datasets (the `data-designer` package).
  Resource: build.nvidia.com.
- **NeMo Retriever embeddings** — `nvidia/llama-nemotron-embed-1b-v2` (`EMBEDDING_MODEL` in
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
> the same Nemotron Super, just run at temperature 0 with a rubric prompt. *"NeMo Data
> Designer vs RAGAS?"* → Data Designer *generates* the test data; RAGAS *scores* the agent on it.
