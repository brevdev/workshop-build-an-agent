# Using MCP

<img src="_static/robots/magician.png" alt="MCP Magic Robot" style="float:right;max-width:300px;margin:25px;" />

Your RAG agent is great for answering questions from the knowledge base. But what about questions it can't answer? Let's **add web search** to your agent using the MCP pattern.

<!-- fold:break -->

## The Goal

Right now your agent only has one tool:
- `company_llc_it_knowledge_base` — Internal IT policies

We're going to add:
- `web_search` — Search the web for current information

**Same agent, more capabilities.**

<!-- fold:break -->

## Your Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/rag_agent.py');"><i class="fa-brands fa-python"></i> code/rag_agent.py</button> and fill in these blanks in the **MCP section**:

### Exercise 4: Initialize the Tavily Client

<button onclick="goToLineAndSelect('code/rag_agent.py', 'tavily_client = ');"><i class="fas fa-code"></i> tavily_client</button> — Create the Tavily client with your API key.

<details>
<summary>🆘 Need some help?</summary>

```python
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
```

</details>

<!-- fold:break -->

### Exercise 5: Call the Search API

<button onclick="goToLineAndSelect('code/rag_agent.py', 'results = ');"><i class="fas fa-code"></i> results</button> — Inside `web_search()`, call the Tavily API.

<details>
<summary>🆘 Need some help?</summary>

```python
results = tavily_client.search(query=query, max_results=5)
```

</details>

<!-- fold:break -->

## What This Enables

After filling in these blanks, your agent can:

| Question Type | Tool Used | Citation |
|---------------|-----------|----------|
| "How do I reset my password?" | Knowledge Base | [KB] |
| "What are the latest AI trends?" | Web Search | [Web] |

The agent decides which tool to use based on the question!

<!-- fold:break -->

## Test Your Agent

After completing exercises 4-5, restart your agent:

```bash
cd code
langgraph dev
```

In the <button onclick="launch('Simple Agents Client');"><i class="fa-solid fa-rocket"></i> Simple Agents Client</button>, try:

- "How do I connect to VPN?" → Should use [KB]
- "What's happening in AI news today?" → Should use [Web]

Continue to [Introduction to Skills](skills.md).
