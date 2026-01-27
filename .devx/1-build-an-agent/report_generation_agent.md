# Report Generation Agent

<img src="_static/robots/surf.png" alt="Research Agent Robot" style="float:right; max-width:300px;margin:25px;" />

Now that you have a grip on the basics of agents, let's check out a more true-to-life agent architecture with your own report generation agent!
The report generation agent will automatically research any topic and write a professional report.

<!-- fold:break -->

## The Components in Action

Remember, there are four primary components to an agent: the model, tools, memory/state, and routing.

In this exercise, we wire up all four:
- **Model**: NVIDIA Nemotron 3 Nano (30B), accessed via NVIDIA's API
- **Tools**: A web search function using the Tavily Search Engine API
- **Memory**: Managed automatically by LangChain as conversation history
- **Routing**: Handled by LangChain's agent framework (no manual loop needed) 

<!-- fold:break -->

## Tools

A prebuilt tool called <button onclick="goToLineAndSelect('code/1-build-an-agent/tools.py', 'async def search_tavily');"><i class="fas fa-code"></i> search_tavily</button> is provided.

Similar to our last exercise, this is just a Python function. This function calls the Tavily API and then formats the results for the model.

Because we are using LangGraph, we can use the `@tool` decorator to automatically create the tool JSON definition.

<!-- fold:break -->

## Agent Logic

<img src="_static/robots/operator.png" alt="Routing Robot" style="float:right; max-width:300px;margin:25px;" />

In the previous exercise, we manually routed messages in a Jupyter notebook. 

The user message went to the model. The model's response included tool calls. Those tools were called and the results sent back to the model. When the model decided it was complete, the final response was returned.

Because this logic is so common, we will use LangChain to handle this routing automatically. This logic is constructed in <button onclick="openOrCreateFileInJupyterLab('code/1-build-an-agent/docgen_agent.py');"><i class="fa-brands fa-python"></i> docgen_agent.py</button>. Let's review that code.

<!-- fold:break -->

<button onclick="goToLineAndSelect('code/1-build-an-agent/docgen_agent.py', 'llm = ');"><i class="fas fa-code"></i> llm = ChatOpenAI( ... )</button> defines the **MODEL** we will use.

<button onclick="goToLineAndSelect('code/1-build-an-agent/docgen_agent.py', 'tools = ');"><i class="fas fa-code"></i> tools = [ ... ]</button> creates a list of all the **TOOLS** available to our agent.

<button onclick="goToLineAndSelect('code/1-build-an-agent/docgen_agent.py', 'system_prompt = ');"><i class="fas fa-code"></i> system_prompt = """ ... """</button> is the **SYSTEM PROMPT** where we define this agent's personality and behavior.

<button onclick="goToLineAndSelect('code/1-build-an-agent/docgen_agent.py', 'agent = ');"><i class="fas fa-code"></i> agent = create_agent( ... )</button> is where LangChain takes our components and creates an agent with standard message **ROUTING**. This creates a ReAct style agent.

<!-- fold:break -->

## Understanding the System Prompt

<img src="_static/robots/study.png" alt="Studying Robot" style="float:right; max-width:280px;margin:25px;" />

Take a moment to read through the system prompt in `docgen_agent.py`. Notice how it:

1. **Defines the role**: "You are ReportWriter, a research-and-writing agent"
2. **Sets quality standards**: "Never invent sources, quotes, statistics, or events"
3. **Guides tool usage**: "If the topic requires up-to-date facts... you MUST use tavily_search"
4. **Specifies output format**: The expected report structure with sections and citations

This prompt shapes everything the agent does. If you wanted a more casual tone, stricter fact-checking, or a different report format, you'd change this prompt - not the code.

**Try experimenting**: After completing the exercise, try modifying the system prompt and see how the agent's behavior changes.

<!-- fold:break -->

## Generating a report

Now that our agent code is built, we just need to build the client that invokes this agent and generates a report. Complete the client code in <button onclick="openOrCreateFileInJupyterLab('code/1-build-an-agent/docgen_client.ipynb');"><i class="fa-solid fa-flask"></i> Document Generation Client</button>.

*🤩 Extra Credit:* Inspect the whole state at the end of the invocation to see all of the steps taken during execution.

<!-- fold:break -->

## Peeking Under the Hood

Agents can feel like black boxes. The model makes decisions we don't directly see. Here's how to understand what's happening:

### Inspect the State

After running your agent, `state["messages"]` contains the full conversation history, including:
- The original user request
- Each tool call the agent made
- The results returned from those tools
- The agent's reasoning (if using a model that exposes it)
- The final response

Try printing `state["messages"]` to see the complete trace of your agent's work.

### What to Watch For

As you experiment with your agent, keep an eye out for:

- **Empty searches**: Did the agent search but find nothing useful?
- **Repeated queries**: Is the agent searching for the same thing multiple times?
- **Missing citations**: The system prompt asks for sources - are they actually in the output?
- **Unexpected tool use**: Did the agent use tools in ways you didn't anticipate?

These observations will help you refine your system prompt and tool descriptions over time.

> **Looking Ahead**: In Module 3, you'll learn systematic ways to evaluate agent quality beyond manual inspection.

<!-- fold:break -->

## Complete!

In this exercise, you were introduced to production-ready agent code with LangChain and wrote the client code that invokes that agent. This code is simpler than our first agent, but it's doing the same steps under the hood!

> **Note on Terminology**: This workshop uses both "LangChain" and "LangGraph" - they're related. LangGraph is built on top of LangChain and provides tools specifically for building stateful, multi-step applications like agents. When we use `create_agent`, we're using LangChain utilities that leverage LangGraph under the hood.

Continue to [Next Steps](next_steps.md) to review what you've learned and see what's coming in the next modules!
