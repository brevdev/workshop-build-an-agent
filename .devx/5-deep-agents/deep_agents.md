# What Are Deep Agents?

<img src="_static/robots/datacenter.png" alt="Deep Agent Architecture" style="float:right;max-width:300px;margin:25px;" />

Now that we understand *why* deep agents exist, let's look at *how* they work. A deep agent isn't just an agent with more tools — it's an agent with a **middleware pipeline** that adds planning, file management, sub-agent orchestration, and context management around every interaction.

In this section, we'll break down each capability and understand the architecture that ties them together.

<!-- fold:break -->

## The `create_deep_agent()` Function

At its core, a deep agent is created with a single function:

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model=model,              # The LLM (e.g., NVIDIA Nemotron)
    tools=[...],              # Extra tools (e.g., web search)
    system_prompt="...",      # Custom instructions
    backend=backend,          # File/shell execution backend
    checkpointer=checkpointer,  # State persistence
    subagents=[...],          # Specialized sub-agents
    skills=["/skills/"],      # Skill file paths
    interrupt_on={...},       # HITL approval config
)
```

This returns a compiled **LangGraph** graph — the same framework we used in earlier modules, but with a much richer node structure.

<!-- fold:break -->

## Built-In Capabilities

Every deep agent comes with these tools out of the box. You don't need to define them — they're provided by the middleware stack.

### Planning — `write_todos`

The agent can create and manage a task list. When given a complex request, it breaks it into steps, tracks progress, and works through them systematically.

```
User: "Research CUDA 13, write a benchmark script, and run it"

Agent thinks: Let me break this into tasks...
→ write_todos([
    "Research CUDA 13 features",
    "Write benchmark script",
    "Execute and analyze results"
  ])
```

This gives the agent a structured approach to multi-step problems instead of improvising each action.

<!-- fold:break -->

### Filesystem — `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`

<img src="_static/robots/operator.png" alt="File Operations" style="float:right;max-width:250px;margin:15px;" />

Deep agents have full filesystem awareness. They can:

| Tool | What It Does |
|---|---|
| `ls` | List directory contents |
| `glob` | Find files by pattern (e.g., `**/*.py`) |
| `grep` | Search file contents by regex |
| `read_file` | Read file contents with line numbers |
| `write_file` | Create or overwrite files |
| `edit_file` | Make targeted edits (find and replace) |

This is what separates deep agents from chatbots. They can navigate a codebase, understand project structure, make surgical edits, and verify their changes — just like a developer.

<!-- fold:break -->

### Shell Execution — `execute`

The `execute` tool runs shell commands. Combined with filesystem tools, this lets the agent:

- Run Python scripts it wrote
- Install packages
- Run tests
- Check system status
- Compile and build projects

Shell access is what makes deep agents truly autonomous — but it's also what makes **sandboxing critical** (more on that in the security section).

<!-- fold:break -->

### Sub-Agents — `task`

Perhaps the most powerful capability: deep agents can **spawn sub-agents** to handle sub-tasks in isolated context windows.

```
User: "Research GPU optimization and write a benchmark script"

Main Agent:
  → task("Researcher": "Find GPU optimization techniques")
  → task("Coder": "Write a CUDA benchmark script")
  → Combines both results into final response
```

Each sub-agent gets its own context, tools, and prompt. This enables:

- **Parallel work** — Multiple sub-tasks running simultaneously
- **Specialization** — Each sub-agent has a focused role
- **Context isolation** — Sub-agent conversations don't pollute the main context

<!-- fold:break -->

### Context Management — Auto-Summarization

Long conversations accumulate tokens quickly. Deep agents handle this with **automatic summarization** — when the conversation gets too long, the middleware summarizes earlier messages to free up context window space.

This happens transparently. The agent keeps working without hitting token limits or losing track of what it was doing.

<!-- fold:break -->

## Extending Deep Agents

Beyond the built-in capabilities, deep agents can be extended with two mechanisms:

### MCP Tools — Model Context Protocol

MCP lets you connect external tool servers to your agent. Any server exposing an SSE or Streamable HTTP endpoint can provide tools:

```python
# Connect to a remote MCP server
client = MultiServerMCPClient({
    "math_server": {"transport": "sse", "url": "http://localhost:8100/sse"}
})
tools = await client.get_tools()
# → [add, multiply, reverse_string, word_count]
```

The agent calls these tools just like built-in ones. MCP is the standard protocol for tool interoperability — your agent can use tools from any MCP-compatible server.

<!-- fold:break -->

### Skills — Markdown Methodology Injection

Skills are `.md` files that get injected into the agent's system prompt. They teach the agent *how* to approach specific types of problems:

```markdown
# Superpowers — Agentic Software Development

When writing code, follow this methodology:
1. Plan before coding — create a todo list
2. Write tests first (TDD)
3. Implement the minimum to pass tests
4. Debug systematically — read errors carefully
```

Skills don't add new tools — they add **expertise**. You can create skills for any domain: code review, data analysis, GPU optimization, legal research, etc.

<!-- fold:break -->

## The Middleware Pipeline

Under the hood, `create_deep_agent()` builds a LangGraph graph with a **middleware stack** that processes every interaction:

```
User Message
  → SummarizationMiddleware    (compress long conversations)
  → PatchToolCallsMiddleware   (fix dangling tool calls)
  → Model                      (LLM generates response)
  → TodoListMiddleware         (manage planning state)
  → FilesystemMiddleware       (handle file operations)
  → SubAgentMiddleware         (delegate to sub-agents)
  → HumanInTheLoopMiddleware   (pause for approval if configured)
  → Tool Execution
  → Back to Model...
```

Each middleware adds a capability without you writing any orchestration code. This is what makes deep agents "batteries-included" — the complexity is handled by the framework.

<!-- fold:break -->

## Deep Agent vs Shallow Agent — Architecture

Here's the key architectural difference:

**Shallow Agent (ReAct):**
```
[Model] ←→ [Tool Node]
```

**Deep Agent:**
```
[Summarization] → [PatchToolCalls] → [Model] → [TodoList] → [Filesystem]
                                                     ↓
                                              [SubAgentMiddleware]
                                                     ↓
                                              [HITL Gate] → [Tools]
```

The deep agent has a **pipeline** of middleware that wraps every model call and tool execution, adding intelligence at each step.

> Ready to build one? Head to [Build a Deep Agent](build_deep_agents) to get hands-on!
