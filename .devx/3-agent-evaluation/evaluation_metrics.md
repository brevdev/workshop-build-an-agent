# Understanding Evaluation Metrics

<img src="_static/robots/datacenter.png" alt="Metrics and Data" style="float:right;max-width:300px;margin:25px;" />

Now that we understand why evaluation is important, let's dive into the specific metrics we can use to measure agent performance. Different types of agents require different evaluation approaches, so we'll explore metrics for both RAG systems and general-purpose agents.

<!-- fold:break -->

## Evaluating RAG Agents

The IT Help Desk agent you built in Module 2 is a Retrieval Augmented Generation (RAG) system. RAG agents have two distinct components that need evaluation:

1. **Retrieval Quality**: How well does the agent find relevant information?
2. **Generation Quality**: How well does the agent use that information to answer questions?

Let's explore the key metrics for each.

<!-- fold:break -->

## RAGAS Metrics Deep Dive

<img src="_static/robots/assembly.png" alt="Building Blocks" style="float:left;max-width:300px;margin:25px;" />

RAGAS provides a comprehensive framework for evaluating RAG systems. Each metric addresses a specific aspect of quality:

### Context Precision

**What it measures**: Whether the retrieved contexts are relevant to the question, with emphasis on ranking quality.

**How it works**: RAGAS uses an LLM to determine if each retrieved chunk is relevant to answering the question. It then calculates precision at each position in the ranked results.

**Why it matters**: High context precision means your retrieval system isn't wasting the LLM's context window with irrelevant information. This improves both quality and cost-efficiency.

**Example**:
- Question: "How do I reset my password?"
- Retrieved contexts: [Password reset guide, VPN setup, Password reset FAQ, Printer setup]
- Context Precision would be lower because irrelevant documents (VPN, Printer) are mixed with relevant ones

<!-- fold:break -->

### Context Recall

**What it measures**: Whether all the necessary information to answer the question was retrieved.

**How it works**: Given a ground truth answer, RAGAS checks if all the facts in that answer can be attributed to the retrieved contexts.

**Why it matters**: Low context recall means your agent is missing important information, leading to incomplete or incorrect answers.

**Example**:
- Question: "What are the steps to request a virtual desktop?"
- Ground truth answer includes: "Submit form, manager approval, IT provisioning"
- If retrieved contexts only mention the form submission, context recall would be low

<!-- fold:break -->

### Faithfulness

**What it measures**: Whether the generated answer is factually consistent with the retrieved context.

**How it works**: RAGAS extracts claims from the generated answer and verifies each claim against the retrieved contexts using an LLM.

**Why it matters**: Faithfulness prevents hallucination. A faithful agent only makes claims supported by its retrieved information.

**Example**:
- Context: "Password resets take 5-10 minutes to propagate"
- Faithful answer: "Your password reset will take 5-10 minutes to take effect"
- Unfaithful answer: "Your password reset is instant" (contradicts context)

<!-- fold:break -->

### Answer Relevancy

**What it measures**: How well the generated answer addresses the original question.

**How it works**: RAGAS generates potential questions that the answer would address, then measures similarity with the original question.

**Why it matters**: An agent might generate a factually correct, faithful response that still doesn't answer what the user asked.

**Example**:
- Question: "How do I reset my password?"
- High relevancy answer: "To reset your password, visit the self-service portal..."
- Low relevancy answer: "Passwords are important for security..." (true but not helpful)

<!-- fold:break -->

## Additional RAG Metrics

Beyond RAGAS, there are other useful metrics for RAG evaluation:

### Context Relevance

**What it measures**: The proportion of relevant information in the retrieved contexts.

**Formula**: (Relevant sentences in context) / (Total sentences in context)

**Why it matters**: Even if you retrieve the right documents, excessive irrelevant content can confuse the LLM or waste tokens.

### Answer Correctness

**What it measures**: Factual accuracy of the answer compared to ground truth.

**How it works**: Combines semantic similarity with factual overlap between generated and ground truth answers.

**Why it matters**: Provides an objective measure when you have labeled test data.

<!-- fold:break -->

