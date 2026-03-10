# LangSmith Studio: Improvement Opportunities for Deep Agents

## Summary

The Agent Builder has the right architecture. There's a **Toolbox** for adding tools, a **Sub-Agents** panel for multi-agent orchestration, a **Skills** section for capability injection, and **Triggers** for automation. The visual graph layout connecting these to the agent is well-designed.

The problem is what's *inside* these sections. For deep agents — coding agents, research agents, data engineering agents — the available options are too limited. The Toolbox shows Tavily Web Search and MCP integrations. The Skills section is empty. There's no sandboxing toggle, no planning tool, no file I/O, no shell execution. These are core capabilities that deep agents need, and they should be first-class items in the UI — not things developers have to wire up in code.

The architecture is there. It just needs to be filled out.

---

## What the Agent Builder Gets Right

Credit where it's due — the Agent Builder's layout already captures the key concepts:

- **Toolbox** — A dedicated panel for adding tools to the agent. Tavily Web Search is already available, and MCP integrations work. This is the right pattern.
- **Sub-Agents** — First-class support for sub-agent configuration (Deep Researcher, Shallow Researcher in the screenshot). Named sub-agents with visibility toggles. This is great.
- **Skills** — The section exists in the UI. Even though it shows "No skills configured" today, the concept is present. The agent graph connects to a Skills node.
- **Triggers** — Automation hooks. Useful for production workflows.
- **Instructions** — System prompt editing with a visual "View" overlay. Clean UX.
- **Visual graph** — The agent sits at the center with dashed connections to Triggers, Toolbox, Sub-Agents, and Skills. This communicates the agent's composition clearly.

The foundation is solid. The gaps are about what's available to put *into* these sections.

---

## Gap 1: The Toolbox Needs Deep Agent Capabilities

**Current state:** The Toolbox includes Tavily Web Search and MCP tool connections. These are external integration tools — great for connecting to third-party APIs and services.

**What's missing:** For deep agents (coding agents, research agents, system agents), the most important tools are *native* capabilities that don't require an external MCP server:

| Capability | What It Does | Why It Should Be in the Toolbox |
|---|---|---|
| **File I/O** | `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep` | Coding agents need to read and modify files. This is the most fundamental capability for any agent that works with code or documents. |
| **Shell Execution** | Run shell commands, Python scripts, system tools | Agents that build software need to run tests, install packages, execute scripts. Without this, a coding agent can only *write* code but never *run* it. |
| **Planning** | `write_todos`, `read_todos` — structured task decomposition | Complex multi-step tasks (build a REST API, debug a codebase) require the agent to plan. A planning tool gives the agent structured task management instead of ad-hoc reasoning. |
| **Code Interpreter** | Execute Python/JS in a managed runtime | Data analysis, visualization, quick computations. OpenAI has this as a built-in — it should be a standalone Toolbox option for any model. |

**The ask:** These should be toggleable items in the Toolbox alongside Tavily Web Search — not capabilities that require writing Python code and configuring a custom backend. A developer should be able to click "Add" next to File I/O the same way they add Web Search.

---

## Gap 2: The Skills Section Needs a Library

**Current state:** The Skills section exists in the Agent Builder UI but shows "No skills configured." The concept is there — skills connect to the agent via the visual graph — but there's nothing to add.

**What's missing:** A **skill library** — pre-built and user-created knowledge packs that inject domain-specific instructions, methodologies, and API references into the agent. Examples of skills that should be available:

| Skill | What It Injects | Use Case |
|---|---|---|
| **TDD / Superpowers** | Test-driven development methodology — plan before coding, write tests first, debug systematically | Software engineering agents |
| **cuDF / RAPIDS** | GPU-accelerated DataFrame API reference, performance tips, migration patterns from pandas | Data engineering on NVIDIA hardware |
| **Code Review** | Systematic code quality analysis checklist — correctness, security, performance, style | Code review automation |
| **Research Methodology** | How to evaluate sources, cross-reference claims, synthesize findings | Research agents |
| **Compliance / Legal** | Regulatory frameworks, citation requirements, audit patterns | Legal and compliance agents |

**The ask:** Two things:
1. **Built-in skill library** — Ship common skills (coding patterns, research methodology, data analysis) that users can toggle on/off from the Skills panel.
2. **Custom skill creation** — Let users create skills from markdown files or structured templates. A `skills/` directory that the Agent Builder auto-discovers would work. Users write a markdown file describing the methodology, drop it in the directory, and it shows up in the Skills panel.

