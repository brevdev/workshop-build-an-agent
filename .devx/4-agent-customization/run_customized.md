# Run Customized Agent

<img src="_static/robots/typewriter.png" alt="Running" style="float:right;max-width:250px;margin:15px;" />

You've completed the customization pipeline:
1. ✅ Built a base agent (generic bash knowledge)
2. ✅ Generated training data (SDG for LangGraph CLI)
3. ✅ Trained with GRPO (verifiable rewards)

Now you have a **specialized model**. The training baked LangGraph CLI knowledge directly into the weights.

<!-- fold:break -->

## Before vs After

| Request | Before Training | After Training |
|---------|-----------------|----------------|
| "Create a react agent" | ❌ Hallucinated command | ✅ `langgraph new ./myapp --template react-agent-python` |
| "Start dev server on 8080" | ❌ Wrong parameters | ✅ `langgraph dev --port 8080` |
| "Build image tagged v2" | ❌ Missing flags | ✅ `langgraph build --tag v2` |

<!-- fold:break -->

## Connecting Back to Evaluation

Remember Module 3's evaluation pipeline? You can now measure the improvement:

1. Run the **same test cases** against base vs trained model
2. Check **tool usage accuracy** — Does it pick the right command?
3. Verify **parameter correctness** — Are arguments valid?

The reward function from GRPO training can serve as your production evaluation metric.

<!-- fold:break -->

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

<!-- fold:break -->

### Exercise 11: System Prompt

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'messages = Messages');"><i class="fas fa-code"></i> Messages</button> — Use JSON prompt (matches training).

<details>
<summary>🆘 Hint</summary>

```python
messages = Messages(config.json_system_prompt)
```
</details>

<!-- fold:break -->

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

<!-- fold:break -->

## Module Wrap-Up

<img src="_static/robots/finish.png" alt="Finish Line" style="float:right;max-width:250px;margin:15px;" />

Congratulations! You've completed the Agent Customization module. Let's recap what you've accomplished.

### What You Learned

| Topic | Key Takeaway |
|-------|--------------|
| **Why Customize** | Training beats Skills/MCP for depth; use both for breadth + depth |
| **The Pipeline** | SDG → GRPO → Deployment is a repeatable pattern |
| **Synthetic Data** | Schema-driven generation ensures coverage, diversity, and validity |
| **Verifiable Rewards** | Code-based verification is faster and more consistent than LLM judges |
| **GRPO Training** | Exploration-based learning discovers better solutions than imitation |
| **Safe Execution** | Allowlists and human-in-the-loop protect against dangerous commands |

<!-- fold:break -->

### The Generalizable Pattern

Everything you learned extends beyond LangGraph CLI:

| Domain | Output Schema | Verification |
|--------|---------------|--------------|
| **kubectl** | Kubernetes resource specs | `kubectl apply --dry-run` |
| **terraform** | HCL resource definitions | `terraform validate` |
| **SQL** | Query structure | Database execution / EXPLAIN |
| **docker** | Container commands | Docker CLI validation |
| **Your internal CLI** | Your Pydantic models | Your validation logic |

The pattern is always:
1. **Define schema** — What are valid outputs?
2. **Generate data** — Cover the output space systematically
3. **Design rewards** — How do you verify correctness with code?
4. **Train with GRPO** — Let the model explore and learn

<!-- fold:break -->

### Skills You've Practiced

- [x] Implementing human-in-the-loop safety wrappers
- [x] Designing Pydantic schemas for structured outputs
- [x] Configuring samplers for data diversity
- [x] Building reward functions for verifiable correctness
- [x] Running GRPO training with NeMo Gym
- [x] Evaluating before/after training improvements

<!-- fold:break -->

### What's Next?

**Immediate extensions:**
- Expand SDG to cover more commands and edge cases
- Increase training steps for better performance
- Add more sophisticated reward components

**Production considerations:**
- Deploy trained model behind an API
- Set up continuous evaluation monitoring
- Plan retraining schedule as CLI evolves

**Advanced topics:**
- Multi-turn conversations with trained models
- Combining Skills + trained models for breadth + depth
- Distillation from larger models to smaller ones

<!-- fold:break -->

### Final Thought

Agent customization isn't magic—it's engineering. You've learned a systematic approach: measure the gap (Module 3), generate targeted data (SDG), define success criteria (rewards), and train (GRPO). This cycle applies wherever you need agents with domain expertise.

The best agents aren't built in one pass. They're refined iteratively through measurement and improvement. You now have the tools to make that process systematic.

Happy building!
