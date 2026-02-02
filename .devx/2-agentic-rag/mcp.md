# Implementing MCP

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

### MCP Architecture

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

### Why MCP Matters

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

### MCP in Practice

You may already be using MCP without realizing it. If you've used:

- **Claude Desktop** with file access or web browsing
- **Cursor** with its built-in browser or terminal tools
- **Custom integrations** via the MCP SDK

...you've experienced MCP in action.

The tools appear seamlessly in the model's context, ready to be invoked when needed, just like the ReAct pattern you learned earlier.

<!-- fold:break -->

## MCP: A Hands-On Implementation

<img src="_static/robots/magician.png" alt="MCP Magic Robot" style="float:right;max-width:300px;margin:25px;" />

Your RAG agent is great for answering questions from the knowledge base. But what about questions it can't answer? Let's **add web search** to your agent using the MCP pattern.

1. **Remote MCP Server** — Connect to Tavily's hosted MCP server at `mcp.tavily.com` via SSE.
2. **Local MCP Server** — Spin up your own MCP server locally using `mcp_server.py` and connect to it. 

We'll see how to do both. 

<!-- fold:break -->

### The Goal

Right now your agent only has one tool:
- `company_llc_it_knowledge_base` — Internal IT policies

We're going to add:
- `web_search` — Search the web for current information

**Same agent, more capabilities.**

<!-- fold:break -->

### Your Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/2-agentic-rag/rag_agent.py');"><i class="fa-brands fa-python"></i> code/2-agentic-rag/rag_agent.py</button> and fill in these blanks in the **MCP section**:

#### Exercise: Configure the MCP Connection

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'MCP_CONFIG = ');"><i class="fas fa-code"></i> MCP_CONFIG</button> — Configure the MCP client to connect to Tavily's remote MCP server using SSE transport.

<details>
<summary>🆘 Need some help?</summary>

```python
MCP_CONFIG = {
    "tavily": {
        "transport": "sse",
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}",
    }
}
```

This configuration connects to Tavily's hosted MCP server via SSE (Server-Sent Events). No local server installation required — just provide your API key in the URL.

</details>

<!-- fold:break -->

#### Exercise: Call the Search Tool via MCP

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'result = ...');"><i class="fas fa-code"></i> result</button> — Inside `web_search()`, call the Tavily search tool through the MCP client.

<details>
<summary>🆘 Need some help?</summary>

```python
tools = client.get_tools()
tavily_tool = next((t for t in tools if "search" in t.name.lower()), None)
result = await client.call_tool(tavily_tool.name, {"query": query})
```

The MCP client discovers available tools from the server, then invokes the search tool with your query.

</details>

<!-- fold:break -->

#### Exercise: Give New Tool to Agent

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'AGENT =');"><i class="fas fa-code"></i> AGENT</button> — Make this new tool available to the agent.

In addition to the `RETRIEVER_TOOL` you implemented previously, also add in `web_search` you just built.

<details>
<summary>🆘  Need some help?</summary>

```python
AGENT = create_react_agent(
    model=llm,
    tools=[RETRIEVER_TOOL, web_search],
    prompt=SYSTEM_PROMPT,
)
```

</details>

<!-- fold:break -->

### What This Enables

After filling in these blanks, your agent can:

| Question Type | Tool Used | Citation |
|---------------|-----------|----------|
| "How do I reset my password?" | Knowledge Base | [KB] |
| "What are the latest AI trends?" | Web Search | [Web] |

The agent decides which tool to use based on the question!

<!-- fold:break -->

## Test Your Agent

After completing the exercises, restart your agent:

```bash
cd code/2-agentic-rag
langgraph dev
```

In the <button onclick="launch('Simple Agents Client');"><i class="fa-solid fa-rocket"></i> Simple Agents Client</button>, try:

- "How do I connect to VPN?" → Should use [KB]
- "What's happening in AI news today?" → Should use [Web]

Wow! That was so much simpler than custom defining our tool implementation for Tavily web search back in Module 1. That's the value of MCP!

<!-- fold:break -->

#### (Optional) Exercise: Run your MCP Server Locally

For security and offline functionality, sometimes it may be useful to run your own MCP servers. Let's see how we can do that. 

In <button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', '# PART 2B');"><i class="fas fa-code"></i> # PART 2B</button> of ``rag_agent.py`` do the following: 

1. Comment out `PART 2A`
2. Uncomment `PART 2B`. Save the file.
3. Run the local MCP server: `cd code/2-agentic-rag && uvicorn mcp_server:app --reload --port 8000`
4. Restart the RAG agent: `cd code/2-agentic-rag && langgraph dev`
5. Test the agent in the Simple Agents Client.

You can see how to set up your local MCP server in the <button onclick="goToLineAndSelect('code/2-agentic-rag/mcp_server.py', 'mcp_server =');"><i class="fas fa-code"></i> mcp_server.py</button> file. 

<!-- fold:break -->

## What's Next

<img src="_static/robots/hiking.png" alt="Journey Robot" style="float:right;max-width:300px;margin:25px;" />

Congrats, you now know how to leverage MCP to integrate standardized tooling into your AI agents! 

In this section, you learned how to: 

- **Build your own MCP server** to expose custom tools
- **Connect existing MCP servers** to your agents
- **Connect locally running MCP servers** to your agents

Now that you understand what MCP is, why it matters, and how to implement it in code, you're ready to explore further. 

Continue to [Agent Skills](skills.md) to learn about how to impart your agent with custom defined skills to better align its tool calling. 