Skills are the simplest way to specialize an agent without changing its tools or architecture. The UI section is already there — it just needs content.

---

## Gap 3: No Sandboxing

**Current state:** The Agent Builder has no visible sandbox configuration. There's no toggle, no settings panel, no indication of execution environment isolation.

**What's missing:** For any agent with file I/O or shell execution, sandboxing is a critical safety layer. The agent's tool calls should be able to run inside an isolated Docker container so the agent cannot access the host filesystem, environment variables, or credentials.

**What it should look like:**

- **Session-level toggle** — A "Sandbox Mode" switch in the agent's settings or alongside the Toolbox. When enabled, all file and shell operations route through a Docker container.
- **Per-tool granularity** — Advanced users should be able to sandbox specific tools. For example: sandbox shell execution but keep file reads local. The UI could show a lock icon next to each sandboxed tool in the Toolbox.
- **Visual indicator** — When sandboxing is active, the agent graph or header should clearly show it (e.g., a shield icon, a "Sandboxed" badge).
- **Resource limits** — Configurable memory, CPU, and timeout limits for the sandbox container.

**Why this matters:** Without sandboxing, giving an agent shell execution access is effectively giving it root access to the developer's machine. Enterprise users, demo environments, and multi-user deployments all require isolation. The Agent Builder already lets you add powerful tools — it should also let you constrain them.

---

## Gap 4: Planning Should Be Visible in the UI

**Current state:** Planning is not a first-class capability in the Agent Builder. There's no planning tool in the Toolbox, and the graph doesn't have a "Planning" node.

**What's missing:** When a planning tool is enabled and the agent creates a task list, that plan should be visible in the Studio UI. This is especially valuable during debugging — if the agent plans poorly, the developer should see it immediately, not discover it buried in the trace logs.

**What it should look like:**

- **Planning tool in the Toolbox** — Toggleable like any other tool. When enabled, the agent gets `write_todos`/`read_todos` (or equivalent structured planning tools).
- **Plan sidebar** — A panel in Studio that renders the agent's current task list: planned tasks, in-progress work, completed items. Updates in real-time as the agent works.
- **Plan inspection in time-travel** — When using time-travel debugging, the plan state at each step should be visible. This lets developers see when and why the agent's plan changed.

---

## Gap 5: Sub-Agent Permissions and Capability Scoping

**Current state:** The Sub-Agents panel is great — named sub-agents (Deep Researcher, Shallow Researcher) with visibility toggles. But from the UI, it's not clear how sub-agent capabilities are scoped.

**What could be improved:**

- **Per-sub-agent capability configuration** — Each sub-agent should have its own Toolbox and Skills configuration. The Deep Researcher might need web search + file I/O, while the Shallow Researcher only needs web search. This should be configurable from the UI.
- **Delegation rules** — When does the parent agent delegate to which sub-agent? This could be a simple set of routing rules visible in the graph (e.g., "complex questions → Deep Researcher, simple questions → Shallow Researcher").
- **Sub-agent sandbox scoping** — Sub-agents should inherit or override the parent's sandbox settings. A parent agent might run unsandboxed, but its sub-agents could be sandboxed for safety.

---

## Summary Table

| Area | What Exists | What's Missing |
|---|---|---|
| **Toolbox** | Web Search, MCP integrations | File I/O, Shell Execution, Planning, Code Interpreter as toggleable native tools |
| **Skills** | UI section exists, "No skills configured" | A skill library (built-in + custom), markdown-based skill creation |
| **Sandboxing** | Not present | Session-level toggle, per-tool granularity, Docker isolation, resource limits |
| **Planning** | Not a first-class tool or UI element | Planning tool in Toolbox, live plan sidebar, plan state in time-travel |
| **Sub-Agents** | Named sub-agents with visibility toggles | Per-sub-agent capability scoping, delegation rules, sandbox inheritance |

---

## The Big Picture

The Agent Builder already has the right layout: a central agent connected to Toolbox, Skills, Sub-Agents, and Triggers. The visual language is clear and the no-code approach is the right direction.

The opportunity is to fill these sections with **deep agent capabilities**. Today the Toolbox is mostly external integrations (Web Search, MCP). It should also include the native building blocks of a powerful agent — file tools, shell access, planning, code execution. The Skills section should ship with a library of useful knowledge packs and let users create their own. Sandboxing should be a first-class setting, not an afterthought.

The architecture is already there. It's about populating it with the capabilities that make agents actually useful for real work.
