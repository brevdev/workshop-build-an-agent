# The Bash Agent

<img src="_static/robots/operator.png" alt="Bash Agent Robot" style="float:right;max-width:300px;margin:25px;" />

Before we can customize an agent, we need to truly understand how it works. In this lesson, you'll get hands-on experience with a **Bash Agent**—an AI assistant that translates natural language into shell commands.

This isn't just any demo agent. The Bash Agent was carefully chosen as our customization target because it produces clear, observable behavior that makes it easy to identify where improvements are needed.

<!-- fold:break -->

## Why a Bash Agent?

Think about how you interact with your computer's terminal. Commands like `ls -la`, `grep -r "error" ./logs`, or `find . -name "*.py"` are powerful—but they require you to remember exact syntax, flags, and options.

A Bash Agent flips this paradigm. Instead of memorizing arcane command syntax, you simply describe what you want:

- *"Show me all the Python files in this directory"*
- *"Find the largest files here"*  
- *"Create a folder called 'experiments' and list what's inside"*

The agent understands your intent and translates it into the appropriate shell commands.

<!-- fold:break -->

## The Perfect Customization Candidate

<img src="_static/robots/wrench.png" alt="Customization" style="float:left;max-width:300px;margin:25px;" />

We chose a Bash Agent for this customization module for several important reasons:

**Observable Behavior**: Shell commands produce clear, measurable outputs. When the agent runs `ls`, you can see exactly what it did and whether it succeeded. This makes evaluation straightforward.

**Safety Boundaries**: The agent operates within a restricted set of allowed commands—no `rm -rf /` disasters here! This teaches an important lesson about designing safe, constrained agents.

**Real-World Applicability**: Many AI engineers use agents like this daily to automate repetitive system tasks, explore codebases, and manage files.

**Clear Improvement Opportunities**: As you'll discover, the agent sometimes makes suboptimal choices. These "rough edges" are perfect targets for the customization techniques you'll learn.

<!-- fold:break -->

## Agent Architecture Overview

The Bash Agent follows the **ReAct (Reason + Act)** pattern, one of the most powerful and widely-used agent architectures:

<center>

| Step | Description |
|------|-------------|
| **Reason** | The LLM analyzes your request and thinks about what needs to be done |
| **Act** | The agent calls a tool (in this case, executes a bash command) |
| **Observe** | The agent sees the result of the command |
| **Repeat** | If the task isn't complete, the cycle continues |

</center>

This architecture is implemented using **LangGraph**, a framework for building stateful, multi-step AI applications. You'll see how the pieces fit together in the hands-on notebook.

<!-- fold:break -->

## Safety First: Human-in-the-Loop

<img src="_static/robots/debug.png" alt="Safety Check" style="float:right;max-width:300px;margin:25px;" />

Running arbitrary shell commands is inherently risky. What if the agent misunderstands your request?

The Bash Agent implements a **Human-in-the-Loop (HITL)** pattern. Before executing any command, it asks for your explicit approval:

```
You: "List all files here"
   ↓
Agent thinks: "I should run 'ls -la'"
   ↓
System: "Execute 'ls -la'? [y/N]:"
   ↓
You type 'y' → Command runs
You type 'n' → Command blocked
```

This pattern is essential for any agent that can take real-world actions. You'll see exactly how this is implemented in the code.

<!-- fold:break -->

## Key Components

The agent is built from several modular components that work together:

| Component | File | Purpose |
|-----------|------|---------|
| **Config** | `bash_agent/config.py` | Model settings, allowed commands, system prompt |
| **Bash Tool** | `bash_agent/bash.py` | Executes commands with security checks |
| **Helpers** | `bash_agent/helpers.py` | Message handling and LLM abstraction |
| **Agent** | `bash_agent.ipynb` | Brings everything together with LangGraph |

Take a moment to explore these files to understand how the pieces fit together:

<button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/bash_agent/config.py');"><i class="fa-brands fa-python"></i> bash_agent/config.py</button> — See the system prompt and allowed commands

<button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/bash_agent/bash.py');"><i class="fa-brands fa-python"></i> bash_agent/bash.py</button> — Explore the tool implementation with safety checks

<!-- fold:break -->

## Hands-On: Meet Your Agent

<img src="_static/robots/magician.png" alt="Showtime!" style="float:left;max-width:300px;margin:25px;" />

Now it's time to interact with the Bash Agent! Open the notebook and work through each section:

<button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/bash_agent.ipynb');"><i class="fa-solid fa-flask"></i> Bash Agent Notebook</button>

In this notebook, you will:

1. **Set up the environment** and load your API keys
2. **Understand the architecture** by examining the imports and components
3. **See the human-in-the-loop pattern** in action with the `ExecOnConfirm` class
4. **Create the agent** using LangGraph's `create_react_agent`
5. **Interact with the agent** to observe its behavior and decision-making

<!-- fold:break -->

## What to Watch For

As you interact with the agent, pay close attention to these aspects of its behavior:

**Command Selection**: Does the agent always choose the most efficient command? Sometimes a simpler command would work just as well, or a more powerful one would be more appropriate.

**Handling Ambiguity**: When your request isn't perfectly clear, does the agent ask for clarification or make assumptions? How reasonable are those assumptions?

**Error Recovery**: What happens when a command fails? Does the agent adapt gracefully or get stuck?

**Response Clarity**: Are the agent's explanations helpful? Does it provide context about what it did and why?

> 💡 **Pro Tip**: Take notes on any behaviors that seem suboptimal. These observations will directly inform the customization work in the next lesson!

<!-- fold:break -->

## Things to Try

Here are some requests to test different aspects of the agent's capabilities:

| Request | What It Tests |
|---------|---------------|
| "List all files here" | Basic command translation |
| "Show me the contents of config.py" | File reading with `cat` |
| "Find all Python files in this directory" | Pattern matching with `find` |
| "How big are the files in this folder?" | Using `du` for disk usage |
| "Create a folder called 'test' and show what's inside" | Multi-step task execution |
| "What's the current directory?" | Simple state awareness |

Try combining multiple requests or asking follow-up questions to see how the agent handles conversational context.

<!-- fold:break -->

## Alternative: Command Line Interface

<img src="_static/robots/typewriter.png" alt="CLI" style="float:right;max-width:300px;margin:25px;" />

Prefer working in a terminal? You can run the same agent as a standalone CLI application.

**Using LangGraph (same as the notebook):**
```bash
cd /project/code/4-agent-customization && python -m bash_agent.main_langgraph
```

**Using a from-scratch implementation:**
```bash
cd /project/code/4-agent-customization && python -m bash_agent.main_from_scratch
```

Comparing these two implementations is a great way to understand what LangGraph provides out of the box versus building the agent loop yourself!

<!-- fold:break -->

## What's Next?

<img src="_static/robots/gitfu.png" alt="Next Steps" style="float:right;max-width:300px;margin:25px;" />

After completing the hands-on notebook, you should have a solid understanding of:

- ✅ How the Bash Agent is architected using LangGraph
- ✅ The role of human-in-the-loop confirmation for safe tool execution
- ✅ The agent's strengths and areas where it could be improved

These observations are crucial! In the next lesson, [Customizing the Agent](bash_customize.md), you'll learn how to use **Synthetic Data Generation (SDG)** and **Reinforcement Learning (RL)** to systematically improve the agent's behavior.

The "rough edges" you identified aren't bugs—they're opportunities for customization. Let's turn them into training signal!
