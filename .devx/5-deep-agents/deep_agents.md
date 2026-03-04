# What Are Deep Agents?

<img src="_static/robots/datacenter.png" alt="Deep Agent Architecture" style="float:right;max-width:300px;margin:25px;" />

**Deep agents** are AI agents equipped with planning tools, file system access, shell execution, and sub-agent spawning, operating through an autonomous reasoning loop to handle complex, multi-step tasks. They use the same LLM-in-a-loop foundation as the ReAct agents you built in earlier modules, but with a **middleware pipeline** around every interaction.

**The result?** Agents that can reliably operate across hundreds of steps and extended time horizons — from minutes to hours — where shallow agents would lose focus, overflow their context, or fail to recover from mistakes.

In this section, we'll first explore the conceptual framework — the "four pillars" that make deep agents work — and then look at how the deepagents library implements them.

<!-- fold:break -->

## The Four Pillars

Deep agents enhance the ReAct loop with four architectural pillars. Each one addresses a specific limitation of shallow agents.

<!-- fold:break -->

### Pillar 1 — Explicit Planning

Shallow agents plan **implicitly** — their "plan" exists only in the chain-of-thought reasoning within the context window. It's ephemeral, easily displaced by tool outputs, and invisible to the outside world.

Deep agents plan **explicitly**. They maintain plan documents — essentially markdown to-do lists — that they review and update between steps. Each task is tracked with a status: **pending**, **in_progress**, or **completed**. Before taking action, the agent consults its plan. After each step, it updates the plan with results and adjusts strategy if needed.

<!-- fold:break -->

This seemingly simple change has profound effects:

- **Persistence** — The plan survives context window pressure because it exists as an external document
- **Visibility** — Humans can inspect the plan to understand what the agent is doing and why
- **Adaptability** — When steps fail, the agent can revise its approach rather than blindly retrying

Think of it this way: a shallow agent is like someone solving a problem in their head. A deep agent is like someone working from a written project plan — they can lose their train of thought and pick right back up.

<details>
<summary><strong>What a plan document looks like in practice</strong></summary>

A deep agent's plan might look like this:

```markdown
## Research Plan: AI Agent Frameworks Comparison

- [x] Identify top 10 frameworks to research
- [x] Research LangChain — architecture, pricing, ecosystem
- [x] Research CrewAI — architecture, pricing, ecosystem
- [ ] Research AutoGen — architecture, pricing, ecosystem (in progress)
- [ ] Research LlamaIndex — architecture, pricing, ecosystem
- [ ] ...
- [ ] Synthesize findings into comparison table
- [ ] Write executive summary
- [ ] Add citations and verify claims
```

The agent updates this plan after every step. If "Research AutoGen" fails because the search returns irrelevant results, the agent can note the failure and try a different search strategy — rather than blindly retrying the same query.

</details>

<!-- fold:break -->

### Pillar 2 — Hierarchical Delegation

Instead of a single agent trying to do everything, deep agents use an **orchestrator** that decomposes complex requests into specialized sub-tasks. Each sub-task is handled by an isolated **sub-agent** — a researcher, a coder, an analyst — with its own clean context window.

Only the synthesized results return to the orchestrator. This creates a hierarchy:

```
Orchestrator (high-level planning)
├── Sub-agent: Researcher (web search, source analysis)
├── Sub-agent: Analyst (data processing, comparison)
└── Sub-agent: Writer (synthesis, report generation)
```

<!-- fold:break -->

This pattern solves two problems at once:

- **Context isolation** — No single sub-task can overflow the orchestrator's context window. Each sub-agent works in a clean environment and returns only what matters.
- **Specialization** — Each sub-agent can have its own system prompt, tools, and instructions optimized for its specific role.

Think of it like a project manager coordinating a team. The manager doesn't write every line of code, conduct every interview, and draft every document. They break the project into work streams, assign specialists, and integrate the results.

<details>
<summary><strong>How delegation prevents context overflow</strong></summary>

Imagine a research task that requires analyzing 20 sources. With a shallow agent, all 20 source summaries pile up in one context window. With hierarchical delegation:

