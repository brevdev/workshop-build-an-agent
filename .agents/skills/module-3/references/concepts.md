# Module 3 Concepts — tutor reference

Answer conceptual questions accurately and in the workshop's voice. For the
authoritative narrative, read the teaching pages in `.devx/3-agent-evaluation/`.
Explaining these concepts is teaching — do it freely. Interpreting the *learner's own*
scores is the exercise — guide, don't conclude.

## Why evaluation, and why it's hard (`intro_evaluation.md`)
Moving from prototype to production needs **trust**, not vibe checks — evaluation is a
core engineering discipline. Agents are harder to test than normal software:
non-determinism (many valid outputs), subjective quality (tone/helpfulness),
multi-step reasoning (early misstep cascades), tool usage (right tool, right args),
context dependence, and malicious-behavior risks (toxicity, prompt injection).

**Process vs outcome.** Measure *how* the agent got the answer and the *quality* of the
answer. For RAG, a wrong answer is either **bad retrieval** (didn't find the docs) or
**bad generation** (found them, answered poorly). **Localize before you fix.**

## The RAGAS 2×2 (`evaluation_metrics.md`)
Four RAGAS metrics, all scored **0–1**, split cleanly across retrieval vs generation:

| Metric | Phase | Question it answers |
|---|---|---|
| **Context Precision** | retrieval | Are retrieved chunks relevant — *and ranked near the top*? |
| **Context Recall** | retrieval | Did we retrieve *everything* needed to answer? |
| **Faithfulness** | generation | Is every claim grounded in the context (no hallucination)? |
| **Answer Relevancy** | generation | Does the answer actually address the question? |

**Score bands — they differ by metric type** (per `evaluation_metrics.md`). The two
**retrieval** metrics (Context Precision/Recall): Poor `<0.50` (urgent), Fair `0.50–0.69` (needs
work), Good `0.70–0.89` (acceptable), Excellent `0.90–1.00` (production-ready). The two
**generation** metrics (Faithfulness, Answer Relevancy) are **stricter**: Poor `<0.60`, Fair
`0.60–0.74`, Good `0.75–0.89`, Excellent `0.90–1.00`. So a 0.72 faithfulness is *Fair* (needs
work), not Good — never flatten one band table across all four; for a specific metric, defer to
the teaching page's per-metric table.

Per-metric detail (use to explain, not to grade the learner's data):
- **Context Precision** — signal-to-noise *with ranking*. Matters because of
  "lost in the middle": the model should see the right chunk first. Improve via
  top-k, better embeddings, reranking, metadata filtering. (Calculated as a
  rank-weighted precision@k average.)
- **Context Recall** — completeness; the system's knowledge "upper bound." Improve via
  more docs (top-k), query expansion, better chunking. (Fraction of ground-truth
  claims attributable to the retrieved contexts.)
- **Faithfulness** — a hallucination measure: fraction of answer claims supported by
  context. "An honest 'I don't know' beats a confident lie." Improve via grounding
  instructions, citations, lower temperature, a fact-check step.
- **Answer Relevancy** — is the answer on-topic for the question (regardless of
  grounding)? Improve via clearer prompts, few-shot examples, a question-understanding
  step. (Measured by generating questions from the answer and comparing to the original.)

**The faithful-but-irrelevant trap (a quiz favorite):** an answer can quote the docs
perfectly (faithfulness ≈ 1) yet never answer what was asked (low relevancy). The two
are independent — this is the single most important distinction in the module.

## Task-agent metrics (for the Report agent)
The Module 1 report agent isn't RAG, so use: **Task Completion Rate** (all requested
sections, each substantive), **Tool Usage Accuracy** (right tool, right time, good
queries), **Output Quality** (coherence/structure/accuracy via an LLM-judge rubric).
Cross-cutting for every agent: latency, cost, error rate.

## The judge problem (`intro_evaluation.md`)
Three ways to grade open-ended output:
- **LLM-as-a-judge** — *primary method here*. A Nemotron model grades against a rubric.
  Scalable, handles subjectivity; but adds cost/latency and can inherit the judge's biases.
- **Human evaluation** — the gold standard for subjective quality; accurate but slow and
  unscalable. Used sparingly "to grade the grader."
- **Deterministic checks** — code pass/fail (did JSON parse? keyword present?). Cheap and
  objective; misses nuance.
In practice: a **hybrid** — LLM judge for quality, deterministic checks for
well-formedness, occasional human calibration.

**Judge calibration** — an LLM judge is only useful if it agrees with humans. Pick 5–10
responses, have a human rate them, run the judge on the same, compare. Misalignment →
refine the eval prompt or add examples. The notebooks include a calibration-check step;
encourage the learner to actually read those samples and decide if they agree.

## Eval prompt design (`running_evaluations.md`)
Four principles for writing judge prompts: **(1)** be specific about criteria (ask for
quantifiable scores + justification); **(2)** provide context (question, output,
retrieved context, ground truth); **(3)** request structured output (JSON with score +
explanation); **(4)** include few-shot examples of high/low scores. The
`FAITHFULNESS_PROMPT` exercise is an application of principle (1).

## Datasets (`evaluation_data.md`)
Good eval data: covers diverse scenarios (common/edge/failure), includes ground truth
where possible, represents real usage, starts small, is version-controlled. The two
agents need different shapes:
- **RAG dataset** — `question` + `ground_truth` answer + expected context keywords +
  `category` (answers are short and objectively correct).
- **Report dataset** — `topic` + `expected_sections` + `quality_criteria` (long,
  variable output, so no single ground truth; score structure/content instead).
Creation strategies: **real-world** (realistic but slow/private), **synthetic / SDG**
(fast, controllable, but needs human validation and may miss edge cases), **hybrid**
(real + synthetic). The workshop uses **NVIDIA NeMo Data Designer** for SDG
(`generate_*_eval_dataset.ipynb`); pre-made datasets are provided as a fallback.

## The evaluation framework (`evaluation_framework.py`)
Shared code the notebooks import: `JUDGE_MODEL = "nvidia/nemotron-3-super-120b-a12b"`,
`EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-1b-v2"`; `create_judge_llm(temperature=0.0)`
(temp 0 = consistent grading); eval prompts `FAITHFULNESS_PROMPT` (the blank),
`RELEVANCY_PROMPT`, `HELPFULNESS_PROMPT`, `REPORT_QUALITY_PROMPT`; and metric functions
`evaluate_faithfulness/relevancy/helpfulness/report_quality` (each is `PROMPT | judge_llm`).
RAGAS is used directly in the RAG notebook (`from ragas import evaluate`).

## Continuous improvement (`continuous_improvement.md`)
The loop: **measure → analyze → hypothesize → implement → validate → repeat.** Five
strategies, matched to symptoms (these are the "where to look" tables — teaching content
you can share, but let the learner map *their* results):
1. **Prompt engineering** — low answer quality/relevancy/tone.
2. **Retrieval optimization** — low context precision/recall/faithfulness (tune k,
   chunking, metadata).
3. **Model selection** — persistent issues despite the above.
4. **Architecture changes** — validation nodes, multi-step, self-correction.
5. **Data enhancement** — add/update knowledge-base docs (lifts recall).
Then **validate** (re-evaluate; watch for regressions) and, before shipping, **A/B test**
to confirm offline gains translate to real users. Goal: continuous progress, not perfect
scores.

## Alternative frameworks (mentioned in the wrap-up)
Beyond RAGAS + custom judges: **NVIDIA NeMo Agent Toolkit** (framework-agnostic
connect/evaluate/profile), **NeMo Evaluator** (enterprise microservice, 100+ benchmarks),
**LangSmith** (tracing + datasets), **Arize Phoenix**, **DeepEval**.

## Source map
- Concepts → `intro_evaluation.md`, `evaluation_metrics.md`
- Datasets → `evaluation_data.md`; Run → `running_evaluations.md` + `evaluation_framework.py`
- Improvement → `continuous_improvement.md`
