# Why Agents?

<img src="_static/robots/spyglass.png" alt="Exploring Robot" style="float:right; max-width:300px;margin:25px;" />

Before we dive into building agents, let's take a step back. What are agents, really? And why would you use one instead of just calling an LLM directly?

<!-- fold:break -->

## The Evolution of LLM Applications

AI applications have evolved through three stages:

### Stage 1: Single LLM Calls

The simplest approach: send a prompt, get a response.

```
User: "What's the capital of France?"
LLM: "Paris"
```

This works great for simple questions, but the model is limited to what it learned during training. It can't look up current information, perform calculations, or take actions in the world.

<!-- fold:break -->

### Stage 2: Workflows (Chains)

<img src="_static/robots/plumber.png" alt="Workflow Robot" style="float:right; max-width:280px;margin:25px;" />

To overcome these limits, developers started chaining operations together. Retrieval Augmented Generation (RAG) is a classic example:

1. Take the user's question
2. Search a knowledge base for relevant documents
3. Pass the documents + question to the LLM
4. Return the response

This is more powerful, but the path is fixed. Every question goes through the same steps, whether it needs them or not.

<!-- fold:break -->

### Stage 3: Agents

Agents take a different approach: **let the model decide what to do**.

Instead of following a predetermined script, an agent:
- Looks at the current situation
- Decides which tool (if any) would help
- Takes action and observes the result
- Repeats until it has what it needs

The model is now in the driver's seat, choosing its own path to the answer.

<!-- fold:break -->

## What Problems Do Agents Solve?

<img src="_static/robots/supervisor.png" alt="Problem Solving Robot" style="float:right; max-width:280px;margin:25px;" />

### Problem 1: Dynamic Requirements

Not all questions need the same approach. "What time is it in Tokyo?" requires a different strategy than "Summarize the key themes in this 50-page document."

Agents can adapt their approach based on what they're asked.

### Problem 2: Multi-Source Integration

Real tasks often require combining information from multiple places - checking inventory, looking up order status, searching FAQs - all in one conversation.

Agents can orchestrate multiple tools without requiring every combination to be pre-programmed.

### Problem 3: Complex Reasoning

Some problems require thinking through multiple steps, with each step informed by previous results.

Agents can break down complex tasks, try different approaches, and recover from dead ends.

<!-- fold:break -->

## When Agents Aren't the Answer

Agents aren't always better. They add complexity, latency, and cost. Consider:

- **Simple questions**: If a single LLM call works, use it
- **Predictable workflows**: If the steps are always the same, a chain is simpler
- **Latency-critical applications**: Multiple model calls take time
- **Cost-sensitive deployments**: More calls = more tokens = higher costs

The goal isn't to use agents everywhere - it's to use them where they provide real value.

<!-- fold:break -->

## What You'll Build

<img src="_static/robots/typewriter.png" alt="Writing Robot" style="float:right; max-width:280px;margin:25px;" />

In this module, you'll build a **Report Generation Agent** - an AI system that can:

- Research any topic using web search
- Decide how many searches it needs
- Synthesize information from multiple sources
- Write a structured report with citations

This is a task that genuinely benefits from an agent's flexibility. Different topics require different research strategies, and the agent adapts accordingly.

Ready to understand how agents work? Continue to [Introduction to Agents](introduction_to_agents.md)!
