# Run Customized Agent

<img src="_static/robots/typewriter.png" alt="Running" style="float:right;max-width:250px;margin:15px;" />

## What Changed

Your model is no longer generic—it's been **specialized**. The training baked LangGraph CLI knowledge directly into the weights. It now:

- Knows `langgraph new`, `dev`, `build`, `up`, `dockerfile` commands
- Understands which templates exist (`react-agent-python`, `memory-agent-python`)
- Generates correct parameters without hallucinating

## Why This Matters

Before training, asking *"create a react agent"* might produce gibberish or a wrong command. After training, the model reliably produces `langgraph new ./myapp --template react-agent-python`.

This is the payoff: **domain expertise without tool overhead**. No MCP server, no skill definitions—just a model that *knows* your CLI.

## Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/03_run_agent.ipynb');"><i class="fa-solid fa-flask"></i> 03_run_agent.ipynb</button>

<!-- fold:break -->

### Exercise 10: Load Model

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'llm = HuggingFaceLLM');"><i class="fas fa-code"></i> HuggingFaceLLM</button>

<details>
<summary>🆘 Hint</summary>

```python
llm = HuggingFaceLLM(config)
```
</details>

### Exercise 11: System Prompt

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'messages = Messages');"><i class="fas fa-code"></i> Messages</button> — Use JSON prompt (matches training).

<details>
<summary>🆘 Hint</summary>

```python
messages = Messages(config.json_system_prompt)
```
</details>

### Exercise 12: Execute

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'tool_result = bash.exec_bash_command');"><i class="fas fa-code"></i> exec_bash_command</button>

<details>
<summary>🆘 Hint</summary>

```python
if confirm_execution(command):
    tool_result = bash.exec_bash_command(command)
```
</details>

<!-- fold:break -->

## Test It

```bash
cd code/4-agent-customization && python3 -m bash_agent.main_hf
```

| Try | Expected |
|-----|----------|
| "List files" | `ls` |
| "Create react agent at ./myapp" | `langgraph new ./myapp --template react-agent-python` |
| "Build image tagged v2" | `langgraph build --tag v2` |

**Extension:** [Sandboxing](sandboxing.md)
