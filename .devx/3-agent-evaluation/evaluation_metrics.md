# Understanding Evaluation Metrics

<img src="_static/robots/datacenter.png" alt="Metrics and Data" style="float:left;max-width:250px;margin:25px;" />

Now that we understand why evaluation is important, let's dive into the specific metrics we can use to measure agent performance. Different types of agents require different evaluation approaches, so we'll explore metrics for both RAG systems and general-purpose agents.

<!-- fold:break -->

One of the most powerful techniques for evaluating AI agents is using another LLM to judge the quality of outputs. This approach, called "LLM-as-a-judge," allows us to evaluate subjective qualities like helpfulness, coherence, and relevance at scale. 

Traditional deterministic metrics like string matching, keyword searching, or BLEU scores don't work well for evaluating natural language outputs. Human evaluation is a lot more accurate and captures subjectivity well, but is expensive and slow. 

LLM-as-a-judge provides a neat middle ground. 

<!-- fold:break -->

**Advantages**:
- **Scalable**: Evaluate thousands of outputs quickly
- **Consistent**: More consistent than human reviewers
- **Flexible**: Can assess any criteria you define
- **Nuanced**: Understands semantic meaning and context
- **Cost-Effective**: Cheaper than human evaluation at scale

<!-- fold:break -->

**Limitations**:
- **Not Perfect**: Judge models can make mistakes
- **Biased**: May favor outputs similar to their own style
- **Costly**: More expensive than simple metrics
- **Requires Validation**: Should be spot-checked against human judgment

<!-- fold:break -->

## Evaluating RAG Agents

The IT Help Desk agent you built in Module 2 is a Retrieval Augmented Generation (RAG) system. RAG agents have two distinct components that need evaluation:

1. **Retrieval Quality**: How well does the agent find relevant information?
2. **Generation Quality**: How well does the agent use that information to answer questions?

Let's explore the key metrics for each.

<!-- fold:break -->

## RAGAS Metrics Deep Dive

<img src="_static/robots/assembly.png" alt="Building Blocks" style="float:right;max-width:300px;margin:25px;" />

RAGAS provides a comprehensive framework for evaluating RAG systems. Each metric addresses a specific aspect of quality.

### Context Precision

**Definition**: Whether the retrieved chunks are relevant or irrelevant to the question (signal-to-noise ratio). Crucially, it accounts for **ranking**. It's not enough to retrieve the right document; it also needs to be at the top of the list. 

**Why it matters**: High context precision means your retrieval system isn't wasting the LLM's context window with irrelevant information. High context precision improves both generation quality and cost-efficiency. It also reduces the risk of the model being distracted by off-topic content.

Crucially, LLMs can suffer from the "Lost in the Middle" phenomenon where relevant information buried in the middle of a context window can be ignored. This is why **ranking** is important as the model can see the right data first for best results. 

<!-- fold:break -->

**How it works**: RAGAS uses an LLM to determine if each retrieved chunk is relevant or irrelevant to answering the question. It then calculates precision at each position (precision@k) in the ranked results and averages them. The formula weighs higher-ranked relevant documents more heavily:

```
Context Precision = (Σ (Precision@k × relevance_k)) / Total number of relevant items in retrieved contexts
```

where `relevance_k` is the relevance indicator (0 or 1) for the item at rank `k` and: 

```
Precision@k = true positives @ k / (true positives @ k + false positives @k) 
```

<details>
<summary><strong>I'm Confused, Click Me to See a Sample Calculation!</strong></summary>

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

</details>

<!-- fold:break -->

**Score interpretation**:
- **0.9-1.0**: Excellent - nearly all retrieved documents are relevant
- **0.7-0.9**: Good - most documents are relevant with few irrelevant ones
- **0.5-0.7**: Fair - significant noise in retrieval results
- **Below 0.5**: Poor - retrieval is returning mostly irrelevant documents

**Optimization Strategies**
- Fine-tune your retrieval parameters (similarity threshold, top-k)
- Improve embedding model quality
- Add reranking as a second stage
- Use metadata filtering to narrow search scope

<details>
<summary><strong>Click to See Another Example</strong></summary>

```
Question: "How do I reset my password?"
Retrieved contexts: 
    [Password reset guide, VPN setup, Password reset FAQ, Printer setup]
```

Context Precision would be lower (approximately 0.5) because irrelevant documents (VPN, Printer) are mixed with relevant ones

