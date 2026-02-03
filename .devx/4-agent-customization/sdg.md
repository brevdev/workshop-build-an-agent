# Synthetic Data Generation

<img src="_static/robots/magician.png" alt="SDG" style="float:right;max-width:250px;margin:15px;" />

**SDG** uses AI to generate training data when real usage logs don't exist.

## Choose Your Path

> **Option A: Use Pre-Generated Data** (Recommended for time-limited workshops)
> 
> We've included 250 training examples in `data/langgraph_cli/`. Skip to [GRPO Training](grpo_training.md).

> **Option B: Generate Your Own Data** (15-20 min)
> 
> Learn how SDG works by generating your own dataset. Continue below.

<!-- fold:break -->

## How SDG Works

1. **Seed values** — Define command distributions (new, dev, build)
2. **Natural language** — LLM generates diverse user requests
3. **Structured output** — Validated JSON tool calls

<!-- fold:break -->

## Your Exercises

Open <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/01_synthetic_data_generation.ipynb');"><i class="fa-solid fa-flask"></i> 01_synthetic_data_generation.ipynb</button> and complete these exercises:

### Exercise 4: Define the Output Schema

<button onclick="goToLineAndSelect('code/4-agent-customization/01_synthetic_data_generation.ipynb', 'class CLIToolCall');"><i class="fas fa-code"></i> CLIToolCall schema</button> — Define the Pydantic model for CLI commands.

<details>
<summary>🆘 Need some help?</summary>

```python
class CLIToolCall(BaseModel):
    command: str = Field(..., description="CLI command: new, dev, up, build, or dockerfile")
    template: Optional[str] = Field(None, description="Template name for 'new' command")
    path: Optional[str] = Field(None, description="Project path for 'new' command")
    port: Optional[int] = Field(None, description="Port for 'dev' or 'up' command")
    no_browser: Optional[bool] = Field(None, description="Skip browser for 'dev' command")
    watch: Optional[bool] = Field(None, description="Watch mode for 'up' command")
    tag: Optional[str] = Field(None, description="Image tag for 'build' command")
```

</details>

<!-- fold:break -->

### Exercise 5: Configure the Template Sampler

<button onclick="goToLineAndSelect('code/4-agent-customization/01_synthetic_data_generation.ipynb', 'name=\"template\"');"><i class="fas fa-code"></i> template sampler</button> — Set up the template values for the `new` command.

<details>
<summary>🆘 Need some help?</summary>

```python
config_builder.add_column(
    SamplerColumnConfig(
        name="template",
        sampler_type=SamplerType.CATEGORY,
        params=CategorySamplerParams(values=[
            "react-agent-python", 
            "memory-agent-python", 
            "retrieval-agent-python", 
            "data-enrichment-agent-python",
            "new-langgraph-project-python"
        ])
    )
)
```

</details>

<!-- fold:break -->

### Exercise 6: Split Train/Validation Data

<button onclick="goToLineAndSelect('code/4-agent-customization/01_synthetic_data_generation.ipynb', 'train_test_split');"><i class="fas fa-code"></i> train_test_split</button> — Split the dataset for training and validation.

<details>
<summary>🆘 Need some help?</summary>

```python
train_data, val_data = train_test_split(data, test_size=0.1, random_state=42)
```

</details>

<!-- fold:break -->

## Output

After running the notebook (or using pre-generated data):

```
data/langgraph_cli/
├── train.jsonl    # 225 examples
└── val.jsonl      # 25 examples
```

Example record:
```json
{"input": "Create a new project at ./assistant using react-agent-python", 
 "output": {"command": "new", "template": "react-agent-python", "path": "./assistant", ...}}
```

**Next:** [GRPO Training](grpo_training.md)
