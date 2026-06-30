# Module 3 Diagrams — tutor reference

Help a learner read the evaluation figures. Diagrams in `.devx/3-agent-evaluation/img/`.

## evaluation_pipeline (`evaluation_pipeline.mmd`)
- **Depicts:** the generic evaluation architecture, left→right: `Test Dataset → Agent Under
  Test → Agent Response → Evaluation Metrics → Results Storage → Analysis & Reports`.
- **Takeaway:** everything except the agent exists to *measure* the agent; the dataset feeds
  it, metrics score the output, analysis turns scores into action.

## rag_evaluation_flow (`rag_evaluation_flow.mmd`) — the RAG 2×2, as a flow
- **Depicts:** `User Question → RAG Agent → Retrieval → Retrieved Contexts → (back to agent)
  → Generated Response`, then the split: **Contexts → Context Metrics → Context Precision +
  Context Recall** (retrieval side) and **Question + Response → Generation Metrics →
  Faithfulness + Answer Relevancy** (generation side), all rolling up to an **Overall Score**.
- **Takeaway:** this is the retrieval-vs-generation split made visual — the same 2×2 from
  `concepts.md`. Context metrics judge *what was retrieved*; generation metrics judge *what
  was written*. Localize a failure to one side before fixing.

## llm_as_judge (`llm_as_judge.mmd`)
- **Depicts:** `Question + Agent Response + Context/Criteria → Judge LLM → Evaluation Prompt
  → Score + Explanation`.
- **Takeaway:** the judge needs *three* inputs (the question, the response, and the
  context/criteria) to score well — that's why eval prompts must "provide context." Maps to
  `evaluation_framework.py`'s `evaluate_*` functions (`PROMPT | judge_llm`).

## improvement_cycle (`improvement_cycle.mmd`)
- **Depicts:** a loop — `Measure → Analyze → Hypothesize → Implement → Validate → (back to
  Measure)`.
- **Takeaway:** evaluation isn't the goal; it drives the loop. "Validate" re-runs the suite
  to confirm a change helped (and didn't regress). Maps to `continuous_improvement.md`.

## Common confusions
- *Context* metrics (precision/recall) grade **retrieval**, not the answer; *Faithfulness/
  Relevancy* grade the **answer**. Mixing these up is the #1 misread (and the
  `evaluation_metrics.md` quiz).
- The Judge LLM is the *same* Nemotron model used elsewhere, run at **temperature 0** for
  consistent grading — it judges, it isn't a separate "evaluator model."
