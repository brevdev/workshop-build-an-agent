# Synthetic Data Generation

<img src="_static/robots/magician.png" alt="SDG" style="float:right;max-width:250px;margin:15px;" />

## The Data Problem

Training requires examples—lots of them. Each example shows the model:
- **Input**: What the user says (*"Create a new project with the react template"*)
- **Output**: What the agent should produce (`{"command": "new", "template": "react-agent-python", ...}`)

But where do these examples come from?

| Source | Pros | Cons |
|--------|------|------|
| **Real user logs** | Authentic patterns | You don't have them yet |
| **Manual writing** | High quality | Slow, expensive, limited diversity |
| **Synthetic generation** | Fast, scalable, diverse | Requires careful design |

For a new domain like LangGraph CLI, we don't have real logs. Manual writing doesn't scale. **SDG is the answer.**

## How SDG Works

**NeMo Data Designer** generates training data programmatically:

1. **Define the output schema** — A Pydantic model describing valid CLI commands
2. **Configure samplers** — Distributions for each field (which commands? which templates? which ports?)
3. **Generate natural language** — An LLM creates realistic user requests for each command
4. **Combine into examples** — Input/output pairs ready for training

This is different from just prompting an LLM to "make up examples." Data Designer ensures:
- **Coverage** — Every command type appears in training
- **Diversity** — Varied phrasing, not repetitive patterns
- **Validity** — Outputs match your schema exactly

## Connection to Evaluation

Remember Module 3's evaluation metrics? The same principles apply here:

- **Ground truth** — SDG gives you known-correct outputs to train against
- **Structured verification** — JSON schema ensures outputs are machine-checkable
- **Train/val split** — Hold out data to measure generalization

The evaluation dataset from Module 3 could even become training data for Module 4.

## Choose Your Path

| Option | Time |
|--------|------|
| **A: Use pre-generated data** | Skip to [GRPO Training](grpo_training.md) |
| **B: Generate your own** | 15-20 min (continue below) |

> 📁 Pre-generated: `data/langgraph_cli/` (250 examples)

<!-- fold:break -->

## Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/01_synthetic_data_generation.ipynb');"><i class="fa-solid fa-flask"></i> 01_synthetic_data_generation.ipynb</button>

### Exercise 4: Output Schema

<button onclick="goToLineAndSelect('code/4-agent-customization/01_synthetic_data_generation.ipynb', 'class CLIToolCall');"><i class="fas fa-code"></i> CLIToolCall</button> — Define Pydantic model for CLI commands.

<details>
<summary>🆘 Hint</summary>

```python
class CLIToolCall(BaseModel):
    command: str
    template: Optional[str] = None
    path: Optional[str] = None
    port: Optional[int] = None
```
</details>

<!-- fold:break -->

### Exercise 5: Template Sampler

<button onclick="goToLineAndSelect('code/4-agent-customization/01_synthetic_data_generation.ipynb', 'react-agent-python');"><i class="fas fa-code"></i> template sampler</button> — Configure template values.

<details>
<summary>🆘 Hint</summary>

```python
params=CategorySamplerParams(values=[
    "react-agent-python", 
    "memory-agent-python"
])
```
</details>

<!-- fold:break -->

### Exercise 6: Train/Val Split

<button onclick="goToLineAndSelect('code/4-agent-customization/01_synthetic_data_generation.ipynb', 'train_test_split');"><i class="fas fa-code"></i> train_test_split</button>

<details>
<summary>🆘 Hint</summary>

```python
train_data, val_data = train_test_split(data, test_size=0.1)
```
</details>

## Output

```
data/langgraph_cli/
├── train.jsonl    # 225 examples
└── val.jsonl      # 25 examples
```

**Next:** [GRPO Training](grpo_training.md)