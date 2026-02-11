# Introduction to Agent Evaluation

<img src="_static/robots/study.png" alt="Understanding Evaluation" style="float:right;max-width:300px;margin:25px;" />

Building AI agents is exciting. Seeing them in action for the first time feels like magic. But as we move closer from prototypes to production, "magic" isn't enough. We need **trust**.

How do you know if your agent is actually working? Is it hallucinating? Is it rude? Is it getting better or worse as you tweak the prompts? 

<!-- fold:break -->

Manual testing ("vibe checking") can only take you so far. As your agents become more complex and handle more use cases, you need systematic ways to measure their performance, identify weaknesses, and track improvements over time. You need to treat evaluation not as an afterthought, but as a core engineering discipline.

In this module, we will transform your agent development process from an art into a science.

<!-- fold:break -->

## The Challenge of Evaluating Agents

<img src="_static/robots/debug.png" alt="Debugging Complexity" style="float:right;max-width:300px;margin:25px;" />

Evaluating AI agents is more complex than traditional software testing because of several factors:

**Malicious Behavior**: Agents can exhibit harmful behaviors on their own or when manipulated by bad actors. Evaluation should include adversarial test cases to ensure safe behavior.

- *Toxic outputs*: Offensive or inappropriate content, even when not prompted
- *Prompt injection*: Malicious inputs that override instructions or leak system prompts
- *Adversarial queries*: Inputs designed to exploit model weaknesses 

**Non-Determinism**: Agents can produce different valid responses to the same input.

This variability is a feature that allows creativity and flexibility, but also makes evaluation tricky - you can't just check for an exact expected output.

<!-- fold:break -->

**Subjective Quality**: Agent quality often depends on subjective attributes like tone, style, and helpfulness.

There isn't always one "right" answer. A response might be factually correct but unhelpful, or seem helpful but contain hallucinations. Evaluation methods need to capture this nuance.

**Multi-Step Reasoning**: Agents chain together complex thoughts and actions to solve problems.

You must evaluate the entire chain, not just isolated steps. A minor early error (like misinterpreting intent) can cascade into a completely wrong result, even if later steps were technically correct.

<!-- fold:break -->

<img src="_static/robots/controls.png" alt="How to Measure" style="float:right;max-width:300px;margin:25px;" />

**Tool Usage**: Agents interact with external APIs, databases, and other systems.

Evaluation must verify not just the final response, but also that the agent selected the right tool, used correct arguments, and properly incorporated the tool's output.

**Context Dependence**: Agent behavior changes based on conversation history and retrieved data.

An agent's answer might differ based on what was said three turns ago. Testing should cover varied conversational flows and retrieval contexts, not just single-turn inputs.

<!-- fold:break -->

## What Should We Measure?

To trust our agents, we need to measure their performance across two key dimensions: **Process** (how they got the answer) and **Outcome** (the quality of the answer itself).

When debugging a RAG agent, for example, a wrong answer could come from two places:
1. **Bad Retrieval**: The agent didn't find the relevant documents.
2. **Bad Generation**: The agent found the documents but hallucinated the answer.

We break these down into specific signals.

<!-- fold:break -->

### Retrieval Metrics (Did we find the right data?)

* **Context Precision**: Is the stuff we found actually useful?
* **Context Recall**: Did we miss anything else important?

### Generation Metrics (Did we write a good answer?)

* **Faithfulness**: Is the answer grounded in the facts we found? (No hallucinations!)
* **Answer Relevance**: Did we actually answer the user's question?

<!-- fold:break -->

### Other Agents

For more traditional autonomous agents (like the report generator from Module 1), we also track metrics such as:
* **Tool Usage**: Did the agent use the search tool correctly?
* **Task Completion**: Did we get a final report that meets the requirements?

We'll get a better understanding of how these metrics work in the next section, as well as get a chance to work with these metrics in the hands-on lab notebooks later in this module! 

<!-- fold:break -->

