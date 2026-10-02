<div class="dx-hero" data-eyebrow="MODULE 03 / 02 - METRICS" data-title="Understanding Evaluation Metrics" data-meta="READ::25 min|CONCEPTS::5+"></div>

<img src="_static/robots/datacenter.png" alt="Metrics and Data" style="float:left;max-width:250px;margin:25px;" />

Now that we understand why evaluation is important, let's dive into the specific metrics we can use to measure agent performance. Different types of agents require different evaluation approaches, so we'll explore metrics for both RAG systems and general-purpose agents.

<!-- fold:break -->

**LLM-as-a-judge**: One of the most powerful techniques for evaluating AI agents is using another LLM to judge the quality of outputs, allowing us to evaluate subjective qualities like helpfulness, coherence, and relevance at scale. 

Traditional deterministic metrics like string or keyword matching don't work well for evaluating natural language outputs. Human review can capture nuance, but requires clear rubrics and agreement checks and is expensive to scale.

LLM-as-a-judge provides a neat middle ground. 

<!-- fold:break -->

## Evaluating RAG Agents

<img src="_static/robots/assembly.png" alt="RAG Components" style="float:right;max-width:300px;margin:25px;" />

The IT Help Desk agent you built in Module 2 is a Retrieval Augmented Generation (RAG) system. RAG agents have two distinct components that need evaluation:

1. **Retrieval Quality**: How well does the agent find relevant information?
2. **Generation Quality**: How well does the agent use that information to answer questions?

Let's explore the key metrics for each.

<!-- fold:break -->

## RAGAS Metrics Deep Dive

RAGAS provides a comprehensive framework for evaluating RAG systems. Each metric addresses a specific aspect of quality - and together they map onto the same retrieval/generation split from the last lesson:

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>CONTEXT PRECISION</h4><span class="dx-chip">RETRIEVAL</span> Are the retrieved chunks relevant - and ranked near the top?</div>
  <div class="dx-cell is-wide"><h4>CONTEXT RECALL</h4><span class="dx-chip">RETRIEVAL</span> Did we retrieve everything needed to answer?</div>
  <div class="dx-cell is-wide"><h4>FAITHFULNESS</h4><span class="dx-chip">GENERATION</span> Is every claim grounded in the context - no hallucinations?</div>
  <div class="dx-cell is-wide"><h4>ANSWER RELEVANCY</h4><span class="dx-chip">GENERATION</span> Does the answer actually address the question?</div>
</div>

<div class="dx-island dx-reveal">
  <p class="dx-island-title">READ SCORES WITH THEIR DEFINITIONS AND COVERAGE</p>
  <p>Context precision, recall, and faithfulness range from 0–1; cosine-based answer relevancy can be negative. The notebook’s custom 1–5 rubrics are divided by 5, so their valid range is 0.2–1.0. A failed measurement is missing, not zero. There are no universal “production-ready” cutoffs: validate task-specific thresholds against reviewed examples, and report sample counts and failure rates.</p>
</div>

<!-- fold:break -->

### Context Precision

**Definition**: Rank-sensitive average precision: are useful retrieved chunks ranked before irrelevant chunks? It is not the fraction of retrieved documents that are relevant.

**Why it matters**: It rewards placing relevant chunks early. However, irrelevant chunks after the last relevant chunk do not lower this metric. For relevance labels `[1, 0, 0]`, average precision is still 1.0; inspect context size and relevance separately. See the [RAGAS definition and examples](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/).

Crucially, LLMs can suffer from the "Lost in the Middle" phenomenon where relevant information buried in the middle of a context window may be ignored. This is why **ranking** matters: the model should see the right data first. 

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-1">How is this calculated?</button>
<div id="aside-em-1" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-1" popovertargetaction="hide" aria-label="Close">×</button>

RAGAS uses an LLM to determine if each retrieved chunk is relevant or irrelevant to answering the question. It then calculates precision at each position (precision@k) in the ranked results and averages them. The formula weighs higher-ranked relevant documents more heavily:

```
Context Precision = (Σ (Precision@k × relevance_k)) / Total number of relevant items in retrieved contexts
```

where `relevance_k` is the relevance indicator (0 or 1) for the item at rank `k` and: 

