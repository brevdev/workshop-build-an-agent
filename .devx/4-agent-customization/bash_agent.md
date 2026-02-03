# The Bash Agent

<img src="_static/robots/operator.png" alt="Bash Agent" style="float:right;max-width:250px;margin:15px;" />

The **Bash Agent** translates natural language into shell commands. It uses the **ReAct** pattern (Reason → Act → Observe → Repeat) and includes **human-in-the-loop** confirmation for safety.

## Key Components

| File | Purpose |
|------|---------|
| `bash_agent/config.py` | Allowed commands, system prompt |
| `bash_agent/bash.py` | Command execution with safety checks |
| `bash_agent.ipynb` | LangGraph agent implementation |

<!-- fold:break -->

## Your Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/bash_agent.ipynb');"><i class="fa-solid fa-flask"></i> bash_agent.ipynb</button> and complete these exercises:

### Exercise 1: Create the Human-in-the-Loop Wrapper

<button onclick="goToLineAndSelect('code/4-agent-customization/bash_agent.ipynb', 'class ExecOnConfirm');"><i class="fas fa-code"></i> ExecOnConfirm class</button> — The agent needs user confirmation before running commands. Fill in the return statement.

<details>
<summary>🆘 Need some help?</summary>

```python
def exec_bash_command(self, cmd: str) -> Dict[str, str]:
    if self._confirm_execution(cmd):
        return self.bash.exec_bash_command(cmd)
    return {"error": "The user declined the execution of this command."}
```

</details>

<!-- fold:break -->

### Exercise 2: Create the ReAct Agent

<button onclick="goToLineAndSelect('code/4-agent-customization/bash_agent.ipynb', 'agent = create_react_agent');"><i class="fas fa-code"></i> create_react_agent</button> — Wire up the LLM, tool, and system prompt.

<details>
<summary>🆘 Need some help?</summary>

```python
agent = create_react_agent(
    model=llm,
    tools=[ExecOnConfirm(bash).exec_bash_command],
    prompt=config.system_prompt,
    checkpointer=InMemorySaver(),
)
```

</details>

<!-- fold:break -->

### Exercise 3: Run the Agent Loop

<button onclick="goToLineAndSelect('code/4-agent-customization/bash_agent.ipynb', 'result = agent.invoke');"><i class="fas fa-code"></i> agent.invoke</button> — Send the user message to the agent.

<details>
<summary>🆘 Need some help?</summary>

```python
result = agent.invoke(
    {"messages": [{"role": "user", "content": user}]},
    config={"configurable": {"thread_id": "cli"}},
)
```

</details>

<!-- fold:break -->

## Test Your Agent

After completing exercises 1-3, run the agent:

```bash
cd code/4-agent-customization && python3 -m bash_agent.main_langgraph
```

| Prompt | Expected |
|--------|----------|
| "List all files here" | `ls` or `ls -la` |
| "Find all Python files" | `find . -name "*.py"` |
| "What's my current directory?" | `pwd` |

**Next:** [Synthetic Data Generation](sdg.md)