<img src="_static/robots/wrench.png" alt="Judge" style="float:left;max-width:250px;margin:25px;" />

## The "Judge" Problem

In addition to what it is we should be evaluating, there's also a question of who should be the one doing the evaluating. 

If an agent writes a poem or summarizes a document, how do you write a unit test for that? Testing for `assert response == "The cat sat on the mat"` rarely works in the age of LLMs.

We generally rely on three approaches: 

<!-- fold:break -->

### 1. LLM-as-a-Judge (The Modern Standard)

We use a specialized NVIDIA Nemotron model to grade the output of our agent. We prompt the judge a special rubric (e.g., "Is this helpful? 1-5"), and it scales well. 

**Pros**

- Can assess subjective qualities
- Handles variation in correct responses
- Scalable

**Cons**

- Adds cost and latency
- Can inherit biases from the judge model
- Requires careful prompt engineering

**This is the primary method we will use in this module.**

<!-- fold:break -->

#### Calibrating Your LLM Judge

An LLM judge is only useful if it agrees with human judgment. Before trusting automated scores, you should **calibrate** your judge by comparing its ratings to human ratings on a small sample.

**A simple calibration workflow:**
1. Select 5-10 representative agent responses
2. Have a human rate each response on your rubric (e.g., 1-5 for helpfulness)
3. Run the same responses through your LLM judge
4. Compare: Do scores align? Where do they disagree?
5. If alignment is poor, refine your evaluation prompt or add examples

Even a quick spot-check on 5 samples can reveal systematic biases in your judge—like being too lenient, too harsh, or misunderstanding your criteria. 

We'll practice this calibration step in the hands-on notebooks later in the module.

<!-- fold:break -->

### 2. Human Evaluation (The Gold Standard)

Real humans reviewing outputs: this is the most accurate signal for subjective qualities but it can be the slowest and most expensive method. 

It's best used to "grade the grader", meaning ensuring your LLM Judge aligns with human preferences. 

**Pros**

- Most accurate for subjective qualities
- Catches issues automated metrics miss

**Cons**

- Expensive, slow, not scalable
- Subject to human bias and inconsistency

In practice, we use human evaluation sparingly to align the LLM judge to human preference rather than as a go-to method. 

<!-- fold:break -->

### 3. Deterministic Checks

Good old-fashioned code-based unit testing. Did the generated SQL query execute without error? Did the JSON parse correctly? Does the response have a specific keyword? 

These are objective, easy to automate pass/fail checks that are essential for reliable agents, though on their own they may not capture nuance well and may miss valid alternative responses. 

**Pros**

- Objective
- Easiest to automate
- Clear pass/fail criteria

**Cons**

- Doesn't capture nuance
- May miss valid alternative responses

Often, evaluation workflows will take on a hybrid approach. 

* LLM-as-a-judge to evaluate the agent's thought process
* Deterministic checks to verify an agent's intermediate and/or final outputs are well-formed
* Occasional calibration with a human evaluator to ensure alignment of judging standards with subjective human preferences. 

<!-- fold:break -->

<img src="_static/robots/surf.png" alt="Judge" style="float:right;max-width:300px;margin:25px;" />

## Your Journey in this Module

We will guide you through the following steps to build your evaluation pipeline:

1.  **[Understanding Evaluation Metrics](evaluation_metrics.md)**: Learn the specific signals we look for, like "Faithfulness" and "Context Recall".
2.  **[Creating Evaluation Datasets](evaluation_data.md)**: Create a dataset for agent evaluation using synthetic data generation. 
3.  **[Running Evaluations](running_evaluations.md)**: Execute the pipeline on your own agents and interpret the results.
4.  **[Continuous Improvement](continuous_improvement.md)**: Close the loop by using data to make your agents smarter.

Ready to turn your "vibe checks" into rigorous engineering? Let's continue to [Understanding Evaluation Metrics](evaluation_metrics.md) to learn about the tools we'll need.