```
Precision@k = true positives @ k / (true positives @ k + false positives @k) 
```

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-2">See a worked example</button>
<div id="aside-em-2" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-2" popovertargetaction="hide" aria-label="Close">×</button>

Consider a sample RAG query in which we have retrieved 2 relevant chunks from ``K=3`` total retrieved chunks. First, label each of the 3 chunks as either relevant or irrelevant for the query. Let's assume relevant-irrelevant-relevant ordering for this exercise. Then: 

* Precision@1 = 1/(1 + 0) = 1.0
* Precision@2 = 1/(1 + 1) = 0.5
* Precision@3 = 2/(2 + 1) = 0.67

The final Context Precision is the average of the individual Precision@k values, ignoring irrelevant retrieved chunks. 

* Rank 1: relevance_1 x Precision@1 = 1 x 1.0 = 1.0
* Rank 2: relevance_2 x Precision@2 = 0 x 0.5 = 0.0
* Rank 3: relevance_3 x Precision@3 = 1 x 0.67 = 0.67

So Context Precision = (1.0 + 0.0 + 0.67) / (1 + 0 + 1) = **0.83**. 

Note that this context precision value is not a perfect 1.0 score. Why? Because we can actually improve the precision if the third retrieved chunk were instead ranked second, ahead of the irrelevant chunk. This would represent the most ideal retrieval arrangement, where all relevant chunks are ranked ahead of irrelevant ones for any particular value of K.

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-3">How do I read the score?</button>
<div id="aside-em-3" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-3" popovertargetaction="hide" aria-label="Close">×</button>

**Score interpretation**: Higher values mean relevant retrieved chunks tend to precede irrelevant ones. A score of 1.0 does not imply that every retrieved chunk is relevant or that every needed fact was retrieved.

**Optimization Strategies**
- Fine-tune your retrieval parameters (similarity threshold, top-k)
- Improve embedding model quality
- Add reranking as a second stage
- Use metadata filtering to narrow search scope

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-4">See an example</button>
<div id="aside-em-4" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-4" popovertargetaction="hide" aria-label="Close">×</button>

```
Question: "How do I reset my password?"
Retrieved contexts: 
    [Password reset guide, VPN setup, Password reset FAQ, Printer setup]
```

Here the relevant chunks are at ranks 1 and 3, with an irrelevant "VPN setup" wedged in at rank 2. Applying the formula above — Precision@1 = 1.0 and Precision@3 = 2/3 — Context Precision = (1.0 + 0.67) / 2 = **0.83**. It falls short of a perfect 1.0 because a relevant chunk was ranked *behind* an irrelevant one — not simply because irrelevant documents appear (context precision is rank-aware).

Better retrieval: [Password reset guide, Password reset FAQ, Account security, Login procedures] ranks both relevant chunks ahead of any noise and scores a perfect **1.0**.

</div>
</div>

<!-- fold:break -->

### Context Recall

**Definition**: How much of a reviewed reference answer is supported by the retrieved contexts. It measures coverage of that reference.

**Why it matters**: Missing evidence limits an answer grounded in those sources. Check whether low recall reflects missing retrieval, an unsuitable reference, or an incorrect judge decision.

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-5">How is this calculated?</button>
<div id="aside-em-5" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-5" popovertargetaction="hide" aria-label="Close">×</button>

Given a *ground truth* answer, RAGAS uses an LLM to extract claims/statements from that answer, then checks if each claim can be attributed to at least one of the retrieved contexts. The score is:

```
Context Recall = (Number of claims attributable to contexts) / (Total number of claims in ground truth)
```

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-6">How do I read the score?</button>
<div id="aside-em-6" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-6" popovertargetaction="hide" aria-label="Close">×</button>

**Score interpretation**: Higher values mean more claims in the reference answer are supported by retrieved contexts. Inspect unsupported reference claims: a flawed reference can lower recall even when retrieval is appropriate.

**Optimization Strategies**:
- Increase the number of retrieved documents (top-k parameter)
- Improve query formulation (query expansion, reformulation)
- Check your chunking strategy (chunks might be too small and losing context)

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-7">See an example</button>
<div id="aside-em-7" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-7" popovertargetaction="hide" aria-label="Close">×</button>