## Evaluating General Agents

<img src="_static/robots/wrench.png" alt="Tool Usage" style="float:right;max-width:300px;margin:25px;" />

For agents like the Report Generation Agent from Module 1, we need different metrics that focus on task completion and tool usage:

### Task Completion Rate

**What it measures**: Percentage of tasks the agent successfully completes.

**How to measure**: Define clear success criteria for each task type, then evaluate whether the agent met those criteria.

**Example for Report Agent**:
- Did it generate a report?
- Does the report have all requested sections?
- Is each section substantive (not just placeholders)?

### Tool Usage Accuracy

**What it measures**: Whether the agent uses the right tools at the right time.

**How to measure**: Track which tools were called and compare against expected tool usage patterns.

**Example for Report Agent**:
- Did it search for information when needed?
- Did it avoid unnecessary searches?
- Did it use appropriate search queries?

### Output Quality

**What it measures**: Subjective quality of the agent's final output.

**How to measure**: Use LLM-as-a-judge with specific criteria:
- Coherence and structure
- Factual accuracy
- Completeness
- Writing quality

<!-- fold:break -->

## Combining Metrics

<img src="_static/robots/supervisor.png" alt="Holistic View" style="float:left;max-width:300px;margin:25px;" />

No single metric tells the whole story. Effective evaluation combines multiple metrics to provide a comprehensive view:

### For RAG Agents:
1. **Context Precision** + **Context Recall** = Retrieval quality
2. **Faithfulness** + **Answer Relevancy** = Generation quality
3. **Answer Correctness** = Overall accuracy (when ground truth available)

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

1. **Your Agent's Purpose**: What is it trying to accomplish?
2. **Available Resources**: Do you have ground truth data? Budget for LLM-based evaluation?
3. **Stakeholder Needs**: What do your users and business care about most?
4. **Development Stage**: Early development might focus on basic functionality; production needs comprehensive monitoring

**Start simple**: Begin with 2-3 key metrics that directly relate to your agent's core function. Add more sophisticated metrics as your evaluation pipeline matures.

<!-- fold:break -->

## Practical Considerations

### Metric Computation Cost

Some metrics are expensive to compute:
- **LLM-based metrics** (RAGAS, LLM-as-judge): Require API calls, add latency and cost
- **Similarity-based metrics**: Fast and cheap, but may miss nuance
- **Human evaluation**: Most expensive, but most accurate for subjective qualities

**Strategy**: Use fast metrics for continuous monitoring, expensive metrics for periodic deep evaluation.

### Metric Reliability

Not all metrics are equally reliable:
- **Deterministic metrics** (exact match, length): Consistent but limited
- **LLM-based metrics**: Powerful but can be inconsistent across runs
- **Human metrics**: Subject to bias and fatigue

**Strategy**: Validate your automated metrics against human judgment periodically.

<!-- fold:break -->

## Creating Evaluation Datasets

<img src="_static/robots/blueprint.png" alt="Dataset Design" style="float:right;max-width:300px;margin:25px;" />

Good metrics require good test data. When creating evaluation datasets:

1. **Cover Diverse Scenarios**: Include common cases, edge cases, and failure modes
2. **Include Ground Truth**: Where possible, provide correct answers for comparison
3. **Represent Real Usage**: Base test cases on actual user interactions
4. **Start Small**: Begin with 20-30 high-quality examples, expand over time
5. **Version Control**: Track your datasets alongside your code

For RAG agents, each test case should include:
- Question
- Ground truth answer (if available)
- Expected retrieved contexts (if available)
- Success criteria

For task agents, each test case should include:
- Task description
- Expected tools to be used
- Success criteria
- Example of good output

<!-- fold:break -->

## Hands-On: Implementing Metrics

Ready to implement these metrics? In the next lesson, we'll explore [LLM-as-a-Judge](llm_as_judge.md) techniques using NVIDIA models to evaluate agent outputs.

You'll learn how to:
- Use NVIDIA Nemotron models as evaluation judges
- Design effective evaluation prompts
- Implement custom evaluation criteria
- Balance cost and quality in evaluation pipelines

