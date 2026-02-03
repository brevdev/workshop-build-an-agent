# The Bash Agent

<img src="_static/robots/operator.png" alt="Bash Agent" style="float:right;max-width:250px;margin:15px;" />

## What It Does

The **Bash Agent** translates natural language → shell commands. Say *"list all Python files"* and it generates `find . -name "*.py"`.

## Why We Build It

This is our **starting point**—a working agent we can later customize. It uses:

- **ReAct pattern** — Reason → Act → Observe in a loop until done
- **Human-in-the-loop** — User approves each command before execution (safety net)
- **LangGraph** — Orchestrates the agent's state machine

The base agent handles generic bash, but it doesn't know specialized CLIs. That's what we'll fix with training.

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

**Next:** [Synthetic Data Generation](sdg.md)