```
Question: "What are the steps to request a virtual desktop?"
Ground truth answer includes: "Submit form, manager approval, IT provisioning"
```

If retrieved contexts only mention the form submission, context recall would be low (eg. approximately 0.33)

For high recall, retrieved contexts must cover all three ground truth steps.

</div>
</div>

<!-- fold:break -->

### Faithfulness

**Definition**: Whether claims in the generated answer are supported by the retrieved context. Unsupported claims may be false or may come from outside knowledge; this metric does not distinguish those cases.

**Why it matters**: It helps identify unsupported claims. A high score does not establish that the source itself is correct, or that the answer is complete or safe.

Abstaining can be appropriate when evidence is insufficient. A ratio-based score may be undefined when an answer has no factual claims; do not automatically count that as a perfect answer.

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-8">How is this calculated?</button>
<div id="aside-em-8" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-8" popovertargetaction="hide" aria-label="Close">×</button>

RAGAS uses an LLM to:
1. Extract individual claims/statements from the *generated answer*
2. For each claim, verify if it's supported by the retrieved contexts
3. Calculate the ratio of supported claims to total claims:

```
Faithfulness = (Number of claims supported by context) / (Total number of claims in answer)
```

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-9">How do I read the score?</button>
<div id="aside-em-9" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-9" popovertargetaction="hide" aria-label="Close">×</button>

**Score interpretation**: Higher values mean a larger fraction of the answer’s claims were judged supported by context. This does not establish that the context is true, that the answer is complete, or that the system is safe.

**Optimization Strategies**:
- Strengthen system prompts to emphasize grounding in context
- Lower model temperature for more deterministic outputs
- Add explicit "cite your sources" instructions
- Implement a validation layer that checks for unsupported claims

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-10">See an example</button>
<div id="aside-em-10" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-10" popovertargetaction="hide" aria-label="Close">×</button>

```
Context: "Password resets take 5-10 minutes to propagate across all systems. Use the self-service portal."

Faithful answer: "Your password reset will take 5-10 minutes to take effect. Use the self-service portal." (Faithfulness = 1.0, both claims supported)

Partially faithful: "Your password reset is instant via the portal." (Faithfulness = 0.5, only portal claim supported)

Unfaithful answer: "Contact your manager to reset passwords immediately." (Faithfulness = 0.0, contradicts context)
```

</div>
</div>

<!-- fold:break -->

### Answer Relevancy

**Definition**: How well the generated answer addresses the original question. It evaluates whether the response is on-topic and directly answers what was originally asked, and penalizes answers that are true and possibly even well-grounded, but off-topic.

**Why it matters**: A grounded answer can still miss the user's question. Relevancy helps detect that mismatch; actionability and usefulness need their own checks.

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-11">How is this calculated?</button>
<div id="aside-em-11" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-11" popovertargetaction="hide" aria-label="Close">×</button>

RAGAS uses an LLM to generate potential questions that the answer would be appropriate for, then measures the semantic similarity between these generated questions and the original question using embeddings:

```
Answer Relevancy = mean(cosine_similarity(original_question, generated_question_i))
```

