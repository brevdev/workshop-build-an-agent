<div class="dx-hero" data-eyebrow="MODULE 03 / 01 - CONCEPTS" data-title="Introduction to Agent Evaluation"></div>

<img src="_static/robots/study.png" alt="Understanding Evaluation" style="float:right;max-width:300px;margin:25px;" />

Building AI agents is exciting. Seeing them in action for the first time feels like magic. But as we move closer from prototypes to production, "magic" isn't enough. We need **trust**.

How do you know if your agent is actually working? Is it hallucinating? Is it rude? Is it getting better or worse as you tweak the prompts? 

<!-- fold:break -->

Manual testing ("vibe checking") can only take you so far. As your agents become more complex and handle more use cases, you need systematic ways to measure their performance, identify weaknesses, and track improvements over time. You need to treat evaluation not as an afterthought, but as a core engineering discipline.

In this module, we will transform your agent development process from an art into a science.

<!-- fold:break -->

## The Challenge of Evaluating Agents

Evaluating AI agents is harder than traditional software testing for several reasons - and a complete evaluation strategy has to account for all of them:

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>MALICIOUS BEHAVIOR</h4>Agents can act harmfully on their own or when manipulated, so evaluation needs adversarial test cases. <span class="dx-chip">TOXIC OUTPUTS</span> <span class="dx-chip">PROMPT INJECTION</span> <span class="dx-chip">ADVERSARIAL QUERIES</span></div>
  <div class="dx-cell is-wide"><h4>NON-DETERMINISM</h4>The same input can yield different valid responses - you cannot just assert on one exact expected output.</div>
  <div class="dx-cell is-wide"><h4>SUBJECTIVE QUALITY</h4>Tone, style, and helpfulness rarely have one right answer; a response can be factually correct yet unhelpful.</div>
  <div class="dx-cell is-wide"><h4>MULTI-STEP REASONING</h4>Evaluate the whole chain - an early misstep cascades into a wrong result even when later steps are sound.</div>
  <div class="dx-cell is-wide"><h4>TOOL USAGE</h4>Verify the agent chose the right tool, with correct arguments, and used the result - not just the final text.</div>
  <div class="dx-cell is-wide"><h4>CONTEXT DEPENDENCE</h4>Behavior shifts with conversation history and retrieved data, so test varied flows, not single turns.</div>
</div>

<!-- fold:break -->

## What Should We Measure?

To trust our agents, we need to measure their performance across two key dimensions: **Process** (how they got the answer) and **Outcome** (the quality of the answer itself).

When debugging a RAG agent, for example, a wrong answer could come from two places:
1. **Bad Retrieval**: The agent didn't find the relevant documents.
2. **Bad Generation**: The agent found the documents but hallucinated the answer.

We break these down into specific signals - and for a RAG agent they form a tidy 2x2:

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>CONTEXT PRECISION</h4><span class="dx-chip">RETRIEVAL</span> Are the retrieved chunks relevant - and ranked near the top?</div>
  <div class="dx-cell is-wide"><h4>CONTEXT RECALL</h4><span class="dx-chip">RETRIEVAL</span> Did we retrieve everything needed to answer?</div>
  <div class="dx-cell is-wide"><h4>FAITHFULNESS</h4><span class="dx-chip">GENERATION</span> Is every claim grounded in the context - no hallucinations?</div>
  <div class="dx-cell is-wide"><h4>ANSWER RELEVANCY</h4><span class="dx-chip">GENERATION</span> Does the answer actually address the question?</div>
</div>

<!-- fold:break -->

### Other Agents

<img src="_static/robots/wrench.png" alt="Other Agent Metrics" style="float:right;max-width:250px;margin:25px;" />

For more traditional autonomous agents (like the report generator from Module 1), we also track metrics such as:
* **Tool Usage**: Did the agent use the search tool correctly?
* **Task Completion**: Did we get a final report that meets the requirements?

We'll get a better understanding of how these metrics work in the next section, as well as get a chance to work with these metrics in the hands-on lab notebooks later in this module! 

<!-- fold:break -->

## The "Judge" Problem

In addition to what it is we should be evaluating, there's also a question of who should be the one doing the evaluating. 

If an agent writes a poem or summarizes a document, how do you write a unit test for that? Testing for `assert response == "The cat sat on the mat"` rarely works in the age of LLMs.

