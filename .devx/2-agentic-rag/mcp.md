# Introduction to MCP

<img src="_static/robots/MCP.png" alt="MCP Robot Character" style="float:right;max-width:300px;margin:25px;" />

The Model Context Protocol (MCP) is an open standard developed by Anthropic that defines how AI agents connect to external tools, data sources, and services. Think of it as a universal adapter that lets your agent plug into anything.

In this lesson, we'll explore what MCP is, why it matters, and how it transforms the way we build agent capabilities.

<!-- fold:break -->

## The Tool Problem

<img src="_static/robots/toolprobem.png" alt="Tools Robot" style="float:left;max-width:250px;margin:25px;" />

In the previous sections, you built tools directly into your agent. The Tavily search tool and the RAG retriever were Python functions defined in your codebase.

This works, but it has limitations:

- **Tight coupling** — Tools live inside your agent's code
- **Duplication** — Every agent project rebuilds the same integrations
- **No ecosystem** — Hard to share and reuse tools across projects

What if tools could be developed, shared, and connected independently of any specific agent?

<!-- fold:break -->

## Enter MCP

MCP solves this by standardizing how agents communicate with external capabilities. Instead of building tools into your agent, you connect to **MCP Servers** that expose tools, resources, and prompts.

<center>

| Traditional Tools | MCP Approach |
|-------------------|--------------|
| Tools bundled in agent code | Tools run as separate services |
| One-off implementations | Reusable across any MCP client |
| Hardcoded integrations | Discoverable at runtime |

</center>

<!-- fold:break -->

## MCP Architecture

<img src="_static/robots/datacenter.png" alt="Architecture Robot" style="float:right;max-width:300px;margin:25px;" />

MCP follows a client-server model:

- **MCP Hosts** — Applications like Claude Desktop, Cursor, or your custom agent
- **MCP Clients** — Protocol handlers that maintain connections to servers  
- **MCP Servers** — Lightweight services that expose tools, resources, and prompts

The protocol defines three core primitives:

1. **Tools** — Functions the model can invoke (like our Tavily search)
2. **Resources** — Data the model can read (files, database records, API responses)
3. **Prompts** — Reusable prompt templates with arguments

<!-- fold:break -->

## Why MCP Matters

<img src="_static/robots/strong.png" alt="Power Robot" style="float:left;max-width:250px;margin:25px;" />

MCP is transforming the agent ecosystem:

**For Developers:**
- Build a tool once, use it everywhere
- Connect to a growing library of pre-built MCP servers
- Standardized patterns reduce boilerplate

**For Organizations:**
- Centralized tool governance and security
- Consistent integration patterns across teams
- Tools can be updated without redeploying agents

**For the Ecosystem:**
- Open source MCP servers for databases, APIs, file systems
- Commercial MCP servers for enterprise integrations
- A shared language for agent capabilities

<!-- fold:break -->

## MCP in Practice

You may already be using MCP without realizing it. If you've used:

- **Claude Desktop** with file access or web browsing
- **Cursor** with its built-in browser or terminal tools
- **Custom integrations** via the MCP SDK

...you've experienced MCP in action.

The tools appear seamlessly in the model's context, ready to be invoked when needed, just like the ReAct pattern you learned earlier.

<!-- fold:break -->

## What's Next

<img src="_static/robots/hiking.png" alt="Journey Robot" style="float:right;max-width:300px;margin:25px;" />

Now that you understand what MCP is and why it matters, you're ready to explore further:

- **Build your own MCP server** to expose custom tools
- **Connect existing MCP servers** to your agents
- **Explore the MCP ecosystem** of pre-built integrations

The skills you learned building RAG tools transfer directly, MCP is just a standardized way to package and share those same capabilities.

Welcome to the future of agent development! 🚀
