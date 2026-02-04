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

<!-- fold:break -->

## Why Synthetic Data Works

<details>
<summary><strong>The cold-start problem in detail</strong></summary>

New CLI tools face a chicken-and-egg problem:
- You need training data to build a good agent
- You need users to generate real training data
- You need a good agent to attract users

**SDG breaks this cycle:**

1. **Define the space** — Your Pydantic schema describes all valid outputs
2. **Sample systematically** — Samplers ensure every corner of the space is covered
3. **Generate natural language** — An LLM creates realistic user phrasings
4. **Result**: Training data without real users

**Why this works**: The model doesn't need *authentic* user phrasing—it needs to learn the *mapping* from intent to command. Synthetic variations are sufficient to learn that mapping, and you can always fine-tune later with real data once you have it.

</details>

<details>
<summary><strong>SDG vs. prompting an LLM to generate examples</strong></summary>

You might wonder: "Why not just ask GPT to generate 200 training examples?"

| Approach | Coverage | Validity | Diversity | Control |
|----------|----------|----------|-----------|---------|
| **LLM prompting** | Random, gaps likely | May hallucinate invalid outputs | Tends toward common patterns | Low |
| **NeMo Data Designer** | Guaranteed by samplers | Guaranteed by schema | Controlled by sampler config | High |

**The key difference**: Data Designer generates outputs *first* (from your schema), then creates matching inputs. LLM prompting generates inputs and hopes the outputs are valid.

```python
# LLM prompting approach (risky)
examples = llm("Generate 100 LangGraph CLI training examples")
# Problem: LLM might invent commands that don't exist!

# Data Designer approach (controlled)
outputs = sample_from_schema(CLIToolCall, n=100)  # Always valid
inputs = llm(f"Write a user request for: {output}")  # Input varies, output fixed
```

</details>

<details>
<summary><strong>What makes training data "good enough"?</strong></summary>

Training data quality matters more than quantity. Here's what to aim for:

**Minimum viable dataset:**
- At least 10-20 examples per command type
- At least 3-5 variations of each flag combination
- Total of 100-300 examples for simple CLIs

**Quality checklist:**
- [ ] Every command type appears multiple times
- [ ] Every flag appears in various combinations
- [ ] Edge cases are represented (empty paths, special characters, max values)
- [ ] Negative examples if needed (invalid commands → error response)

**Diminishing returns**: Beyond 500-1000 examples, adding more data helps less. Focus on diversity over quantity.

</details>

## Data Quality Checklist

Before training, verify your synthetic data meets these criteria:

### Coverage
- [ ] Does every command type appear? (`new`, `dev`, `up`, `build`, `dockerfile`)
- [ ] Does every flag appear for each relevant command?
- [ ] Are edge cases represented? (null values, boundary values)

### Balance
- [ ] Are command types roughly balanced?
- [ ] No single command should be > 40% of data unless that matches real usage

**Quick diagnostic:**
```python
from collections import Counter
commands = [json.loads(ex["output"])["command"] for ex in data]
print(Counter(commands))
# Good: Counter({'new': 55, 'dev': 48, 'up': 52, 'build': 45, 'dockerfile': 50})
# Bad:  Counter({'new': 180, 'dev': 10, 'up': 5, 'build': 3, 'dockerfile': 2})
```

### Diversity
- [ ] Do inputs vary in phrasing, not just slot values?
- [ ] Mix of formal and casual language?
- [ ] Different sentence structures (imperative, question, description)?

**Examples of good diversity:**
```
"Create a new project with react template"      (imperative)
"I want to start a react agent project"         (statement)
"Can you set up a react-agent-python project?"  (question)
"Initialize react-agent-python in ./myapp"      (technical)
```

### Validity
- [ ] Do all outputs parse as valid JSON?
- [ ] Do all outputs pass schema validation?
- [ ] Do command/flag combinations make sense?

```python
# Validate all outputs
for ex in data:
    output = json.loads(ex["output"])
    CLIToolCall(**output)  # Raises if invalid
print("All outputs valid!")
```

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