Cosine similarity ranges from −1 to 1, although these scores usually fall between 0 and 1 ([RAGAS definition](https://docs.ragas.io/en/v0.2.15/concepts/metrics/available_metrics/answer_relevance/)).

where `i` indicates the index of a generated question derived from the generated response.

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-12">How do I read the score?</button>
<div id="aside-em-12" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-12" popovertargetaction="hide" aria-label="Close">×</button>

**Score interpretation**: Higher values indicate closer alignment between the original question and questions generated from the answer. This is a proxy for relevance, not proof of correctness or user satisfaction.

**Optimization Strategies**:
- Add examples of relevant vs. irrelevant answers in system prompt
- Implement answer validation that checks alignment with question
- Use instruction-tuned models that follow user intent better
- Add a reformulation step to ensure question is understood correctly

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-em-13">See an example</button>
<div id="aside-em-13" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-em-13" popovertargetaction="hide" aria-label="Close">×</button>

```
Question: "How do I reset my password?"

High relevancy answer: "To reset your password, visit the self-service portal at portal.company.com/reset and follow the prompts." (Relevancy ≈ 0.95)
    
    Generated questions: "How to reset password?", "What's the password reset process?"

Medium relevancy: "You can reset your password. Also, remember to use strong passwords with special characters." (Relevancy ≈ 0.70)
    
    Generated questions: "Can I reset my password?", "What does a strong password look like?"

Low relevancy: "Passwords are important for security. Our company requires passwords to be changed every 90 days." (Relevancy ≈ 0.40)
    
    Generated questions: "Why are passwords important?", "How often do I need to change my password?"
```

</div>
</div>

<!-- fold:break -->

<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">An agent answers How do I reset my password? with three accurate paragraphs about your password-complexity policy - every claim quoted from the retrieved docs. Which metric flags this response?</p>
  <button class="dx-quiz-opt" data-right data-fb="Exactly. Faithfulness only checks that claims are grounded; it says nothing about whether the answer is on-topic. A grounded-but-off-topic answer scores high on faithfulness and low on relevancy.">Answer Relevancy - it is faithful to the context but never answers the question asked</button>
  <button class="dx-quiz-opt" data-fb="No - every claim is accurately quoted from the docs, so faithfulness is high. Faithfulness measures grounding, not relevance to the question.">Faithfulness - the answer contains hallucinations</button>
  <button class="dx-quiz-opt" data-fb="Context Precision grades the retrieved documents, not the generated answer. The docs may be perfectly relevant; the problem is how the agent used them.">Context Precision - the retrieval was poor</button>
  <button class="dx-quiz-opt" data-fb="This is the core misconception. An answer can be fully grounded in its context yet completely miss what the user asked - which is exactly what Answer Relevancy catches.">None - a faithful answer is always a good answer</button>
</div>

<!-- fold:break -->

## Evaluating General Task Agents

For agents like the Report Generation Agent from Module 1, we need different metrics that focus on task completion and tool usage. 

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>TASK COMPLETION RATE</h4>Percent of tasks finished against clear success criteria. <i>Report agent: did it produce a report with every requested section, each one substantive?</i></div>
  <div class="dx-cell"><h4>TOOL USAGE ACCURACY</h4>Did the agent call the right tools at the right time - searching when needed, skipping needless calls, with good queries?</div>
  <div class="dx-cell"><h4>OUTPUT QUALITY</h4>Subjective quality of the final output - coherence, structure, factual accuracy, completeness, writing - scored by an LLM-as-a-judge rubric.</div>
</div>

<!-- fold:break -->

## Combining Metrics

No single metric tells the whole story. Effective evaluation combines multiple signals for a comprehensive view:

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>RAG AGENTS</h4><b>Context Precision + Recall</b> = retrieval quality. <b>Faithfulness + Answer Relevancy</b> = generation quality.</div>
  <div class="dx-cell"><h4>TASK AGENTS</h4><b>Task Completion</b> = core function. <b>Tool Usage</b> = efficiency. <b>Output Quality</b> = user satisfaction.</div>
  <div class="dx-cell"><h4>CROSS-CUTTING</h4><b>Latency</b>, <b>Cost</b> (tokens / API calls), and <b>Error Rate</b> - track these for every agent.</div>
</div>

<!-- fold:break -->

## Choosing the Right Metrics

<img src="_static/robots/supervisor.png" alt="Choosing Metrics" style="float:right;max-width:300px;margin:25px;" />

When deciding which metrics to use, consider:

1. **Your Agent's Purpose**: What is it trying to accomplish? What do good outcomes look like? Bad outcomes? 
2. **Available Resources**: Do you have ground truth data? Budget for LLM-based evaluation?
3. **Stakeholder Needs**: What do your users and business care about most?
4. **Development Stage**: Early development might focus on basic functionality; production needs comprehensive monitoring

**Start simple**: Begin with 2-3 key metrics that directly relate to your agent's core function. Add more sophisticated metrics as your evaluation pipeline matures.

<!-- fold:break -->

## Hands-On: Evaluating your Agents

Ready to implement these evaluation metrics? In the next lesson, we'll get hands-on with [Creating Evaluation Datasets](evaluation_data.md) using synthetic data generation to evaluate agent outputs.

Over the next sections, you'll learn how to:
- Use SDG to generate synthetic datasets for evaluation
- Use NVIDIA Nemotron models as evaluation judges
- Design effective evaluation prompts
- Implement custom evaluation criteria