Better retrieval: [Password reset guide, Password reset FAQ, Account security, Login procedures] would score higher

</details>

<!-- fold:break -->

### Context Recall

**Definition**: Whether all the necessary information to answer the question was retrieved. It evaluates completeness rather than precision.

**Why it matters**: This is your system's "Upper Bound" of knowledge. Low context recall means your agent is missing important information, leading to incomplete or incorrect answers. Even with perfect generation, missing context will result in gaps in the response.

<!-- fold:break -->

**How it works**: Given a *ground truth* answer, RAGAS uses an LLM to extract claims/statements from that answer, then checks if each claim can be attributed to at least one of the retrieved contexts. The score is:

```
Context Recall = (Number of claims attributable to contexts) / (Total number of claims in ground truth)
```

<!-- fold:break -->

**Score interpretation**:
- **0.9-1.0**: Excellent - all critical information was retrieved
- **0.7-0.9**: Good - most information retrieved, minor gaps
- **0.5-0.7**: Fair - significant information gaps
- **Below 0.5**: Poor - major information gaps, answer will be incomplete

**Optimization Strategies**:
- Increase the number of retrieved documents (top-k parameter)
- Improve query formulation (query expansion, reformulation)
- Check your chunking strategy (chunks might be too small and losing context)

<details>
<summary><strong>Click to See an Example</strong></summary>

```
Question: "What are the steps to request a virtual desktop?"
Ground truth answer includes: "Submit form, manager approval, IT provisioning"
```

If retrieved contexts only mention the form submission, context recall would be low (eg. approximately 0.33)

For high recall, contexts must cover all three steps.

</details>

<!-- fold:break -->

### Faithfulness

**Definition**: Whether the generated answer is factually consistent with the retrieved context, eg. whether every claim can be inferred from somewhere in the retrieved context. It's essentially a measure of hallucination - lower faithfulness means more hallucinated content.

**Why it matters**: Faithfulness is critical for production RAG systems since safety is paramount. It prevents hallucination and ensures users can trust the agent's responses. Low faithfulness means the model is "making things up" rather than grounding answers in retrieved knowledge.

A faithful answer might be "I don't know" (if the context is empty). An unfaithful answer invents facts. At the end of the day, **an honest "I don't know" is preferable over a confident lie.**

<!-- fold:break -->

**How it works**: RAGAS uses an LLM to:
1. Extract individual claims/statements from the *generated answer*
2. For each claim, verify if it's supported by the retrieved contexts
3. Calculate the ratio of supported claims to total claims:

```
Faithfulness = (Number of claims supported by context) / (Total number of claims in answer)
```

<!-- fold:break -->

**Score interpretation**:
- **0.9-1.0**: Excellent - answer is fully grounded in context
- **0.7-0.9**: Good - mostly grounded with minor extrapolations
- **0.5-0.7**: Fair - significant unsupported claims
- **Below 0.5**: Poor - frequent hallucination, unreliable

**Optimization Strategies**:
- Strengthen system prompts to emphasize grounding in context
- Lower model temperature for more deterministic outputs
- Add explicit "cite your sources" instructions
- Implement a validation layer that checks for unsupported claims

<details>
<summary><strong>Click to See an Example</strong></summary>

```
Context: "Password resets take 5-10 minutes to propagate across all systems. Use the self-service portal."

Faithful answer: "Your password reset will take 5-10 minutes to take effect. Use the self-service portal." (Faithfulness = 1.0, both claims supported)

Partially faithful: "Your password reset is instant via the portal." (Faithfulness = 0.5, only portal claim supported)

Unfaithful answer: "Contact your manager to reset passwords immediately." (Faithfulness = 0.0, contradicts context)
```
</details>

<!-- fold:break -->

### Answer Relevancy

**Definition**: How well the generated answer addresses the original question. It evaluates whether the response is on-topic and directly answers what was originally asked, and penalizes answers that are true and possibly even well-grounded, but off-topic.

**Why it matters**: An agent might generate a factually correct, faithful response that still doesn't answer what the user asked. High relevancy ensures users get actionable answers to their specific questions, improving user satisfaction and reducing follow-up queries.

<!-- fold:break -->

**How it works**: RAGAS uses an LLM to generate potential questions that the answer would be appropriate for, then measures the semantic similarity between these generated questions and the original question using embeddings:

```
Answer Relevancy = mean(cosine_similarity(original_question, generated_question_i))
```

where `i` indicates the index of a generated question derived from the generated response.