1. The orchestrator identifies 5 sub-topics
2. Four researcher sub-agents each handle 5 sources in their own clean context
3. Each researcher returns a 200-word summary
4. The orchestrator receives 800 words total — instead of 20 full source documents

The total information processed is the same, but no single context window is overwhelmed.

</details>

<!-- fold:break -->

### Pillar 3 — Persistent Memory

Shallow agents treat the context window as a warehouse — everything they know must fit inside it. Deep agents treat the context window as a **workspace** — a temporary scratchpad for the current task, with everything else stored externally.

Deep agents shift from "remembering everything in context" to "knowing where to find information." They use:

- **File system access** — Read, write, edit, and search files as external memory. Intermediate results, research notes, and draft outputs all live on disk.
- **Shared workspaces** — Sub-agents can read and write to common directories, enabling coordination without passing everything through the orchestrator's context.

<!-- fold:break -->

This is what enables deep agents to work on tasks that span hundreds of steps. The context window holds only what's immediately relevant — the plan, the current sub-task, and the most recent results. Everything else is a file read away.

| | Shallow Agent | Deep Agent |
|---|---|---|
| **Where state lives** | Context window | Files, databases, plan documents |
| **What happens at step 50** | Context overflows, early state lost | Agent reads relevant files on demand |
| **Cross-session memory** | None — starts fresh each time | Files and databases persist knowledge |

<!-- fold:break -->

### Pillar 4 — Agent Skills

The system prompts you've written so far — "You are a helpful assistant that..." — are typically a few hundred tokens. Deep agent **skills** are far more detailed, often thousands of tokens long, defining:

- **Decision thresholds** — When to search for more information vs. proceed with what you have
- **Tool-usage patterns** — Which tools to prefer in which situations
- **Error recovery strategies** — What to do when a tool call fails or returns unexpected results
- **Output formats** — Exactly how to structure intermediate and final results

If you worked through Module 4's **Superpowers** skills framework, you've already seen a taste of this. Deep agent skills take it further — they're detailed operating procedures that guide the agent's behavior across complex, multi-step workflows.

<details>
<summary><strong>Example: A deep research agent's skill excerpt</strong></summary>

A deep research agent might have skill instructions like:

> "When researching a topic, first create a plan document with 3-7 sub-topics. For each sub-topic, spawn a researcher sub-agent with web search tools. If a sub-agent returns fewer than 3 relevant sources, expand the search query and retry once. If the retry also fails, mark the sub-topic as 'insufficient data' in the plan and proceed. After all sub-agents complete, synthesize results into a structured report with citations. If any section has fewer than 2 citations, flag it for human review."

This level of detail is what separates a deep agent from a shallow one using the same model. The model's capabilities are identical — the difference is in the instructions.

</details>

<!-- fold:break -->

## Shallow vs. Deep Agents

Here's a comprehensive comparison of the two architectures:

| Dimension | Shallow Agent | Deep Agent |
|-----------|--------------|------------|
| **Planning** | Implicit (chain-of-thought) | Explicit (plan documents) |
| **Delegation** | Single agent does everything | Orchestrator + specialized sub-agents |
| **Memory** | Context window only | File system + external stores |
| **System Prompt** | Brief instructions | Detailed skills with protocols |
| **Task Horizon** | 5-15 steps | 50-500+ steps |
| **Error Recovery** | Retry or fail | Adapt strategy, try alternatives |
| **Best For** | Focused, short tasks | Complex, multi-step workflows |

The key insight: deep agents don't replace shallow agents. They **extend** them. A deep agent's sub-agents are themselves shallow agents — focused, single-loop executors. The deep agent architecture adds the coordination layer that lets them work together on larger problems.

<details>
<summary><strong>Where do the agents you built fit?</strong></summary>

Looking back at the workshop:

- **Module 1 Report Agent** — A shallow agent. Single loop, 5-10 tool calls, everything in context. Perfect for short research reports.
- **Module 2 RAG Agent** — A shallow agent with enhanced retrieval. Still single loop, but with richer context from external documents.
- **Module 4 Customized Agent** — A shallow agent with trained expertise. Better at its domain, but still architecturally limited to single-loop execution.

