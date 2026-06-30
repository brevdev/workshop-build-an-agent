# Module 3 Exercises — tutor guide

Module 3 has **few code blanks** and a lot of **run-and-interpret** work. This file
covers both: (1) hint ladders for the code blanks, and (2) how to help with
interpretation — the real work — *without doing it for the learner*.

**Rules:** never paste a target; never open/echo `evaluation_framework.answers.py` or
`evaluate_*_agent.answers.ipynb`. Targets below are for *your* calibration; the
learner's escape hatch is the teaching page's `🆘 Need some help?` block.

---
## Part 1 — Code blanks (hint ladders)

### F1 · `evaluation_framework.py` — complete `FAITHFULNESS_PROMPT` (`running_evaluations.md`)
- **Goal:** give the judge a clear 1–5 rubric for faithfulness (apply eval-prompt
  principle #1: be specific about criteria).
- **L1:** "What does each score *mean*? Describe, in one line each, what a 5 vs a 1 looks like for 'is every claim supported by the context?'"
- **L2:** "Anchor the ends and middle: 5 = all claims supported; 3 = some supported, some not; 1 = mostly unsupported/contradicted. Fill 4 and 2 between."
- **L3:** the page's `🆘` block has a sample rubric.
- **Common mistakes:** vague levels ("good/bad"); rating something other than grounding (that's relevancy, not faithfulness).
- **Target:** a 1–5 scale from "all claims fully supported by context" (5) down to "most claims unsupported or contradicted" (1).

### R1 · `evaluate_rag_agent.ipynb` cell 6 — load the dataset
- **Goal:** read the test-cases JSON.
- **L1:** "The file handle `f` is open — which `json` function reads a file object into Python?"
- **L2:** "`json.load(f)`."
- **Common mistakes:** `json.loads(f)` (that's for strings); `json.load(f.read())`.
- **Target:** `test_dataset = json.load(f)`

### R2 · `evaluate_rag_agent.ipynb` cell 11 — run the agent on each test case
- **Goal:** send the test case's question to the agent.
- **L1:** "Each `test_case` is a dict — which field holds the user's question? Pass that as the message content."
- **L2:** "`{'role': 'user', 'content': test_case['question']}`."
- **Common mistakes:** passing the whole `test_case`; wrong field name (it's `question`).
- **Target:** `"content": test_case["question"]`

### R3 · `evaluate_rag_agent.ipynb` cell 13 — score with the LLM judge
- **Goal:** call the framework's metric function(s) on each response (faithfulness / relevancy / helpfulness).
- **L1:** "The framework gives you `evaluate_faithfulness`, `evaluate_relevancy`, `evaluate_helpfulness`. What three inputs does a judge need — the answer, the question, and …?"
- **L2:** "Pass the agent's response, the question, and the joined `context_str`; reuse the `judge_llm` you created. Check the function signatures in `evaluation_framework.py`."
- **Common mistakes:** re-creating a judge per call (pass the existing one); forgetting the context argument.
- **Target:** calls to the `evaluate_*` functions with `(response, question/context, judge_llm=judge_llm)` per their signatures.

### P1 · `evaluate_report_agent.ipynb` cell 6 — load the dataset
- Same as R1: `report_test_cases = json.load(f)`.

### P2 · `evaluate_report_agent.ipynb` cell 10 — generate a report per topic
- **Goal:** invoke the **async** Module 1 agent on each topic.
- **L1:** "It's the report agent from Module 1 — async. Which field is the report subject, and how do you ask the agent to write about it?"
- **L2:** "`await agent.ainvoke({'messages': [{'role':'user','content': <a request referencing test_case['topic']>}]})`."
- **Common mistakes:** forgetting `await`/`.ainvoke`; using `test_case['question']` (report cases use `topic`).
- **Target:** an `await agent.ainvoke(...)` whose message content asks for a report on `test_case["topic"]`.

### P3 · `evaluate_report_agent.ipynb` cell 12 — score report quality
- **Goal:** call `evaluate_report_quality` with the right fields.
- **L1:** "The TODO hint lists what `result` contains: `topic`, `report`, `expected_sections`, `quality_criteria`. Which does the report-quality judge need?"
- **L2:** "`evaluate_report_quality(report=result['report'], expected_sections=result['expected_sections'], …)` — confirm the signature in `evaluation_framework.py`."
- **Target:** `evaluate_report_quality(...)` populated from the `result` fields.

> The `generate_*_eval_dataset.ipynb` notebooks are **run-as-is** (synthetic data
> generation with NeMo Data Designer) — no blanks. If a learner is stuck there, it's a
> runtime/Data-Designer issue (see `troubleshooting.md`), not an exercise.

---
## Part 2 — Helping with interpretation (the real work, no code to write)

This is where most learners want help. **Explain the concept; guide them to the
conclusion about their own data — don't state it.**

### Reading scores
- All RAGAS scores are **0–1**, but bands differ by metric type (per `evaluation_metrics.md`):
  **retrieval** (precision/recall) — Poor `<0.50` / Fair `0.50–0.69` / Good `0.70–0.89` / Excellent `0.90+`;
  **generation** (faithfulness/relevancy) is stricter — Poor `<0.60` / Fair `0.60–0.74` / Good `0.75–0.89` / Excellent `0.90+`.
  Ask: "Which band is your score in for *that* metric, and what does it imply about readiness?" — let them place it.

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
3. **L2** specific pointer (function/field/where-to-look table).
4. **Last resort** for code blanks — the teaching page's `🆘 Need some help?` block.
Never paste it; never open the `.answers` files. For interpretation, never hand the
conclusion — keep asking the question that gets them there.
