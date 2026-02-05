# Run Customized Agent

<img src="_static/robots/typewriter.png" alt="Running" style="float:right;max-width:250px;margin:15px;" />

Congratulations, you've now completed the customization pipeline:
1. ✅ Built a base agent (generic bash knowledge)
2. ✅ Generated training data (SDG for LangGraph CLI)
3. ✅ Trained with GRPO (verifiable rewards)

Now you have a **specialized agent**. The training baked LangGraph CLI knowledge directly into the agent.

<!-- fold:break -->

## Exercises

Open the following notebook: <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/03_run_agent.ipynb');"><i class="fa-solid fa-flask"></i> 03_run_agent.ipynb</button>

### Exercise: Load Model

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'llm = HuggingFaceLLM');"><i class="fas fa-code"></i> HuggingFaceLLM</button>

<details>
<summary>🆘 Need some help?</summary>

```python
llm = HuggingFaceLLM(config)
```
</details>

<!-- fold:break -->

### Exercise: System Prompt

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'messages = Messages');"><i class="fas fa-code"></i> Messages</button> — Use JSON prompt (matches training).

<details>
<summary>🆘 Need some help?</summary>

```python
messages = Messages(config.json_system_prompt)
```
</details>

<!-- fold:break -->

### Exercise: Execute

<button onclick="goToLineAndSelect('code/4-agent-customization/03_run_agent.ipynb', 'tool_result = bash.exec_bash_command');"><i class="fas fa-code"></i> exec_bash_command</button>

<details>
<summary>🆘 Need some help?</summary>

```python
if confirm_execution(command):
    tool_result = bash.exec_bash_command(command)
```
</details>

<!-- fold:break -->

## Run Agent Interactively

### Run the Customized Agent

After completing the exercises, start your new agent in the <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button>:

Make sure you're in the `code/4-agent-customization` directory:

```bash
code/4-agent-customization
```

And start your customized bash agent: 

```bash
python3 -m bash_agent.main_hf
```

<!-- fold:break -->

### Test the Customized Agent

Try some of the following commands and see how your agent has improved in its understanding with customization. 

| Request | Before Training | After Training |
|---------|-----------------|----------------|
| "List files" | ✅ `ls` | ✅ `ls` |
| "Create a react agent" | ❌ Hallucinated command | ✅ `langgraph new ./myapp --template react-agent-python` |
| "Start dev server on 8080" | ❌ Wrong parameters | ✅ `langgraph dev --port 8080` |
| "Build image tagged v2" | ❌ Missing flags | ✅ `langgraph build --tag v2` |

<!-- fold:break -->

## Measuring the Improvement

The reward function you built for GRPO training doubles as an evaluation metric. Run your validation set against both the base and trained models to quantify the improvement:

| Metric | Base Model | Trained Model |
|--------|-----------|---------------|
| **JSON Format Accuracy** | ~30% | ~95% |
| **Command Correctness** | ~10% | ~90% |
| **Flag Accuracy** | ~5% | ~85% |
| **Overall Mean Reward** | ~0.15 | ~0.90 |

This closes the loop with Module 3: the same evaluation mindset applies, but now your reward function provides **objective, automated scoring** rather than relying on an LLM judge.

<!-- fold:break -->

## What If Results Aren't Good Enough?

If the trained model still makes mistakes, apply the iterative improvement cycle from Module 3:

1. **Analyze failure patterns** — Which commands or flags fail most? Use the reward function's component scores (JSON format, command correctness, flag accuracy) to pinpoint weak spots.
2. **Generate targeted data** — SDG can oversample weak areas. If `dockerfile` commands have low accuracy, generate more examples with diverse `output_path` values.
3. **Adjust reward weights** — If the model gets commands right but flags wrong, increase the `flag_accuracy_reward` weight to focus training attention there.
4. **Train longer** — 50 steps is a starting point. Extending to 100-200 steps often improves edge case handling.

The pattern is always: **measure → diagnose → fix → retrain → re-measure**.

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

### The Full Workshop Arc

You've now traveled the complete agent development lifecycle:

| Module | What You Learned | Key Capability |
|--------|-----------------|----------------|
| **Module 1** | Build agents with ReAct | Agent fundamentals |
| **Module 2** | Extend with RAG, tools, and skills | Agent capabilities |
| **Module 3** | Measure and evaluate systematically | Agent quality |
| **Module 4** | Customize through training | Agent expertise |

This is the same cycle production teams follow: build, extend, measure, improve. Each module's skills compound—evaluation informs customization, customization produces measurable improvement, and the cycle continues.

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