A deep agent could **orchestrate** all of these as sub-agents: use the RAG agent for document retrieval, the report agent for writing, and the customized agent for domain-specific analysis — all coordinated by a planner.

</details>

<!-- fold:break -->

## Deep Agents in the Real World

<img src="_static/robots/supervisor.png" alt="Real World Applications" style="float:right;max-width:250px;margin:25px;" />

Deep agent patterns have moved rapidly from research to production. Let's look at where they're making the biggest impact. Click on each use case to learn more. 

<details>
<summary><strong>1. Deep Research</strong></summary>

Deep research is the flagship application of deep agents — and the category where all major AI providers have converged on remarkably similar architectures:

| Provider | Product | Distinguishing Feature |
|----------|---------|----------------------|
| **OpenAI** | Deep Research | Uses o3 for extended autonomous browsing and synthesis |
| **Google** | Gemini Deep Research | Produces 100+ page reports via multi-agent workflows |
| **Perplexity** | Deep Research | Speed-optimized, prioritizing faster turnaround |
| **Anthropic** | Claude Research | Extended thinking for multi-step research synthesis |

Despite different implementations, the common architecture follows a consistent pattern:

1. **Scoping** — Clarify the research question, identify sub-topics and constraints
2. **Supervisor** — An orchestrator plans the research strategy and assigns sub-tasks
3. **Sub-agents** — Parallel researchers each tackle a sub-topic, browsing dozens of sources
4. **Compression** — Results are synthesized, deduplicated, and cross-referenced
5. **Report** — A final structured document is generated with citations

</details>

<details>
<summary><strong>2. Coding Assistants</strong></summary>

Software development is the most battle-tested use case for deep agents. Tools like **Claude Code**, **Cursor**, and **GitHub Copilot** all leverage deep agent patterns:

- **Planning tools** to decompose engineering tasks into subtasks
- **File system access** to navigate and modify large codebases
- **Sub-agents** for parallel work (e.g., writing code while running tests)
- **Persistent memory** to track progress across multi-file refactors

These agents don't just autocomplete code — they reason about architecture, track progress, adapt when builds fail, and coordinate changes across dozens of files.

</details>

<!-- fold:break -->

## Benefits and Tradeoffs

Like any architectural decision, deep agents come with both benefits and costs. Click on each of the following to learn more: 

<details>
<summary><strong>1. Benefits of Deep Agent Architecture</strong></summary>

| Benefit | Description |
|---------|-------------|
| **Complex task handling** | Multi-step workflows spanning long time horizons that would overwhelm shallow agents |
| **Scalable context** | File system access and sub-agent delegation prevent context overflow |
| **Resilient planning** | Adapts strategy when steps fail instead of entering infinite loops |
| **Safe execution** | Sandboxing enables autonomous code execution in production |

</details>

<details>
<summary><strong>2. Tradeoffs of Deep Agent Architecture</strong></summary>

| Tradeoff | Detail |
|----------|--------|
| **Latency** | Minutes to hours vs. seconds for shallow agents |
| **Cost** | ~15x more tokens than standard chat interactions |
| **Complexity** | Harder to test, predict, and debug across multiple agents |
| **Coordination** | Multi-agent writing can produce disjointed output without careful orchestration |

</details>

<details>
<summary><strong>3. So Why are Deep Agents Practical Now?</strong></summary>

Recent advances in LLM capabilities have made these patterns practical for production use:

- **Longer context windows** make it feasible for orchestrators to manage complex plans
- **Better instruction following** means agents reliably execute detailed skill protocols
- **Improved tool use** enables reliable file system access, code execution, and API calls
- **Faster inference** makes multi-agent architectures practical without prohibitive latency

Deep agents are not universally better than shallow agents — they're better for a specific class of problems. Using a deep agent for a simple question-answering task is like using a distributed system for a single-user application: architecturally sound but massively over-engineered.

</details>

