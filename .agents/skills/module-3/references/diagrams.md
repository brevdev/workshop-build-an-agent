# Module 3 Diagrams — tutor reference

Help a learner read the evaluation figures. Diagrams in `.devx/3-agent-evaluation/img/`.

## evaluation_pipeline (`evaluation_pipeline.mmd`)
- **Depicts:** the generic evaluation architecture, left→right: `Test Dataset → Agent Under
  Test → Agent Response → Evaluation Metrics → Results Storage → Analysis & Reports`.
- **Takeaway:** everything except the agent exists to *measure* the agent; the dataset feeds
  it, metrics score the output, analysis turns scores into action.

## rag_evaluation_flow (`rag_evaluation_flow.mmd`) — the RAG 2×2, as a flow
- **Depicts:** the agent’s retrieval tool returns actual contexts to the agent. Contexts, question, and reviewed reference feed context precision/recall; contexts and response feed faithfulness; question and response feed answer relevancy. Results retain per-metric coverage rather than implying a universal overall RAGAS score.
- **Takeaway:** the same observed contexts used to answer must be used to evaluate. A second independent retrieval can measure different evidence.

## llm_as_judge (`llm_as_judge.mmd`)
- **Depicts:** `Question + Response + Observed Context/Criteria → Evaluation Prompt → Judge LLM → Validated Score + Explanation`, with invalid output recorded as a measurement error.
- **Takeaway:** `PROMPT | judge_llm` supplies instructions before the judge runs; a valid JSON score is bounded and still needs calibration.

## improvement_cycle (`improvement_cycle.mmd`)
- **Depicts:** a loop — `Measure → Analyze → Hypothesize → Implement → Validate → (back to
  Measure)`.
- **Takeaway:** evaluation isn't the goal; it drives the loop. "Validate" re-runs the suite
  to confirm a change helped (and didn't regress). Maps to `continuous_improvement.md`.

## Common confusions
- *Context* metrics (precision/recall) grade **retrieval**, not the answer; *Faithfulness/
  Relevancy* grade the **answer**. Mixing these up is the #1 misread (and the
  `evaluation_metrics.md` quiz).
- The shared `judge` role selects the configured Nemotron model, with **temperature 0**
  and JSON output mode. A separate model choice does not make its judgments objective; inspect calibration cases.
