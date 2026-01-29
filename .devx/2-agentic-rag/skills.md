# Introduction to Skills

<img src="_static/robots/study.png" alt="Skills Robot Character" style="float:right;max-width:300px;margin:25px;" />

Skills are folders of instructions, scripts, and resources that your agent loads dynamically to improve performance on specialized tasks. Think of them as teaching your agent *how* to do something in a repeatable, consistent way.

In this lesson, we'll explore what Skills are, how they differ from MCP, and how to create your own.

<!-- fold:break -->

## What Are Skills?

<img src="_static/robots/typewriter.png" alt="Writing Robot" style="float:left;max-width:250px;margin:25px;" />

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

## Anatomy of a Skill

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

## Skills vs Prompts

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

## Skills + MCP = Powerful Agents

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

## What's Next

<img src="_static/robots/hiking.png" alt="Journey Robot" style="float:right;max-width:300px;margin:25px;" />

Now that you understand Skills:

- **Explore the [Anthropic Skills repo](https://github.com/anthropics/skills)** for examples and patterns
- **Create a skill** for a task you do repeatedly
- **Combine Skills with MCP** to build powerful, knowledgeable agents

Skills and MCP together represent the future of agent development — agents that not only *can* do things, but *know how* to do them well. 🚀
