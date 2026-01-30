# Agent Skills

<img src="_static/robots/study.png" alt="Skills Robot Character" style="float:left;max-width:300px;margin:25px;" />

Skills are folders of instructions, scripts, and resources that your agent loads dynamically to improve performance on specialized tasks. Think of them as teaching your agent *how* to do something in a repeatable, consistent way.

In this lesson, we'll explore what Skills are, how they differ from MCP, and how to create your own.

<!-- fold:break -->

## What Are Skills?

<img src="_static/robots/typewriter.png" alt="Writing Robot" style="float:right;max-width:250px;margin:25px;" />

Skills teach your agent how to complete specific tasks:

- Creating documents with your company's brand guidelines
- Analyzing data using your organization's workflows
- Automating personal tasks with specific patterns
- Following coding standards for your team

Unlike MCP (which provides *tools* and *data*), Skills provide *instructions* and *knowledge*. They're complementary:

| MCP | Skills |
|-----|--------|
| Provides tools to **do** things | Provides instructions on **how** to do things |
| Connects to external services | Loads context and guidelines |
| Runtime capabilities | Domain expertise |

<!-- fold:break -->

### Anatomy of a Skill

Every skill is simply a folder containing a `SKILL.md` file. The file has two parts:

**1. YAML Frontmatter** — Metadata about the skill:

```yaml
---
name: my-skill-name
description: A clear description of what this skill does
---
```

**2. Markdown Instructions** — What the agent should follow:

```markdown
# My Skill Name

Instructions that the agent will follow when this skill is active.

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
```

That's it! Skills are intentionally simple.

<!-- fold:break -->

### Skills vs Prompts

<img src="_static/robots/blueprint.png" alt="Blueprint Robot" style="float:right;max-width:300px;margin:25px;" />

You might wonder: "Why not just put instructions in the system prompt?"

Skills offer advantages:

- **Modularity** — Load only what's needed for each task
- **Reusability** — Share skills across projects and teams
- **Organization** — Keep complex instructions out of your main prompt
- **Versioning** — Track changes to instructions over time
- **Discovery** — The agent can select relevant skills automatically

Think of skills as a library of expertise that your agent can draw from.

<!-- fold:break -->

## Real-World Examples

The [Anthropic Skills Repository](https://github.com/anthropics/skills) contains many examples:

**Creative & Design:**
- Art generation guidelines
- Music composition patterns
- Design system standards

**Development & Technical:**
- Testing web applications
- MCP server generation
- Code review workflows

**Enterprise & Communication:**
- Brand voice guidelines
- Document formatting standards
- Communication templates

**Document Skills:**
- PDF extraction and creation
- PowerPoint generation
- Excel data manipulation

<!-- fold:break -->

## Creating Your First Skill

<img src="_static/robots/plumber.png" alt="Building Robot" style="float:left;max-width:250px;margin:25px;" />

Let's create a simple skill. Create a folder called `my-skill/` with a `SKILL.md` file:

```yaml
---
name: code-reviewer
description: Reviews code following team standards and best practices
---
```

```markdown
# Code Reviewer

You are a code reviewer following our team's standards.

## Review Checklist
- Check for proper error handling
- Verify naming conventions match our style guide
- Look for potential security issues
- Ensure tests are included

## Feedback Style
- Be constructive and specific
- Suggest improvements, don't just criticize
- Include code examples when helpful
```

<!-- fold:break -->

## Using Skills

Skills can be loaded in multiple ways:

**Via Agent Tools:**
Your agent can use tools like `list_available_skills()` and `get_skill()` to discover and load skills dynamically.

**Via System Prompt:**
Include the skill content directly in your agent's system prompt.

**With MCP:**
Skills and MCP work together — MCP provides the tools, Skills provide the expertise to use them effectively.

<!-- fold:break -->

### Skills + MCP = Powerful Agents

<img src="_static/robots/strong.png" alt="Power Robot" style="float:right;max-width:300px;margin:25px;" />

The combination of Skills and MCP creates highly capable agents:

| Component | What It Provides |
|-----------|------------------|
| **LLM** | Reasoning and language |
| **MCP** | Tools, resources, data access |
| **Skills** | Domain knowledge, procedures, guidelines |

For example, an IT Help Desk agent might use:
- **MCP Server** → Query the knowledge base, create tickets
- **Skill** → Follow company support procedures, use proper tone

This separation of concerns makes agents more maintainable and adaptable.

<!-- fold:break -->

## Skills: A Hands-On Implementation with MCP

<img src="_static/robots/magician.png" alt="Skills Magic Robot" style="float:right;max-width:300px;margin:25px;" />

Your RAG agent currently has **tools** (knowledge base + web search). Let's add **skills** — specialized expertise your agent can load on demand.

<!-- fold:break -->

### The Goal

Add two new tools:
- `list_available_skills` — See what skills exist
- `get_skill` — Load a skill for expertise

**Available Skills:**
- `code_review` — Systematic code review with checklist
- `technical_writing` — Guidelines for clear documentation

<!-- fold:break -->

### Your Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/2-agentic-rag/rag_agent.py');"><i class="fa-brands fa-python"></i> code/2-agentic-rag/rag_agent.py</button> and fill in these blanks in the **Skills section**:

#### Exercise: Load a Skill

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'def get_skill');"><i class="fas fa-code"></i> get_skill return</button> — Return the loaded skill content.

<details>
<summary>🆘 Need some help?</summary>

```python
return load_skill(skill_name)
```

</details>

<!-- fold:break -->

#### Exercise: List Available Skills

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'def list_available_skills');"><i class="fas fa-code"></i> list_available_skills return</button> — Return the list of skills.

<details>
<summary>🆘 Need some help?</summary>

```python
return list_skills()
```

</details>

<!-- fold:break -->

#### Exercise: Create the Agent with ALL Tools

<button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'AGENT = ');"><i class="fas fa-code"></i> AGENT</button> — Wire up all four tools!

<details>
<summary>🆘 Need some help?</summary>

```python
AGENT = create_react_agent(
    model=llm,
    tools=[RETRIEVER_TOOL, web_search, get_skill, list_available_skills],
    prompt=SYSTEM_PROMPT,
)
```

</details>

<!-- fold:break -->

## Test Your Complete Agent

```bash
cd code/2-agentic-rag
langgraph dev
```

Restart your agent and try these prompts in the <button onclick="launch('Simple Agents Client');"><i class="fa-solid fa-rocket"></i> Simple Agents Client</button>:

| Prompt | Expected Behavior |
|--------|-------------------|
| "How do I reset my password?" | Uses knowledge base [KB] |
| "What are the latest AI trends?" | Uses web search [Web] |
| "What skills do you have?" | Lists `code_review`, `technical_writing` |
| "Review this code: `def add(a,b): return a+b`" | Loads code_review skill, gives structured feedback |

<!-- fold:break -->

## Next Steps

<img src="_static/robots/strong.png" alt="Strong Robot" style="float:right;max-width:250px;margin:25px;" />

Congratulations! Your agent now has:

- ✅ **RAG** — Knowledge base retrieval (Exercises 1-3)
- ✅ **MCP** — Web search (Exercises 4-5)
- ✅ **Skills** — Dynamic expertise (Exercises 6-9)

Skills and MCP together represent the future of agent development — agents that not only *can* do things, but *know how* to do them well. Now that you understand Skills, explore the [Anthropic Skills repo](https://github.com/anthropics/skills)** for other examples and patterns. 

## Operations Ready

Our agent is now ready for day 2 operations. To control costs, we would like to run our own models before going to production. Let's explore how we can do that in [Migrate to Local NIM](migrate.md).
