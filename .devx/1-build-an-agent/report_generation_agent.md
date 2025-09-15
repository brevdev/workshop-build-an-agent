# Report Generation Agent

<img src="_static/robots/surf.png" alt="Research Agent Robot" style="float:right; max-width:300px;margin:25px;" />

Now that you have a grip on the basics of agents, let's check out a more true-to-life agent architecture with your own report generation agent!
The report generation agent automatically researches any topic, creates an outline, writes comprehensive sections, and delivers a complete professional report.

## Under the Hood

The report generation agent works in three simple steps:

1. **Research** - Uses a research agent to search the web using Tavily
2. **Plan** - A single LLM call creates an outline based on the research findings
3. **Write** - Use an agent to write each section and do more research as needed

That's it! The agent handles all the complexity behind the scenes, delivering a professional report from just a topic prompt.

## Experience It in Action

<button onclick="openOrCreateFileInJupyterLab('code/agent_client.ipynb');"><i class="fa-solid fa-flask"></i> Report Agent</button>

See the report generation in action! Prompt the agent to search for information, gather relevant sources, and synthesize its findings. 
