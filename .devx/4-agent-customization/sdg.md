# Synthetic Data Generation

<img src="_static/robots/magician.png" alt="SDG" style="float:right;max-width:250px;margin:15px;" />

Training requires examples—lots of them. Each example shows the model:
- **Input**: What the user says (*"Create a new project with the react template"*)
- **Output**: What the agent should produce (`{"command": "new", "template": "react-agent-python", ...}`)

But where do these examples come from?

| Source | Pros | Cons |
|--------|------|------|
| **Real user logs** | Authentic patterns | You don't have them yet |
| **Manual writing** | High quality | Slow, expensive, limited diversity |
| **Synthetic generation** | Fast, scalable, diverse | Requires careful design |

For a new domain like the LangGraph CLI, we don't have the real logs from the agent. Manual writing doesn't scale. **SDG is the answer.**

<!-- fold:break -->

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

Click on each of the following items to learn more. 

<details>
<summary><strong>The Cold Start Problem</strong></summary>

New CLI tools face a chicken-and-egg problem:
- You need training data to build a good agent
- You need users to generate real training data
- You need a good agent to attract users

**SDG breaks this cycle:**

1. **Define the space** — Your Pydantic schema describes all valid outputs
2. **Sample systematically** — Samplers ensure every corner of the space is covered
3. **Generate natural language** — An LLM creates realistic user phrasings
4. **Result**: Real training data without real users

**Why this works**: The model doesn't need *authentic* user phrasing—it needs to learn the *mapping* from intent to command. Synthetic variations are sufficient to learn that mapping, and you can always fine-tune later with real data once you have it.

</details>

<details>
<summary><strong>SDG vs. LLM Prompting</strong></summary>

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
<summary><strong>What makes Training Data "Good Enough"?</strong></summary>

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

<!-- fold:break -->

## Data Quality Checklist

Before training, verify your synthetic data meets these criteria. **Click each item to learn more.**

<details>
<summary><strong>Coverage</strong></summary>

- [ ] Does every command type appear? (`new`, `dev`, `up`, `build`, `dockerfile`)
- [ ] Does every flag appear for each relevant command?
- [ ] Are edge cases represented? (null values, boundary values)

</details>

<details>
<summary><strong>Balance</strong></summary>

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

</details>

<details>
<summary><strong>Diversity</strong></summary>

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

</details>

<details>
<summary><strong>Validity</strong></summary>

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

</details>

<!-- fold:break -->

## Sample Datasets

We recommend generating your own datasets to get hands-on experience with the synthetic data generation process. However, if you're running into issues or want to move ahead quickly, we've provided a starter dataset you can use. 

> 📁 Sample Training Data (225 examples): <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/data/langgraph_cli/train.jsonl');"><i class="fa-brands fa-python"></i> train.jsonl</button>

These pre-made dataset can also serve as reference examples when you create your own.

<!-- fold:break -->

## SDG: Hands On Implementation

Open the <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/01_synthetic_data_generation.ipynb');"><i class="fa-solid fa-flask"></i> 01_synthetic_data_generation.ipynb</button> notebook. 

### Exercise: Output Schema

<button onclick="goToLineAndSelect('code/4-agent-customization/01_synthetic_data_generation.ipynb', 'class CLIToolCall');"><i class="fas fa-code"></i> CLIToolCall</button> — Define Pydantic model for CLI commands. 

Include `command` (str), `template` (optional str), `path` (optional str), and `port` (optional str) fields. 

<details>
<summary>🆘 Need some help?</summary>

```python
class CLIToolCall(BaseModel):
    command: str
    template: Optional[str] = None
    path: Optional[str] = None
    port: Optional[int] = None
```
</details>

<!-- fold:break -->

### Exercise: Template Sampler

<button onclick="goToLineAndSelect('code/4-agent-customization/01_synthetic_data_generation.ipynb', 'react-agent-python');"><i class="fas fa-code"></i> template sampler</button> — Configure template values.

Include the `react-agent-python` and `memory-agent-python` parameters in the list of `values`.

<details>
<summary>🆘 Need some help?</summary>

```python
params=CategorySamplerParams(values=[
    "react-agent-python", 
    "memory-agent-python"
])
```
</details>

<!-- fold:break -->

### Exercise: Train/Val Split

<button onclick="goToLineAndSelect('code/4-agent-customization/01_synthetic_data_generation.ipynb', 'train_test_split');"><i class="fas fa-code"></i> train_test_split</button>

Split the `data` and set the `test_size` to 0.1.

<details>
<summary>🆘 Need some help?</summary>

```python
train_data, val_data = train_test_split(data, test_size=0.1)
```
</details>

<!-- fold:break -->

## Output

Double check that you have successfully generated synthetic data for the LangGraph CLI.

```
data/langgraph_cli/
├── train.jsonl    # 225 examples
└── val.jsonl      # 25 examples
```

With this data, we are now ready to begin the customization. Check out [GRPO Training](grpo_training.md) to learn more and get started!