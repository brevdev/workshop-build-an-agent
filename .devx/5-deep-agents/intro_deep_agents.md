# Introduction to Deep Agents

<img src="_static/robots/magician.png" alt="Deep Agent Robot" style="float:right;max-width:300px;margin:25px;" />

In Modules 1 through 4, we built increasingly capable agents — from a report generator to a RAG-powered help desk to a customized bash agent. Each used the same fundamental pattern: a **ReAct loop** where a single model reasons, calls a tool, observes the result, and repeats.

These agents are powerful, but they're **shallow**. In this module, we'll explore what happens when we go *deep*.

<!-- fold:break -->

## The Shallow Agent Pattern

Every agent we've built so far follows the same architecture:

```
User → Model → Tool → Model → Tool → ... → Response
```

One model. One context window. One tool at a time. The bash agent from Module 4 pushed this pattern to its limit — it could execute shell commands, but it still operated in a single flat loop. It couldn't:

- **Plan ahead** — Break a complex task into steps and track progress
- **Delegate work** — Spawn a sub-agent to handle a sub-task in parallel
- **Manage files** — Read, write, edit, search, and organize code across a project
- **Manage its own context** — Summarize long conversations to avoid running out of tokens

For simple tasks, this is fine. But real-world production tasks — "research this topic, write code, test it, fix any bugs, and write documentation" — require something more.

<!-- fold:break -->

## What Makes an Agent "Deep"?

<img src="_static/robots/supervisor.png" alt="Supervisor Robot" style="float:right;max-width:300px;margin:25px;" />

A **deep agent** goes beyond the flat ReAct loop. It has built-in capabilities that make it autonomous enough to handle complex, multi-step tasks without constant human guidance:

| Capability | Shallow Agent | Deep Agent |
|---|---|---|
| **Planning** | None — improvises each step | `write_todos` for task breakdown and tracking |
| **File System** | Maybe one tool (e.g., read) | Full suite: `read`, `write`, `edit`, `ls`, `glob`, `grep` |
| **Shell Access** | Maybe (with HITL) | Built-in `execute` with sandboxing |
| **Sub-Agents** | None | `task` tool to delegate work to specialized agents |
| **Context Management** | Fixed window, truncation | Auto-summarization when conversations get long |
| **Skills** | Hardcoded prompts | Loadable markdown methodology files |

Deep agents aren't just agents with more tools — they're agents with an **architecture** designed for complex, autonomous work.

<!-- fold:break -->

## From Bash Agent to Deep Agent

Remember the bash agent from Module 4? It could translate natural language into shell commands. That was a big step — an agent touching the real system.

Now imagine an agent that can:

1. **Plan** — "I need to research GPU optimization, write a benchmark script, run it, analyze results, and write a report."
2. **Execute** — Write files, run commands, read outputs, fix errors
3. **Delegate** — "Let me send the research task to a sub-agent while I start writing the code."
4. **Adapt** — If the context gets too long, summarize and continue
5. **Learn** — Load skills (markdown files) that teach it specific methodologies

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

<!-- fold:break -->

## What We'll Build

<img src="_static/robots/plumber.png" alt="Builder Robot" style="float:right;max-width:300px;margin:25px;" />

In this module, you'll:

1. **Understand** the architecture of deep agents and how they differ from shallow ReAct agents
2. **Explore** advanced capabilities — MCP tools, skills, sub-agent spawning, and middleware
3. **Build** a deep agent step by step, filling in the core functions that power it
4. **Test** your agent using an interactive Deep Agent Builder UI with drag-and-drop tools
5. **Secure** your agent with Docker-based sandboxing and understand production deployment

By the end, you'll have a production-grade agent that can plan, code, execute, delegate, and self-manage — running safely in an isolated environment.

> Head over to [What Are Deep Agents](deep_agents) to dive into the architecture!
