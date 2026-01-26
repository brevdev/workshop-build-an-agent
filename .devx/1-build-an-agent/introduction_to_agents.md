# Introduction to Agents

<img src="_static/robots/blueprint.png" alt="VSS Robot Character" style="float:left; max-width:300px;margin:25px;" />

Welcome to the world of AI agents! In this module, we'll explore how agents apply Large Language Models to solve complex tasks.

<!-- fold:break -->

## What is an Agent?

Large Language Models (LLMs) have an impressive ability to generate text and recall information. On their own, however, they are limited by their training data and cannot interact with the outside world.

**Workflows** extend LLMs by adding pre-defined sequences of operations. Retrieval Augmented Generation (RAG) is a common example: always retrieve documents, then generate a response. The path is fixed by the developer.

**Agents** go further. An agent uses an LLM to *decide* what actions to take. Instead of following a script, the agent reasons about what it needs and chooses the right tools dynamically.

| Approach | Who decides what to do? | Flexibility |
|----------|------------------------|-------------|
| LLM | N/A (single response) | Low |
| Workflow | Developer (hardcoded) | Medium |
| Agent | The LLM itself | High |

<!-- fold:break -->

## Anatomy of an Agent

<img src="_static/robots/assembly.png" alt="Agent Blueprint" style="float:right; max-width:320px; margin:20px 0 20px 30px; border-radius:12px;" />

There are **four key components** fundamental to all agents:

<ul style="margin-left:1em;">
  <li><b>MODEL:</b> The LLM that decides which tools to use and how to respond</li>
  <li><b>TOOLS:</b> Functions that let the agent perform actions (search, calculate, query APIs)</li>
  <li><b>MEMORY/STATE:</b> Information available during and between conversations</li>
  <li><b>ROUTING:</b> The logic that orchestrates flow between reasoning and acting</li>
</ul>

<!-- fold:break -->

## Tool Schemas

Tools are just functions, but the LLM needs to know how to use them. A **tool schema** describes each tool's name, purpose, and parameters:

```json
{
  "name": "search_web",
  "description": "Search the web for current information",
  "parameters": {
    "query": { "type": "string", "description": "The search query" }
  }
}
```

The quality of your tool descriptions directly affects how well your agent uses them.

<!-- fold:break -->

## The Agentic Loop

The core of any agent is a loop where the model decides what happens next:

1. Receive input and available tools
2. Model decides: **respond** or **call a tool**
3. If tool call → execute it, add result to memory, return to step 1
4. If response → return to user

This loop continues until the model decides it has enough information. The model controls the flow, not hardcoded logic.

<!-- fold:break -->

## The ReAct Pattern

<img src="_static/robots/study.png" alt="Research Robot" style="float:right; max-width:300px;margin:25px;" />

**ReAct** (Reasoning + Acting) is the most common agent architecture. The agent alternates between:

- **Thought**: "I need current data on this topic"
- **Action**: Call search tool
- **Observation**: Process search results
- **Thought**: "Now I can answer the question"
- **Action**: Generate response

ReAct agents can adapt their approach based on intermediate results, retry failed actions, and decompose complex tasks into steps.

<!-- fold:break -->

## When to Use Agents

**Good fit for agents:**
- Tasks requiring dynamic decisions based on intermediate results
- Open-ended questions needing research
- Integration of real-time information

**Consider simpler approaches when:**
- The task sequence is fixed and predictable
- Latency or cost is critical
- Simple classification or generation suffices

<!-- fold:break -->

## Do It Yourself

Ready to see these components in action?

Check out the
<button onclick="openOrCreateFileInJupyterLab('code/1-build-an-agent/intro_to_agents.ipynb');"><i class="fa-solid fa-flask"></i> Introduction to Agents</button>
notebook where you'll build your first agent from scratch!


