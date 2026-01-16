# Introduction to Agent Evaluation

<img src="_static/robots/study.png" alt="Understanding Evaluation" style="float:right;max-width:300px;margin:25px;" />

Building AI agents is exciting. Seeing them in action for the first time feels like magic. But as we move closer from prototypes to production, "magic" isn't enough. We need **trust**.

How do you know if your agent is actually working? Is it hallucinating? Is it rude? Is it getting better or worse as you tweak the prompts? 

Manual testing ("vibe checking") can only take you so far. As your agents become more complex and handle more use cases, you need systematic ways to measure their performance, identify weaknesses, and track improvements over time. You need to treat evaluation not as an afterthought, but as a core engineering discipline.

In this module, we will transform your agent development process from an art into a science.

<!-- fold:break -->

## The Challenge of Evaluating Agents

<img src="_static/robots/debug.png" alt="Debugging Complexity" style="float:right;max-width:300px;margin:25px;" />

Evaluating AI agents is more complex than traditional software testing because of several factors:

<!-- fold:break -->

**Malicious Behavior**: Unlike traditional software with predictable failure modes, agents can exhibit harmful behaviors, either through their own outputs or when manipulated by bad actors. Evaluation must include "red teaming" with adversarial test cases to ensure your agent behaves safely even under attack.

- *Toxic outputs* occur when an agent generates offensive, harmful, or inappropriate content—even when not explicitly prompted to do so. 
- *Prompt injection* happens when malicious users craft inputs designed to override the agent's instructions, potentially causing it to ignore safety guidelines, leak system prompts, or perform unintended actions. 
- *Adversarial queries* are carefully designed inputs that exploit model weaknesses to produce incorrect or dangerous responses. 

<!-- fold:break -->

**Non-Determinism**: AI agents are non-deterministic, meaning they can produce different valid responses to the same input. 

Unlike traditional software where the same input conditions will always lead to the same output, an agent might answer the same question differently every time. This variability is a feature, not a bug; it allows for creativity and flexibility in responses. But it can also make evaluation difficult.

<!-- fold:break -->

**Subjective Quality**: Agent quality is often subjective, depending on attributes like tone, style, and helpfulness. 

Unlike a binary assertion in code testing, there isn't always one "right" answer. One response might be factually true but unhelpful or rude. Another response might appear helpful and benign but content-wise is not rooted in ground truth. These complexities require evaluation methods that can capture nuance rather than just strict string matching.

<!-- fold:break -->

**Multi-Step Reasoning**: Agents typically perform multi-step reasoning, chaining together thoughts and actions to solve complex problems. 

Unlike unit testing a single isolated function, you must evaluate the entire chain of logic. A minor error in an early step, like misinterpreting a user's intent, can cascade into a completely incorrect result, even if the later steps were technically flawless under traditional standards.

<!-- fold:break -->

**Tool Usage**: Agents often engage in tool usage, interacting with external APIs, databases, and environments. 

Unlike testing pure software logic, this introduces side effects and dependencies on external systems. Evaluation must verify not only the final text response but also that the agent selected the appropriate tool, retrieved the appropriate information, formatted the arguments correctly, and handled the tool's output properly in response generation.

<!-- fold:break -->

**Context Dependence**: Agents exhibit context dependence, meaning their behavior changes based on conversation history or retrieved data. 

Unlike stateless functions that process inputs in a vacuum in traditional software, an agent's answer might change based on what was said three turns ago. Ensuring consistency requires testing across varied conversational flows and data retrieval contexts, not just single-turn inputs and outputs.

<!-- fold:break -->

<img src="_static/robots/controls.png" alt="How to Measure" style="float:right;max-width:300px;margin:25px;" />

## What Should We Measure?

To trust our agents, we need to measure their performance across two key dimensions: **Process** (how they got the answer) and **Outcome** (the quality of the answer itself).

When debugging a RAG agent, for example, a wrong answer could come from two places:
1. **Bad Retrieval**: The agent didn't find the relevant documents.
2. **Bad Generation**: The agent found the documents but hallucinated the answer.

We break these down into specific signals.

<!-- fold:break -->

### Retrieval Metrics (Did we find the right data?)

* **Context Precision**: Is the stuff we found actually useful?
* **Context Recall**: Did we miss anything important?

### Generation Metrics (Did we write a good answer?)

* **Faithfulness**: Is the answer grounded in the facts we found? (No hallucinations!)
* **Answer Relevance**: Did we actually answer the user's question?

<!-- fold:break -->

### Other Agents

For more traditional autonomous agents (like the researcher from Module 1), we also track metrics such as:
* **Tool Usage**: Did the agent use the search tool correctly?
* **Task Completion**: Did we get a final report that meets the requirements?

We'll get a better understanding of how these metrics work in the next section, as well as get a chance to work with these metrics in the hands-on lab notebooks later in this module! 

<!-- fold:break -->

<img src="_static/robots/wrench.png" alt="Judge" style="float:left;max-width:250px;margin:25px;" />

## The "Judge" Problem

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

Even a quick spot-check on 5 samples can reveal systematic biases in your judge—like being too lenient, too harsh, or misunderstanding your criteria. We'll practice this calibration step in the hands-on notebooks later in the module.

<!-- fold:break -->

### 2. Human Evaluation (The Gold Standard)

Real humans reviewing logs. This is the most accurate signal for subjective qualities but it can be the slowest and most expensive method. It's best used to "grade the grader", meaning ensuring your LLM Judge aligns with human preferences. 

**Pros**

- Most accurate for subjective qualities
- Catches issues automated metrics miss

**Cons**

- Expensive, slow, not scalable
- Subject to human bias and inconsistency

In practice, we use human evaluation sparingly to align the LLM judge to human preference rather than a go-to method. 

<!-- fold:break -->

### 3. Deterministic Checks

Good old-fashioned code-based unit testing. Did the generated SQL query execute without error? Did the JSON parse correctly? Does the response have a specific keyword? 

These are binary pass/fail checks that are essential for reliable agents. These are objective and easy to automate with clear pass/fail criteria, but does not capture nuance well and may miss valid alternative responses. 

**Pros**

- Objective
- Easiest to automate
- Clear pass/fail criteria

**Cons**

- Doesn't capture nuance
- May miss valid alternative responses

Often, evaluation workflows will take on a hybrid approach. For example, use an LLM-as-a-judge to evaluate the agent's thought process, a deterministic check to verify an agent's intermediate and/or final outputs are valid, and an occasional calibration with a human evaluator to ensure alignment of judging standards with subjective human preferences. 

<!-- fold:break -->

<img src="_static/robots/surf.png" alt="Judge" style="float:right;max-width:300px;margin:25px;" />

## Your Journey in this Module

We will guide you through the following steps to build your evaluation pipeline:

1.  **[Understanding Evaluation Metrics](evaluation_metrics.md)**: Learn the specific signals we look for, like "Faithfulness" and "Context Recall".
2.  **[Creating Evaluation Datasets](evaluation_data.md)**: Create a dataset for agent evaluation using synthetic data generation. 
3.  **[Running Evaluations](running_evaluations.md)**: Execute the pipeline on your own agents and interpret the results.
4.  **[Continuous Improvement](continuous_improvement.md)**: Close the loop by using data to make your agents smarter.

Ready to turn your "vibe checks" into rigorous engineering? Let's continue to [Understanding Evaluation Metrics](evaluation_metrics.md) to learn about the tools we'll need.

