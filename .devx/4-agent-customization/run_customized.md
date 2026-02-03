# Running the Customized Agent

<img src="_static/robots/typewriter.png" alt="Running" style="float:right;max-width:250px;margin:15px;" />

Your model now understands both **bash commands** and **LangGraph CLI**.

## Your Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/03_run_agent.ipynb');"><i class="fa-solid fa-flask"></i> 03_run_agent.ipynb</button> and complete these exercises:

<!-- fold:break -->

### Exercise 10: Load the Trained Model

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'llm = HuggingFaceLLM');"><i class="fas fa-code"></i> HuggingFaceLLM</button> — Initialize the LLM with your trained model.

<details>
<summary>🆘 Need some help?</summary>

```python
llm = HuggingFaceLLM(config)
```

</details>

<!-- fold:break -->

### Exercise 11: Initialize with the Correct Prompt

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'messages = Messages');"><i class="fas fa-code"></i> Messages init</button> — Use the JSON system prompt (matches training!).

<details>
<summary>🆘 Need some help?</summary>

```python
messages = Messages(config.json_system_prompt)
```

</details>

<!-- fold:break -->

### Exercise 12: Process Tool Calls

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'tool_result = bash.exec_bash_command');"><i class="fas fa-code"></i> exec_bash_command</button> — Execute the command after user confirmation.

<details>
<summary>🆘 Need some help?</summary>

```python
if confirm_execution(command):
    tool_result = bash.exec_bash_command(command)
else:
    tool_result = {"error": "The user declined to execute this command."}
```

</details>

<!-- fold:break -->

## Run It

After completing exercises 10-12:

```bash
cd code/4-agent-customization
python3 -m bash_agent.main_hf
```

> Install LangGraph CLI first: `pip install langgraph-cli`

## Test Prompts

| Prompt | Expected Output |
|--------|-----------------|
| "List all files here" | `ls` (bash still works!) |
| "Create a new project at ./assistant using react-agent-python" | `langgraph new ./assistant --template react-agent-python` |
| "Start the dev server on port 8080 without opening a browser" | `langgraph dev --port 8080 --no-browser` |
| "Build a Docker image and tag it as myapp:v2" | `langgraph build --tag myapp:v2` |

<!-- fold:break -->

## Key Points

- ✅ Agent handles **both** bash and LangGraph CLI commands
- ✅ Always asks for confirmation before executing
- ✅ Training specialized the model for LangGraph CLI
- ✅ Combined system prompt enables full functionality

**Extension:** [Safe Execution & Sandboxing](sandboxing.md)
