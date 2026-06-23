<div class="dx-hero" data-eyebrow="MODULE 02 / 04 - MCP" data-title="Implementing MCP"></div>

The Model Context Protocol (MCP) is an open standard developed by Anthropic that defines how AI agents connect to external tools, data sources, and services. Think of it as a universal adapter that lets your agent plug into anything.

In this lesson, we'll explore what MCP is, why it matters, and how it transforms the way we build agent capabilities.

<!-- fold:break -->

<div class="dx-island dx-reveal">
  <p class="dx-island-title">THE TOOL PROBLEM</p>
  <p>In the previous sections, you built tools directly into your agent - the Tavily search and the RAG retriever were Python functions in your codebase. That works, but it has limits:</p>
  <p><span class="dx-chip">TIGHT COUPLING</span> Tools live inside your agent's code.</p>
  <p><span class="dx-chip">DUPLICATION</span> Every agent project rebuilds the same integrations.</p>
  <p><span class="dx-chip">NO ECOSYSTEM</span> Hard to share and reuse tools across projects.</p>
  <p>What if tools could be developed, shared, and connected independently of any specific agent?</p>
</div>

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

MCP is transforming the agent ecosystem:

<div class="dx-bento dx-reveal">
  <div class="dx-cell"><h4>FOR DEVELOPERS</h4>Build a tool once, use it everywhere. Tap a growing library of pre-built MCP servers. Standardized patterns cut boilerplate.</div>
  <div class="dx-cell"><h4>FOR ORGANIZATIONS</h4>Centralized tool governance and security. Consistent integration across teams. Update tools without redeploying agents.</div>
  <div class="dx-cell is-wide"><h4>FOR THE ECOSYSTEM</h4>Open-source MCP servers for databases, APIs, and file systems; commercial servers for enterprise; a shared language for agent capabilities.</div>
</div>

<!-- fold:break -->

### MCP in Practice

You may already be using MCP without realizing it. If you've used:

- **Claude Desktop** with file access or web browsing
- **Cursor** with its built-in browser or terminal tools
- **Custom integrations** via the MCP SDK

...you've experienced MCP in action.

The tools appear seamlessly in the model's context, ready to be invoked when needed, just like the ReAct pattern you learned earlier.

<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">You connect your agent to Tavily's hosted MCP server for web search. Where does the search tool's code actually run?</p>
  <button class="dx-quiz-opt" data-fb="That's the pre-MCP approach - bundling the tool's implementation into your agent's codebase. MCP exists precisely to decouple the two.">Inside your agent's process, after MCP copies the tool code into it</button>
  <button class="dx-quiz-opt" data-right data-fb="Right. The tool lives and runs on the MCP server (here, Tavily's hosted one); your agent just discovers and calls it over the protocol. Build once, use anywhere.">On the MCP server; your agent discovers and calls it over the protocol</button>
  <button class="dx-quiz-opt" data-fb="The LLM never executes tool code - it only requests a call. With MCP, the MCP server runs the tool, not the model.">The LLM runs it directly as part of generating its response</button>
</div>

<!-- fold:break -->

## MCP: A Hands-On Implementation

<img src="_static/robots/magician.png" alt="MCP Magic Robot" style="float:right;max-width:300px;margin:25px;" />

Your RAG agent is great for answering questions from the knowledge base. But what about questions it can't answer? Let's **add web search** to your agent using the MCP pattern.

1. **Remote MCP Server** — Connect to Tavily's hosted MCP server at `mcp.tavily.com` via stdio.
2. **Local MCP Server** — Spin up your own MCP server locally using `mcp_server.py` and connect to it. 

We'll see how to do both. 

<!-- fold:break -->

### The Goal

<img src="_static/robots/MCP.png" alt="MCP Robot Character" style="float:right;max-width:300px;margin:25px;" />

Right now your agent only has one tool:
- `company_llc_it_knowledge_base` — Internal IT policies

We're going to add:
- `web_search` — Search the web for current information

**Same agent, more capabilities.**

<!-- fold:break -->

### Your Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/2-agentic-rag/rag_agent.py');"><i class="fa-brands fa-python"></i> code/2-agentic-rag/rag_agent.py</button> and fill in these blanks in the **MCP section**:

#### Exercise: Configure the MCP Connection

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'MCP_CONFIG = ');"><i class="fas fa-code"></i> MCP_CONFIG</button> — Configure the MCP client to connect to Tavily's remote MCP server using stdio transport.