We generally rely on three approaches: 

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>LLM-AS-A-JUDGE</h4><span class="dx-chip is-green">PRIMARY METHOD</span> A specialized NVIDIA Nemotron model grades outputs against a rubric. Scalable and handles subjective qualities - but adds cost and latency, and can inherit the judge model's biases.</div>
  <div class="dx-cell"><h4>HUMAN EVALUATION</h4>The gold standard for subjective quality - most accurate, but slow, expensive, and not scalable. Used sparingly to grade the grader.</div>
  <div class="dx-cell"><h4>DETERMINISTIC CHECKS</h4>Code-based pass/fail (did the JSON parse? is the keyword present?). Objective and cheap, but misses nuance and valid alternatives.</div>
</div>

<!-- fold:break -->

<div class="dx-island dx-reveal">
  <p class="dx-island-title">CALIBRATING YOUR LLM JUDGE</p>
  <p>An LLM judge is only useful if it agrees with human judgment. Before trusting automated scores, <b>calibrate</b> it against human ratings on a small sample:</p>
  <ol>
    <li>Select 5-10 representative agent responses.</li>
    <li>Have a human rate each on your rubric (e.g. 1-5 for helpfulness).</li>
    <li>Run the same responses through your LLM judge.</li>
    <li>Compare: do the scores align? Where do they disagree?</li>
    <li>If alignment is poor, refine the evaluation prompt or add examples.</li>
  </ol>
  <p>Even a quick spot-check on 5 samples can reveal a judge that is too lenient, too harsh, or misreads your criteria. We'll practice this in the hands-on notebooks.</p>
</div>

<!-- fold:break -->

<div class="dx-island dx-reveal">
  <p class="dx-island-title">IN PRACTICE: A HYBRID APPROACH</p>
  <ul>
    <li><b>LLM-as-a-judge</b> to evaluate the agent's reasoning and subjective quality.</li>
    <li><b>Deterministic checks</b> to verify intermediate and final outputs are well-formed.</li>
    <li><b>Occasional human calibration</b> to keep the judge aligned with human preferences.</li>
  </ul>
</div>

<!-- fold:break -->

<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">Your IT Help Desk RAG agent gives a wrong answer. Where should you look first?</p>
  <button class="dx-quiz-opt" data-fb="Not necessarily. The wrong answer may come from bad RETRIEVAL - the agent never saw the right document. Rewriting generation prompts cannot fix a retrieval miss.">Assume it hallucinated and rewrite the system prompt</button>
  <button class="dx-quiz-opt" data-right data-fb="Right. RAG failures split into two independent causes: the agent did not find the right docs (retrieval), or it found them but answered poorly (generation). Localize before you fix.">Measure retrieval and generation separately - the fault could be in either</button>
  <button class="dx-quiz-opt" data-fb="That only helps if the cause is missing information (low context recall). If retrieval ranking or generation is the real problem, a bigger knowledge base will not move the score.">Add more documents to the knowledge base</button>
  <button class="dx-quiz-opt" data-fb="A reasonable generation tweak, but it does nothing if the real failure is retrieval - the agent never had the right context to ground on.">Lower the model temperature</button>
</div>

<!-- fold:break -->

## Your Journey in this Module

We will guide you through the following steps to build your evaluation pipeline:

<div class="dx-bento dx-reveal">
  <div class="dx-cell"><h4>01 &middot; METRICS</h4><a href="evaluation_metrics.md">Understanding Evaluation Metrics</a> - the signals we look for, like Faithfulness and Context Recall.</div>
  <div class="dx-cell"><h4>02 &middot; DATASETS</h4><a href="evaluation_data.md">Creating Evaluation Datasets</a> - build a dataset using synthetic data generation.</div>
  <div class="dx-cell"><h4>03 &middot; RUN</h4><a href="running_evaluations.md">Running Evaluations</a> - execute the pipeline on your agents and interpret the results.</div>
  <div class="dx-cell"><h4>04 &middot; IMPROVE</h4><a href="continuous_improvement.md">Continuous Improvement</a> - close the loop and make your agents smarter.</div>
</div>

Ready to turn your "vibe checks" into rigorous engineering? Let's continue to [Understanding Evaluation Metrics](evaluation_metrics.md) to learn about the tools we'll need.
