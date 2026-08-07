# Module 1 Quizzes — tutor deep-dive

Use this to give richer "Check Your Understanding" feedback than the in-page two-liner. If
the learner hasn't attempted the quiz yet, encourage a guess first (the struggle is the
learning); once they've engaged, explain the correct answer, the underlying principle, why
each distractor is *tempting* but wrong, and how to go deeper.

## `why_agents.md` — "Which task is the best fit for an agent?"
- **Correct:** *Investigate a reported bug by searching docs, checking incident reports,
  and writing a likely root cause.*
- **Why:** an agent earns its overhead only when the path is **dynamic** — here the steps
  vary per bug, pull from several sources, and each depends on the last. That's the "the
  model chooses the path" criterion.
- **Distractors (the misconception each encodes):**
  - *Sort tickets into 3 buckets* → one fixed classification = a single LLM call; the
    reasoning loop only adds latency/cost.
  - *Condense an email to bullets* → fixed input→output = a workflow (chain), not an agent.
  - *Translate a block of text* → one deterministic transform; reaching for an agent is
    over-engineering.
- **Principle:** single-call vs workflow vs agent = *"who decides the path, and does it
  vary?"* (`concepts.md` → "the three stages").
- **Go deeper:** ask the learner to classify one of *their own* tasks against the criterion.

## `introduction_to_agents.md` — "Your agent decides to use the add tool. What happens next?"
- **Correct:** *Your code reads the request, runs the function, appends the result to
  memory, then calls the model again.*
- **Why:** "tool calling" is a misnomer. The model only **emits a structured request**
  (tool name + arguments); your routing layer executes it and feeds the result back. That
  request → execute → observe cycle *is* the ReAct loop.
- **Distractors:**
  - *The model runs it internally* → the model never executes code; it can't.
  - *It runs automatically because it's in the schema* → the schema is "the menu, not the
    kitchen" — listing a tool only tells the model it exists.
- **Principle:** the single most important Module 1 idea. It's exactly what the learner
  implements by hand in `intro_to_agents.ipynb` (Part 4: parse the tool call → execute →
  append a `tool` message → loop).
- **Go deeper:** if they've done the from-scratch notebook, connect this back to cells
  21/24/27; if not, it's a great reason to do it.
