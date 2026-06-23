<div class="dx-hero" data-eyebrow="MODULE 01 / 01 - CONCEPTS" data-title="Why Agents?" data-meta="DURATION::1-2 hrs|MODEL::Nemotron 3 Super|GPU::Hosted API endpoint"></div>

Before we dive into building agents, let's take a step back. What are agents, really? And why would you use one instead of just calling an LLM directly?

<!-- fold:break -->

## The Evolution of LLM Applications

AI applications have evolved through three stages:

<div class="dx-bento dx-reveal">
  <div class="dx-cell"><h4>STAGE 1: SINGLE LLM CALL</h4>Send a prompt, get a response. Limited to training data - no live info, no actions.</div>
  <div class="dx-cell"><h4>STAGE 2: WORKFLOW</h4>Chain fixed steps (e.g. RAG). More capable, but every query takes the same hardcoded path.</div>
  <div class="dx-cell is-wide"><h4>STAGE 3: AGENT</h4>The model decides what to do - choosing tools and looping until it has the answer. The path adapts to each task.</div>
</div>

### Stage 1: Single LLM Calls

<img src="_static/robots/spyglass.png" alt="Exploring Robot" style="float:right; max-width:300px;margin:25px;" />

The simplest approach: send a prompt, get a response.

```
User: "What's the capital of France?"
LLM: "The capital of France is Paris"
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

<div class="dx-island dx-reveal">
  <p class="dx-island-title">WHEN AGENTS AREN'T THE ANSWER</p>
  <p>Agents aren't always better. They add complexity, latency, and cost. Consider a simpler approach for:</p>
  <p><span class="dx-chip">SIMPLE QUESTIONS</span> If a single LLM call works, use it.</p>
  <p><span class="dx-chip">PREDICTABLE WORKFLOWS</span> If the steps are always the same, a chain is simpler.</p>
  <p><span class="dx-chip">LATENCY-CRITICAL</span> Multiple model calls take time.</p>
  <p><span class="dx-chip">COST-SENSITIVE</span> More calls = more tokens = higher costs.</p>
  <p>The goal isn't to use agents everywhere - it's to use them where they provide real value.</p>
</div>

<!-- fold:break -->

## What You'll Build

<img src="_static/robots/typewriter.png" alt="Writing Robot" style="float:right; max-width:280px;margin:25px;" />

In this module, you'll build a **Report Generation Agent** - an AI system that can:

- Research any topic using web search
- Decide how many searches it needs
- Synthesize information from multiple sources
- Write a structured report with citations

This is a task that genuinely benefits from an agent's flexibility. Different topics require different research strategies, and the agent adapts accordingly.

<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">Which of these tasks is the best fit for an agent, rather than a single LLM call or a fixed workflow?</p>
  <button class="dx-quiz-opt" data-fb="This is one fixed classification with a fixed set of outputs - a single LLM call does it. An agent's reasoning loop only adds latency and cost when the path never changes.">Sort each incoming support ticket into billing, technical, or other</button>
  <button class="dx-quiz-opt" data-right data-fb="Right. The path changes per bug, it pulls from several sources, and each step depends on the last - exactly where letting the model choose its next move pays off.">Investigate a reported bug by searching the docs, checking recent incident reports, and writing up a likely root cause</button>
  <button class="dx-quiz-opt" data-fb="Input-to-summary is a single fixed path with no decisions to make. That is a workflow (a chain), not an agent.">Condense a customer email into three bullet points</button>
  <button class="dx-quiz-opt" data-fb="A single deterministic transformation - no tools, no branching, no iteration. Reaching for an agent here is over-engineering.">Translate a fixed block of text from English to Spanish</button>
</div>

Ready to understand how agents work? Continue to [Introduction to Agents](introduction_to_agents.md)!
