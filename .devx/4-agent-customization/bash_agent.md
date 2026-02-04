# The Bash Agent

<img src="_static/robots/operator.png" alt="Bash Agent" style="float:right;max-width:250px;margin:15px;" />

## What It Does

The **Bash Agent** translates natural language → shell commands. Say *"list all Python files"* and it generates `find . -name "*.py"`.

This is the same agentic pattern from Module 1, applied to a different domain. The agent reasons about your request, selects appropriate commands, and executes them—with your approval.

## Why a Bash Agent?

We chose this agent for customization training because:

1. **Observable outputs** — Shell commands are concrete and verifiable. Unlike creative writing, we can objectively check if `langgraph new --template react-agent-python` is correct.

2. **Clear improvement target** — The base model knows generic bash but not LangGraph CLI. This gap is measurable and fixable with training.

3. **Real-world applicability** — Many developers want agents that understand their specific CLIs, APIs, and toolchains.

## Architecture

The agent uses patterns you've seen before:

- **ReAct pattern** — Reason → Act → Observe in a loop until done
- **Human-in-the-loop** — User approves each command before execution (safety net)
- **LangGraph** — Orchestrates the agent's state machine

## The Gap We'll Fix

Try asking the base agent: *"Create a new LangGraph project with the react-agent template"*

It might:
- Hallucinate a command that doesn't exist
- Use wrong parameter names
- Miss required arguments

After training, the same request reliably produces:
```bash
langgraph new ./myapp --template react-agent-python
```

This transformation—from unreliable to expert—is what customization achieves.

## Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/bash_agent.ipynb');"><i class="fa-solid fa-flask"></i> bash_agent.ipynb</button>

<!-- fold:break -->

### Exercise 1: HITL Wrapper

<button onclick="goToLineAndSelect('code/4-agent-customization/bash_agent.ipynb', 'class ExecOnConfirm');"><i class="fas fa-code"></i> ExecOnConfirm</button> — Require user approval before running commands.

<details>
<summary>🆘 Hint</summary>

```python
if self._confirm_execution(cmd):
    return self.bash.exec_bash_command(cmd)
return {"error": "User declined."}
```
</details>

<!-- fold:break -->

### Exercise 2: Create Agent

<button onclick="goToLineAndSelect('code/4-agent-customization/bash_agent.ipynb', 'agent = create_react_agent');"><i class="fas fa-code"></i> create_react_agent</button> — Wire up LLM, tool, and prompt.

<details>
<summary>🆘 Hint</summary>

```python
agent = create_react_agent(
    model=llm,
    tools=[ExecOnConfirm(bash).exec_bash_command],
    prompt=config.system_prompt,
)
```
</details>

<!-- fold:break -->

### Exercise 3: Run Loop

<button onclick="goToLineAndSelect('code/4-agent-customization/bash_agent.ipynb', 'result = agent.invoke');"><i class="fas fa-code"></i> agent.invoke</button> — Send user message to agent.

<details>
<summary>🆘 Hint</summary>

```python
result = agent.invoke({"messages": [{"role": "user", "content": user}]})
```
</details>

## Test It

```bash
cd code/4-agent-customization && python3 -m bash_agent.main_langgraph
```

Try: `"List all files"` → `ls`

## Superpowers Skills

The Bash Agent includes skills from the [Superpowers](https://github.com/obra/superpowers) framework—structured workflows that guide the agent through complex tasks.

### Available Skills

| Skill | Purpose |
|-------|---------|
| `systematic-debugging` | 4-phase root cause analysis before fixing bugs |
| `test-driven-development` | RED-GREEN-REFACTOR workflow |
| `brainstorming` | Socratic design refinement |
| `writing-plans` | Create detailed implementation plans |
| `executing-plans` | Execute plans with checkpoints |

### How to Use

The agent can load skills on demand:

- *"List available skills"* — See all skills
- *"Load the systematic-debugging skill"* — Get the full workflow
- *"I have a bug, what skill should I use?"* — Get recommendations

Skills transform the agent from a simple command executor into a methodical problem-solver that follows proven workflows.

**Next:** [Synthetic Data Generation](sdg.md)