<!-- fold:break -->

### When to Use Deep Agents

Not every task needs a deep agent. Here's a decision framework:

| Use a Deep Agent When... | Use a Shallow Agent When... |
|--------------------------|----------------------------|
| Tasks span dozens to hundreds of steps | Tasks complete in 5-15 steps |
| Multiple specialized skills are needed | A single tool-calling loop suffices |
| The problem would overflow a context window | Everything fits in one conversation |
| Autonomous operation is acceptable | Real-time response is required |
| The task benefits from planning and delegation | The path is straightforward |

> **A practical rule of thumb** - Ask yourself: "Could a single person complete this in one sitting without taking notes?" If yes, a shallow agent is probably fine. If the answer is "no — you'd need to break it into subtasks, keep a to-do list, and coordinate with specialists," that's a deep agent problem.

<!-- fold:break -->

Here are some concrete examples:

| Task | Agent Type | Why |
|------|-----------|-----|
| "Summarize these articles" | Shallow | Single step, fits in context |
| "Answer this question using our docs" | Shallow | RAG + generation, 3-5 steps |
| "Research 10 competitors and write a market report" | Deep | Multi-source, requires planning and synthesis |
| "Refactor this codebase to use a new API" | Deep | Multi-file, needs progress tracking |
| "Generate a quarterly compliance report from 50 documents" | Deep | Long-running, delegation needed |

<!-- fold:break -->

## Putting It All Together

To see how the four pillars work in concert, consider a deep research task: "Analyze the current state of AI regulation across the G7 countries."

1. **Explicit Planning** — The agent creates a plan: research each country's regulations, then synthesize a comparison
2. **Hierarchical Delegation** — The orchestrator spawns 7 researcher sub-agents, one per country
3. **Persistent Memory** — Each researcher writes findings to files; the orchestrator reads them for synthesis
4. **Agent Skills** — Detailed instructions tell each researcher how many sources to gather, what format to use, and how to handle conflicting information

No single pillar is sufficient on its own — together, they enable reliable autonomous operation at a scale shallow agents can't reach.

Now let's see how the **deepagents library** implements these pillars.

<!-- fold:break -->

### The `create_deep_agent()` Function

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

### The Middleware Pipeline

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

### Built-In Capabilities

Every deep agent comes with these tools out of the box — provided by the middleware stack.

#### Planning — `write_todos`

The agent can create and manage a task list. When given a complex request, it breaks it into steps, tracks progress, and works through them systematically. This is **Pillar 1 (Explicit Planning)** in action.

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

#### Filesystem — `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`

<img src="_static/robots/operator.png" alt="File Operations" style="float:right;max-width:250px;margin:15px;" />

Deep agents have full filesystem awareness — the tooling layer for **Pillar 3 (Persistent Memory)**. They can:

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

#### Shell Execution — `execute`

The `execute` tool runs shell commands. Combined with filesystem tools, this lets the agent:

- Run Python scripts it wrote
- Install packages
- Run tests
- Check system status
- Compile and build projects

Shell access is what makes deep agents truly autonomous — but it's also what makes **sandboxing critical** (more on that in the security section).

<!-- fold:break -->

#### Sub-Agents — `task`

Perhaps the most powerful capability: deep agents can **spawn sub-agents** to handle sub-tasks in isolated context windows. This is **Pillar 2 (Hierarchical Delegation)** in action.

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

#### Context Management — Auto-Summarization

Long conversations accumulate tokens quickly. Deep agents handle this with **automatic summarization** — when the conversation gets too long, the middleware transparently compresses earlier messages so the agent keeps working without hitting token limits. This supports **Pillar 3 (Persistent Memory)** by ensuring the agent doesn't lose track of its work.

<!-- fold:break -->

### Extending Deep Agents

Beyond the built-in capabilities, deep agents can be extended with two mechanisms:

#### MCP Tools — Model Context Protocol

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

#### Skills — Markdown Methodology Injection

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

## Architecture Summary

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

> Ready to build one? Head to [Set Up the Agent Builder](setup_agent_builder) to get your environment ready!
