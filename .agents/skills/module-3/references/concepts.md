# Module 3 Concepts — tutor reference

Explain concepts freely. Interpreting the learner’s own scores is the exercise: guide them to inspect evidence and form a conclusion. Teaching pages live in `.devx/3-agent-evaluation/`.

## What evaluation measures

Evaluate both the process (tool choices, arguments, retrieved evidence, failures) and the answer. A poor answer can originate in retrieval, generation, a flawed reference, or the evaluator itself. LLM judgments are measurements with limitations, not ground truth.

| Metric | Main question |
|---|---|
| Context precision | Are useful retrieved chunks ranked ahead of irrelevant chunks? |
| Context recall | Are the reference answer’s claims supported by retrieved contexts? |
| Faithfulness | Are the answer’s claims supported by its actual contexts? |
| Answer relevancy | Does the answer align with the question? |

RAGAS context precision is rank-sensitive average precision. Labels `[1, 0, 0]` can score 1.0: trailing irrelevant chunks do not reduce it. It is not the fraction of relevant documents. Context recall depends on a correct reference. Faithfulness does not prove the source is true or the answer is complete. Answer relevancy is estimated by generating questions from the answer and comparing them with the original question.

An answer may be faithful but irrelevant: it can quote a source accurately while answering a different question. Inspect both dimensions.

## Scales, missing data, and readiness

Context precision, recall, and faithfulness range from 0–1; cosine-based answer relevancy can be negative. Custom 1–5 rubric scores are divided by 5, so valid normalized values range from 0.2 to 1.0. These are different measures despite similar names. No universal score cutoff establishes production readiness. Read means with sample sizes, successful-measurement counts, failures, and the task’s risks.

`EvaluationResult` has `status` (`ok`, `error`, or `not_applicable`) and a nullable score. Agent failures and empty answers are not graded. Judge/format failures remain null, and incomplete applicable metrics prevent an aggregate. With no retrieved context, custom faithfulness is not applicable; inspect retrieval coverage separately. Strict parsing accepts JSON or one JSON fence with a finite numeric score from 1 to 5 and a nonempty explanation.

## Evidence and provenance

The RAG evaluation reuses Module 2’s model, retriever tool, and `SYSTEM_PROMPT`, with only the KB tool enabled. It extracts actual tool artifacts, including query rewrites and repeated calls. It never retrieves again to manufacture evaluation contexts. `[KB:source_id]` labels resolve to observed chunks; citation validity does not establish claim support.

The report rubric measures structure, content, coverage, writing, and support against the actual Tavily excerpts. The historical `accuracy` key means evidence support, not external factual verification. Without excerpts that dimension is not applicable.

## Judge calibration and datasets

Humans and LLM judges both need clear rubrics and agreement checks. Independent human ratings across a varied sample help reveal bias and inconsistency. Reviewing one to three examples is a smoke check, not proof of calibration. Temperature zero reduces sampling variation but does not guarantee reproducibility.

RAG SDG gives the full source article to both question and proposed-reference generation. It requests a verbatim supporting quote, checks matching wording while ignoring Markdown decoration and whitespace, and saves source filenames/hashes and review status. That check does not establish entailment; inspect each accepted reference for invented steps or missing qualifications. Report SDG generates tasks and criteria, not verified facts. Both generators require human review. Pre-made datasets are available as a fallback.

## Run records and improvement

`workshop_support.get_model` supplies agent, judge, embedding, and reranking IDs; `load_secrets` loads repo-root credentials. Notebook setup discovers the project root instead of assuming a working directory.

Each evaluation saves a unique `runs/<kind>-<id>/` directory with a dataset hash, configuration, package versions, results, and optional RAGAS/custom/human-review artifacts. `compare_runs` requires the same dataset and pairs cases graded successfully in both runs. Review its configuration differences and failure counts. Search results and models may vary even when configuration is unchanged.

Follow measure → analyze → hypothesize → implement → validate. Change one component, restart the kernel after editing imported modules, rerun the same dataset, and inspect regressions and variability. Broader deployment claims need broader evidence.
