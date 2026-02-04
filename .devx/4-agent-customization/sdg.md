# Synthetic Data Generation

<img src="_static/robots/magician.png" alt="SDG" style="float:right;max-width:250px;margin:15px;" />

## What It Does

**SDG (Synthetic Data Generation)** creates training examples automatically. Instead of manually writing hundreds of input/output pairs, we define *what kind* of data we want and let the system generate variations.

## Why We Need It

Training requires data—lots of it. For a new domain (like LangGraph CLI), we don't have real user logs yet. SDG solves the cold-start problem:

1. **Define the schema** — What does a valid CLI command look like?
2. **Set the variations** — Which templates? Which paths? Which ports?
3. **Generate at scale** — 250 diverse examples in minutes

The result: training data that teaches the model *"when user says X, output Y"*.

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