<!-- fold:break -->

**Score interpretation**:
- **0.9-1.0**: Excellent - answer directly addresses the question
- **0.7-0.9**: Good - mostly relevant with minor tangents
- **0.5-0.7**: Fair - partially addresses question
- **Below 0.5**: Poor - answer is off-topic or too generic

**Optimization Strategies**:
- Add examples of relevant vs. irrelevant answers in system prompt
- Implement answer validation that checks alignment with question
- Use instruction-tuned models that follow user intent better
- Add a reformulation step to ensure question is understood correctly

<details>
<summary><strong>Click to See an Example</strong></summary>

```
Question: "How do I reset my password?"

High relevancy answer: "To reset your password, visit the self-service portal at portal.company.com/reset and follow the prompts." (Relevancy ≈ 0.95)
    
    Generated questions: "How to reset password?", "What's the password reset process?"

Medium relevancy: "You can reset your password. Also, remember to use strong passwords with special characters." (Relevancy ≈ 0.70)
    
    Generated questions: "Can I reset my password?", "What does a strong password look like?"

Low relevancy: "Passwords are important for security. Our company requires passwords to be changed every 90 days." (Relevancy ≈ 0.40)
    
    Generated questions: "Why are passwords important?", "How often do I need to change my password?"
```

</details>

<!-- fold:break -->

## Evaluating General Task Agents

<img src="_static/robots/wrench.png" alt="Tool Usage" style="float:right;max-width:300px;margin:25px;" />

For agents like the Report Generation Agent from Module 1, we need different metrics that focus on task completion and tool usage. 

<!-- fold:break -->

### Task Completion Rate

**What it measures**: Percentage of tasks the agent successfully completes.

**How to measure**: Define clear success criteria for each task type, then evaluate whether the agent met those criteria.

**Example for Report Agent**:
- Did it generate a report?
- Does the report have all requested sections?
- Is each section substantive (not just placeholders)?

<!-- fold:break -->

### Tool Usage Accuracy

**What it measures**: Whether the agent uses the right tools at the right time.

**How to measure**: Track which tools were called and compare against expected tool usage patterns.

**Example for Report Agent**:
- Did it search for information when needed?
- Did it avoid unnecessary searches?
- Did it use appropriate search queries?

<!-- fold:break -->

### Output Quality

**What it measures**: Subjective quality of the agent's final output. This can be largely user-defined based on the particular task the agent is asked to do. 

**How to measure**: Use LLM-as-a-judge with specific criteria, such as:
- Coherence and structure
- Factual accuracy
- Completeness
- Writing quality

<!-- fold:break -->

## Combining Metrics

<img src="_static/robots/supervisor.png" alt="Holistic View" style="float:right;max-width:300px;margin:25px;" />

No single metric tells the whole story. Effective evaluation combines multiple metrics to provide a comprehensive view:

### For RAG Agents:
1. **Context Precision** + **Context Recall** = Retrieval quality
2. **Faithfulness** + **Answer Relevancy** = Generation quality

### For Task Agents:
1. **Task Completion Rate** = Core functionality
2. **Tool Usage Accuracy** = Efficiency
3. **Output Quality** = User satisfaction

### Cross-Cutting Metrics:
- **Latency**: How long does the agent take?
- **Cost**: How many tokens/API calls are used?
- **Error Rate**: How often does the agent fail or produce errors?

<!-- fold:break -->

## Choosing the Right Metrics

When deciding which metrics to use, consider:

1. **Your Agent's Purpose**: What is it trying to accomplish? What do good outcomes look like? Bad outcomes? 
2. **Available Resources**: Do you have ground truth data? Budget for LLM-based evaluation?
3. **Stakeholder Needs**: What do your users and business care about most?
4. **Development Stage**: Early development might focus on basic functionality; production needs comprehensive monitoring

**Start simple**: Begin with 2-3 key metrics that directly relate to your agent's core function. Add more sophisticated metrics as your evaluation pipeline matures.

<!-- fold:break -->

## Hands-On: Implementing Metrics

Ready to implement these evaluation metrics? In the next lesson, we'll get hands-on with [Running Evaluations](running_evaluations.md) using NVIDIA models to evaluate agent outputs.

You'll learn how to:
- Use NVIDIA Nemotron models as evaluation judges
- Design effective evaluation prompts
- Implement custom evaluation criteria
- Balance cost and quality in evaluation pipelines

