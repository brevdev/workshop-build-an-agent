# Module 3 Quizzes — tutor deep-dive

Richer "Check Your Understanding" feedback than the in-page two-liner. Encourage an attempt
first; then explain the answer, the principle, why each distractor is tempting, and how to
go deeper. (These quizzes are conceptual — fair game to explain fully once engaged.)

## `intro_evaluation.md` — "Your RAG agent gives a wrong answer. Where to look first?"
- **Correct:** *Measure retrieval and generation separately — the fault could be in either.*
- **Why:** a RAG failure has two independent causes — the agent never found the right docs
  (**retrieval**), or it found them but answered poorly (**generation**). **Localize before
  you fix.**
- **Distractors:** *assume hallucination, rewrite the prompt* → can't fix a retrieval miss;
  *add more docs* → only helps if the cause is low recall; *lower temperature* → a generation
  tweak that does nothing if retrieval is the problem.
- **Principle:** process vs outcome; the retrieval/generation split (`concepts.md`).
- **Go deeper:** have them look at one low-scoring case and decide, from the retrieved
  contexts, which side failed.

## `evaluation_metrics.md` — "A faithful-but-off-topic answer: which metric flags it?"
- **Correct:** *Answer Relevancy.*
- **Why:** Faithfulness only checks that claims are **grounded**; it says nothing about
  whether the answer is **on-topic**. An answer can quote the docs perfectly (faithfulness ≈
  1) yet never address the question (low relevancy). They're independent axes.
- **Distractors:** *Faithfulness/hallucination* → no, every claim is quoted, so faithfulness
  is high; *Context Precision* → grades the retrieved docs, not the answer; *"a faithful
  answer is always good"* → the core misconception this quiz exists to break.
- **Principle:** the **faithful-but-irrelevant trap** — the single most important distinction
  in the metrics (`concepts.md`).
- **Go deeper:** ask them to imagine a response that's the opposite (relevant but unfaithful)
  and which metric catches *that*.

## `evaluation_data.md` — "You synthetically generated 500 test cases. What matters most?"
- **Correct:** *Have a human validate a sample — synthetic data can miss edge cases and
  inherit the generator's biases.*
- **Why:** SDG's strength is speed/coverage; its risk is **unverified realism**. Trusting it
  blind means your eval may not reflect real users.
- **Distractors:** *use as-is* → the trap; *discard, only real data is trustworthy* → too far
  (real data is slow/private/often absent — hence the hybrid approach); *generate 500 more* →
  volume doesn't fix unvalidated quality.
- **Principle:** real vs synthetic vs hybrid; "validate a sample" (`concepts.md` → Datasets).
- **Go deeper:** connect to Module 4, where SDG (NeMo Data Designer) generates *training*
  data — the same "validate before you trust it" caution applies.
