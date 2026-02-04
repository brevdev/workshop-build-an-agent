# Run Customized Agent

<img src="_static/robots/typewriter.png" alt="Running" style="float:right;max-width:250px;margin:15px;" />

## The Payoff

You've completed the customization pipeline:
1. ✅ Built a base agent (generic bash knowledge)
2. ✅ Generated training data (SDG for LangGraph CLI)
3. ✅ Trained with GRPO (verifiable rewards)

Now you have a **specialized model**. The training baked LangGraph CLI knowledge directly into the weights.

## Before vs After

| Request | Before Training | After Training |
|---------|-----------------|----------------|
| "Create a react agent" | ❌ Hallucinated command | ✅ `langgraph new ./myapp --template react-agent-python` |
| "Start dev server on 8080" | ❌ Wrong parameters | ✅ `langgraph dev --port 8080` |
| "Build image tagged v2" | ❌ Missing flags | ✅ `langgraph build --tag v2` |

## Connecting Back to Evaluation

Remember Module 3's evaluation pipeline? You can now measure the improvement:

1. Run the **same test cases** against base vs trained model
2. Check **tool usage accuracy** — Does it pick the right command?
3. Verify **parameter correctness** — Are arguments valid?

The reward function from GRPO training can serve as your production evaluation metric.

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
