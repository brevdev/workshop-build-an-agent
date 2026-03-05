# Introduction to Deep Agents

<img src="_static/robots/magician.png" alt="Deep Agent Robot" style="float:right;max-width:300px;margin:25px;" />

In Modules 1 through 4, we built increasingly capable agents — from a report generator to a RAG-powered help desk to a customized bash agent. Each used the same fundamental pattern: a **ReAct loop** where a single model reasons, calls a tool, observes the result, and repeats.

These agents are powerful, but they're **shallow**. In this module, we'll explore what happens when we go *deep*.

<!-- fold:break -->

## The Story So Far

Here's a quick recap of what you've accomplished across the workshop:

| Module | What You Built | Key Pattern |
|--------|---------------|-------------|
| 1 | Report generation agent | ReAct loop with tool calling |
| 2 | RAG-augmented IT help desk agent | Retrieval + generation |
| 3 | Evaluation pipelines for agent quality | LLM-as-judge, RAGAS metrics |
| 4 | Customized CLI agent via SDG + RLVR  | Domain specialization |

But all of these agents share a common architecture: a **single model in a single loop**, with all state living inside the context window. We call these "shallow" agents — not because they're simple, but because their reasoning stays within a single layer of execution.

<!-- fold:break -->

### The Shallow Agent Pattern

Every agent we've built so far follows the same architecture:

```
User → Model → Tool → Model → Tool → ... → Response
```

One model. One context window. One tool at a time. The bash agent from Module 4 pushed this pattern to its limit — it could execute shell commands, but it still operated in a single flat loop.

<!-- fold:break -->

#### Shallow Agent Capabilities

Your ReAct agents are genuinely capable. They can:

- **Dynamically select tools** — Choose the right tool for each step based on reasoning
- **Execute multi-step tasks** — Chain together 5-15 tool calls to complete a task
- **Ground responses** — Use retrieved information rather than hallucinating
- **Produce structured output** — Generate formatted reports, JSON, or other structured results

These capabilities cover a wide range of real-world tasks. For focused problems that fit within a single conversation — answering questions, generating short reports, triaging requests — shallow agents are often the right choice.

<!-- fold:break -->

#### Shallow Agent Limitations

But what happens when the task outgrows the architecture? The shallow agent pattern breaks down because it can't:

- **Plan ahead** — Break down a complex task, track progress over long time horizons
- **Delegate work** — Spawn a sub-agent to handle a sub-task in parallel
- **Manage files** — Read, write, edit, search, and organize files across a project
- **Manage its own context** — Summarize long conversations to avoid running out of tokens

For simple tasks, this is fine. But real-world production tasks — "research this topic, write code, test it, fix any bugs, and write documentation" — require something more.

<details>
<summary><strong>A concrete example of shallow agent breakdown</strong></summary>

Consider asking your Module 1 report generation agent: "Research the competitive landscape of AI agent frameworks, comparing at least 10 frameworks across architecture, pricing, ecosystem, and adoption. Produce a detailed report with citations."

Here's what would likely happen:

1. The agent searches for the first few frameworks and gets good results
2. By framework 5-6, earlier search results are being pushed out of context
3. The agent starts repeating searches it already did (it forgot the results)
4. The comparison table becomes inconsistent (some frameworks have pricing info, others don't)
5. The final report is patchy — strong on the last few frameworks researched, weak on the first ones

A human researcher would take notes, organize by subtopic, and check their work against their outline. The shallow agent can't do any of this.

</details>

> Think about how a human handles complex tasks. You don't try to hold everything in your head. You:
> - Write down a plan and check items off as you go
> - Delegate specialized work to colleagues
> - Take notes and refer back to them
> - Follow established procedures for common workflows
> 
> These are exactly the capabilities that deep agents add to the LLM loop.

<!-- fold:break -->

## What Makes an Agent "Deep"?

A **deep agent** goes beyond the flat ReAct loop. It has built-in capabilities that make it autonomous enough to handle complex, multi-step tasks without constant human guidance:

| Capability | Shallow Agent | Deep Agent |
|---|---|---|
| **Planning** | Limited to CoT reasoning | `write_todos` for task breakdown and tracking |
| **File System** | Limited tooling (e.g., read) | Full suite: `read`, `write`, `edit`, `ls`, `glob`, `grep` |
| **Shell Access** | Possible with custom implementation | Built-in `execute` with sandboxing |
| **Sub-Agents** | None | `task` tool to delegate work to specialized agents |
| **Context Management** | Fixed window, truncation | Auto-summarization when conversations get long |
| **Skills** | Primarily relies on system prompts | Loadable markdown methodology files |

Deep agents aren't just agents with more tools — they're agents with an **architecture** designed for complex, autonomous work.

<!-- fold:break -->

### From Bash Agent to Deep Agent

Remember the bash agent from Module 4? It could translate natural language into shell commands. That was a big step — an agent touching the real system.

Now imagine that agent with the following capabilities:

1. **Plan** — "I need to research GPU optimization, write a benchmark script, run it, analyze results, and write a report."
2. **Execute** — Write files, run commands, read outputs, debug errors
3. **Delegate** — "Let me send the research task to a sub-agent while I start writing the code."
4. **Adapt** — If the context gets too long, summarize and continue
5. **Learn** — Load skills (markdown files) that teach it specific domains and methodologies

That's a deep agent. And that's what we'll build in this module.

<!-- fold:break -->

## The Deep Agents Library

We'll use [**langchain-ai/deepagents**](https://github.com/langchain-ai/deepagents) — an open-source agent harness built on LangChain and LangGraph. It's designed to be batteries-included:

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model=model,
    tools=[tavily_search],
    system_prompt="You are a helpful assistant.",
    backend=LocalShellBackend(root_dir="/workspace"),
)
```

One function call gives you an agent with planning, filesystem access, shell execution, sub-agents, and context management — all wired up and ready to go.

> To learn more about NVIDIA's integrations with LangChain, check out [these docs](https://docs.langchain.com/oss/python/integrations/providers/nvidia). 

<!-- fold:break -->

## What You'll Learn

<img src="_static/robots/plumber.png" alt="Builder Robot" style="float:right;max-width:300px;margin:25px;" />

Here's what's ahead in this module, page by page:

**[What Are Deep Agents?](deep_agents)** — The four pillars of deep agent architecture, real-world applications, and how the deepagents library implements it all.

**[Set Up the Agent Builder](setup_agent_builder)** — Get the Deep Agent Builder UI running so you have an interactive environment for the hands-on exercises.

**[Build a Deep Agent](build_deep_agents)** — Hands-on with the deepagents library. You'll build a deep agent step by step, filling in the core functions that power it, and test it using an interactive UI with drag-and-drop tools.

**[Sandboxing and Security](sandboxing_security)** — How to run autonomous agents safely. You'll learn about sandboxing patterns, security architecture, and defense-in-depth strategies for production deployment.

> Head over to [What Are Deep Agents](deep_agents) to dive into the architecture!
