# Module 3 Exercises — tutor guide

Module 3 has **few code blanks** and a lot of **run-and-interpret** work. This file
covers both: (1) hint ladders for the code blanks, and (2) how to help with
interpretation — the real work — *without doing it for the learner*.

**Rules:** never open/echo `evaluation_framework.answers.py` or
`evaluate_*_agent.answers.ipynb`. **Targets are for checking the learner's work and
calibrating hints; never paste or dictate them, in whole or in part** (equivalent code is
fine). L2 hints are pointers (where to look, which variable holds the value), never the
finished line. The learner's escape hatch is the in-page help block (the teaching page's
`🆘 Need some help?` for the framework; the notebook's `💡 NEED SOME HELP?` under each exercise).

---
## Part 1 — Code blanks (hint ladders)

### F1 · `evaluation_framework.py` — complete `FAITHFULNESS_PROMPT` (`running_evaluations.md`)
- **Goal:** give the judge a clear 1–5 rubric for faithfulness (apply eval-prompt
  principle #1: be specific about criteria).
- **L1:** "What does each score *mean*? Describe, in one line each, what a 5 vs a 1 looks like for 'is every claim supported by the context?'"
- **L2:** "Model it on `RELEVANCY_PROMPT` and `HELPFULNESS_PROMPT` just below in the same file:
  same 'Rate … on a scale of 1-5:' list, one line per level. Define each level by how many
  of the response's claims the context supports."
- **L3:** the page's `🆘` block has a sample rubric.
- **Common mistakes:** vague levels ("good/bad"); rating something other than grounding (that's relevancy, not faithfulness); leaving levels undefined.
- **Target:** replace `TODO: ...` with a "Rate faithfulness on a scale of 1-5:" list defining all five levels by claim support — 5 all claims fully supported by context; 4 most supported, minor unsupported details; 3 some supported, some unsupported; 2 few supported; 1 most unsupported or contradicted. Equivalent wording is fine.

### R1 · `evaluate_rag_agent.ipynb` cell 6 — load the dataset
- **Goal:** read the test-cases JSON.
- **L1:** "The file handle `f` is open — which `json` function reads a file object into Python?"
- **L2:** "Check the `json` module docs: one function reads from an open file object; its
  `s`-suffixed sibling parses a string."
- **Common mistakes:** `json.loads(f)` (that's for strings); `json.load(f.read())`.
- **Target:** `test_dataset = json.load(f)`

### R2 · `evaluate_rag_agent.ipynb` cell 11 — copy the case fields and run the agent
Two blanks in the same loop: the result-row fields, then the agent call.
- **Goal:** keep each case's question, reference and category with its result, and send the question to the KB-only `AGENT` built in the previous code cell.
- **L1:** "Each `test_case` is a dict — which keys hold the question, the reference answer and the category? And what message shape does a LangGraph agent's `invoke` expect?"
- **L2:** "Print one `test_case` (or open `data/evaluation/rag_agent_test_cases.json`): its keys
  match the row's key names. For the call, read `invoke_with_retry` in `evaluation_support.py`
  to see what kind of argument it expects (it calls it). The agent is the `AGENT` from the
  previous code cell, and it takes the same `{"messages": [...]}` user-message shape as Module 1."
- **Common mistakes:** passing the whole `test_case` as content; using the wrong key (the reference is `ground_truth`); calling `AGENT.invoke(...)` directly inside `invoke_with_retry(...)` instead of wrapping it in a `lambda`.
- **Target:** `"question": test_case["question"], "ground_truth": test_case["ground_truth"], "category": test_case["category"]`; `response = invoke_with_retry(lambda: AGENT.invoke({"messages": [{"role": "user", "content": test_case["question"]}]}))`

### R3 · `evaluate_rag_agent.ipynb` cell 13 — score with the LLM judge
- **Goal:** apply the framework's three rubrics (faithfulness / relevancy / helpfulness) to each successful answer.
- **L1:** "The framework gives you `evaluate_rag_response`, which applies the three rubrics. What three inputs does a judge need — the answer, the question, and …?"
- **L2:** "Read `evaluate_rag_response`'s signature in `evaluation_framework.py`. Each value is
  already in scope: two fields of `result`, the `context_str` joined on the line above, and the
  `judge_llm` created at the top of the cell."
- **Common mistakes:** re-creating a judge per call (pass the existing one); forgetting the context argument; grading the reference instead of `agent_response`.
- **Target:** `eval_results = evaluate_rag_response(question=result["question"], response=result["agent_response"], context=context_str, judge_llm=judge_llm)`

### R4 · cell 15 — RAGAS evaluation
- **Goal:** pass the four metrics, the prepared dataset, judge, embeddings, and conservative `RunConfig` to `evaluate`.
- **L1:** "Which metrics assess retrieval, and which assess the answer?"
- **L2:** "Everything is built earlier in the same cell: `ragas_dataset`, the four metric
  objects, `ragas_judge`, `embeddings`, and the limits recorded in `record_config(...)`
  (`max_workers`, `metric_job_timeout`, `max_retries`). Match them to `ragas.evaluate`'s
  parameters and `RunConfig`'s fields. Inspect missing values and counts afterward."
- **Common mistakes:** passing the rubric `judge_llm` instead of `ragas_judge`; omitting `run_config` (RAGAS then defaults to 16 parallel workers and 10 retries); passing metric classes instead of the instances.
- **Target:** `ragas_results = evaluate(dataset=ragas_dataset, metrics=[context_precision, context_recall, faithfulness, answer_relevancy], llm=ragas_judge, embeddings=embeddings, run_config=RunConfig(max_workers=1, timeout=600, max_retries=2))`

### R5 · cell 27 — custom actionability chain
- **Goal:** connect `custom_prompt` and `judge_llm`.
- **L1:** "Which operator composed the other prompt/model chains?"
- **L2:** "`_judge()` in `evaluation_framework.py` builds the same kind of chain; follow its
  pattern with this cell's prompt and judge. The provided parser validates the returned score."
- **Target:** `custom_chain = custom_prompt | judge_llm`

### P1 · `evaluate_report_agent.ipynb` cell 6 — load the dataset
- Same blank and ladder as R1.
- **Target:** `report_test_cases = json.load(f)`

### P2 · `evaluate_report_agent.ipynb` cell 10 — record a report case
- **Goal:** preserve the topic and expected sections in the result row; the prompt and async invocation are provided.
- **L1:** "Which fields describe the report request and its required structure?"
- **L2:** "Print one `test_case` (or open `data/evaluation/report_agent_test_cases.json`): its
  keys match the row's key names."
- **Common mistakes:** using the RAG field `question`, or dropping expected sections.
- **Target:** `"topic": test_case["topic"], "expected_sections": test_case["expected_sections"]`

### P3 · `evaluate_report_agent.ipynb` cell 12 — score report quality
- **Goal:** call `evaluate_report_quality` with the request, the report, the criteria and the actual search excerpts.
- **L1:** "Which fields of `result` describe the request, the generated report, the criteria and the evidence? The accuracy rubric needs the evidence (`source_context`)."
- **L2:** "Read `evaluate_report_quality`'s signature in `evaluation_framework.py`: every
  parameter except the judge has a same-named key in `result`, and the judge is the
  `judge_llm` created at the top of the cell."
- **Common mistakes:** omitting `source_context` (then accuracy is not applicable); passing the topic as the report.
- **Target:** `eval_results = evaluate_report_quality(topic=result["topic"], report=result["report"], expected_sections=result["expected_sections"], quality_criteria=result["quality_criteria"], source_context=result["source_context"], judge_llm=judge_llm)`

> The `generate_*_eval_dataset.ipynb` notebooks are **run-as-is** (synthetic data
> generation with NeMo Data Designer) — no blanks. If a learner is stuck there, it's a
> runtime/Data-Designer issue (see `troubleshooting.md`) or a source-review task, rather than a missing code answer.

---
## Part 2 — Helping with interpretation (the real work, no code to write)

This is where most learners want help. **Explain the concept; guide them to the
conclusion about their own data — don't state it.**

### Reading scores
- Most RAGAS metrics here use 0–1; cosine-based relevancy can be negative. Custom 1–5 rubrics are divided by 5 (valid 0.2–1.0). Ask what the metric measures and how many cases were successfully measured. A failed or not-applicable score is missing, not zero. Do not infer readiness from a universal band.

### Diagnosing a low metric
- First localize: "Is this a **retrieval** metric (context precision/recall) or a
  **generation** one (faithfulness/relevancy)?" That alone narrows the cause.
- Have them **read the judge's explanations** for the low-scoring cases (the framework
  returns explanations). Ask "what reason is the judge giving?" rather than guessing.
- Map symptom → strategy using the module's "where to look" tables (share those — they're
  teaching content), but let the learner choose and try the fix, then re-evaluate.

### The faithful-but-irrelevant trap
- If faithfulness is high but relevancy is low: "every claim is grounded, but is it
  answering the question that was asked?" Guide them to see the two are independent.

### Judge calibration
- "Pick a few responses, score them yourself on the rubric, compare to the judge. Where
  do you disagree, and why?" If misaligned, the fix is a better eval prompt / examples —
  have them reason about *what* the judge is misreading.

### Choosing improvements
- Walk the cycle (measure → analyze → hypothesize → implement → validate). For their
  specific low metric, point to the matching strategy (prompt / retrieval / model /
  architecture / data) and let them form the hypothesis and validate it by re-running.

---
## Escalation protocol
1. Ask what they've tried / what they're seeing (scores, judge explanations).
2. **L1** conceptual nudge.
3. **L2** specific pointer (function/field/where-to-look table — not the finished line).
4. **Last resort** for code blanks — the in-page help block (`running_evaluations.md`'s
   `🆘 Need some help?` for F1; the notebook's `💡 NEED SOME HELP?` for the notebook blanks).
Never paste it; never open the `.answers` files. For interpretation, never hand the
conclusion — keep asking the question that gets them there.
