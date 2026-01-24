# Report Generation Agent

<img src="_static/robots/surf.png" alt="Research Agent Robot" style="float:right; max-width:300px;margin:25px;" />

Now that you have a grip on the basics of agents, let's check out a more true-to-life agent architecture with your own report generation agent!
The report generation agent will automatically research any topic and write a professional report.

<!-- fold:break -->

## The components of an agent

Remember, there are four primary components to an agent: the model, tools, memory/state, and message routing.

In this excercise, we will use a tool that allows the model to search Tavily for research. Instead of routing messages from scratch, we will use LangChain to orchestrate the agent internals.

Now is also a good time to introduce a new concept: `System Prompts`. System Prompts are special messages in the history that are only read by the model. They are used to define the agent's job. Changing the System Prompt will change how the agent responds. 

<!-- fold:break -->

## Tools

A prebuilt tool called <button onclick="goToLineAndSelect('code/1-build-an-agents/tools.py', 'async def search_tavily');"><i class="fas fa-code"></i> search_tavily</button> is provided.

Similar to our last excercise, this is just a Python function. This function calls the Tavily API and then formats the results for the model.

Because we are using LangGraph, we can use the `@tool` decorator to automatically create the tool JSON definition.

<!-- fold:break -->

## Agent Logic

<img src="_static/robots/operator.png" alt="Routing Robot" style="float:right; max-width:300px;margin:25px;" />

In the last excercise, we manually routed messages in a Jupyter notebook. 

The user message went to the model. The model's response included tool calls. Those tools were called and the results sent back to the model. When the model dedicided it was complete, the final response was returned.

Because this logic is so common, we will use LangChain to handle this routing automatically. This logic is constructed in <button onclick="openOrCreateFileInJupyterLab('code/1-build-an-agents/docgen_agent.py');"><i class="fa-brands fa-python"></i> docgen_agent.py</button>. Let's review that code.

<!-- fold:break -->

<button onclick="goToLineAndSelect('code/1-build-an-agents/docgen_agent.py', 'llm = ');"><i class="fas fa-code"></i> llm = ChatOpenAI( ... )</button> defines the **MODEL** we will use.

<button onclick="goToLineAndSelect('code/1-build-an-agents/docgen_agent.py', 'tools = ');"><i class="fas fa-code"></i> tools = [ ... ]</button> creates a list of all the **TOOLS** available to our agent.

<button onclick="goToLineAndSelect('code/1-build-an-agents/docgen_agent.py', 'system_prompt = ');"><i class="fas fa-code"></i> system_prompt = """ ... """</button> is that **SYSTEM PROMPT** where we define this agent's job.

<button onclick="goToLineAndSelect('code/1-build-an-agents/docgen_agent.py', 'agent = ');"><i class="fas fa-code"></i> agent = create_agent( ... )</button> is where LangChain takes our components and creates an agent with standard message **ROUTING**. This creates a ReAct style agent, but we will discuss that more in the next lesson.

<!-- fold:break -->

## Generating a report

Now that are agent code is built, we just need to build the client that invokes this agent and generates a report. Complete the client code in <button onclick="openOrCreateFileInJupyterLab('code/1-build-an-agents/docgen_client.ipynb');"><i class="fa-solid fa-flask"></i> Document Generation Client</button>.

*🤩 Extra Credit:* Inspect the whole state at the end of the invocation to see all of the steps taken during execution.

<!-- fold:break -->

## Complete!

In this excercise, you were introduced to production ready agent code with LangChain and wrote the client code that invoked that agent. This code was a far cry simpler than our first agent, but its actually doing the same steps under the hood!