The mcp-remote package acts as a bridge, allowing stdio-based clients to connect to remote MCP servers over HTTP.

<details>
<summary>🆘 Need some help?</summary>

```python
MCP_CONFIG = {
    "tavily": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "mcp-remote", f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"]
    }
}
```

This configuration connects to Tavily's hosted MCP server URL. No local server installation required — just provide your API key in the URL.

</details>

<!-- fold:break -->

#### Exercise: Call the Search Tool via MCP

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'result = ...');"><i class="fas fa-code"></i> result</button> — Inside `web_search()`, call the Tavily search tool through the MCP client.

<details>
<summary>🆘 Need some help?</summary>

```python
result = await session.call_tool("tavily_search", {"query": query})
```

The `session.call_tool()` method invokes the Tavily search tool on the remote MCP server with your query.

</details>

<!-- fold:break -->

#### Exercise: Give New Tool to Agent

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'AGENT =');"><i class="fas fa-code"></i> AGENT</button> — Update the `AGENT` definition to include your new tool alongside the existing one.

In addition to the `RETRIEVER_TOOL` you implemented previously, also add in `web_search` you just built. This replaces your earlier definition — we're expanding the agent's toolkit.

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

After filling in these blanks, your agent can now differentiate between the following queries:

<div class="dx-term dx-reveal">
  <span class="dx-term-title">rag_agent</span>
  <span class="dx-term-line" data-kind="prompt">How do I reset my password?</span>
  <span class="dx-term-line" data-kind="think" data-delay="300">Internal IT policy - the knowledge base should have this.</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[action] company_llc_it_knowledge_base("reset password")</span>
  <span class="dx-term-line" data-kind="answer" data-delay="350">...follow the self-service reset steps. [KB]</span>
  <span class="dx-term-line" data-kind="prompt" data-delay="500">What are the latest AI trends?</span>
  <span class="dx-term-line" data-kind="think" data-delay="300">Not in our IT policies, and it needs current info - use web search.</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[action] web_search("latest AI trends 2025")</span>
  <span class="dx-term-line" data-kind="answer" data-delay="350">...here are the current trends... [Web]</span>
</div>

The agent decides which tool to use based on the question!

<!-- fold:break -->

## Test Your Agent

After completing the exercises, restart your agent in the <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button>:

Make sure you're in the `code/2-agentic-rag` directory:

```bash
cd code/2-agentic-rag
```

And start your Agent API with the LangGraph CLI.

```bash
langgraph dev
```

In the <button onclick="launch('Simple Agents Client');"><i class="fa-solid fa-rocket"></i> Simple Agents Client</button>, try:

- "How do I connect to VPN?" → Should use [KB]
- "What's happening in AI news today?" → Should use [Web]

Wow! Remember that custom, complicated Tavily tool implementation from Module 1? Now, we can eliminate the need for that by decoupling the tool from the agent. Build once, use anywhere - That's the value of MCP!

<!-- fold:break -->

#### (Optional) Exercise: Run your MCP Server Locally

For security and offline functionality, sometimes it may be useful to run your own MCP servers locally. Let's see how we can do that.

Take a look at the local MCP server implementation in the <button onclick="goToLineAndSelect('code/2-agentic-rag/mcp_server.py', 'mcp_server =');"><i class="fas fa-code"></i> mcp_server.py</button> file. 

Once you're ready, run the MCP server locally in a new <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> window. 

```bash
cd code/2-agentic-rag && uvicorn mcp_server:app --reload --port 8000
```

In <button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', '# PART 2B');"><i class="fas fa-code"></i> # PART 2B</button> of ``rag_agent.py`` do the following: 

1. Comment out `PART 2A`
2. Uncomment `PART 2B`. Save the file.
3. Restart the RAG agent: `cd code/2-agentic-rag && langgraph dev`
4. Test the agent in the Simple Agents Client. 

Responses should now use the tool located on our locally running MCP server! 

<!-- fold:break -->

## What's Next

<img src="_static/robots/hiking.png" alt="Journey Robot" style="float:right;max-width:300px;margin:25px;" />

Congrats, you now know how to leverage MCP to integrate standardized tooling into your AI agents! 

In this section, you learned how to: 

- **Connect remote MCP servers** to your agents
- **Connect local MCP servers** to your agents
- **Explore how MCP servers are built** to expose custom tools

Now that you understand what MCP is, why it matters, and how to implement it in code, you're ready to explore further. 

Continue to [Agent Skills](skills.md) to learn about how to impart your agent with custom defined skills to better align its tool calling. 
