# GRPO Training

<img src="_static/robots/debug.png" alt="Training" style="float:right;max-width:250px;margin:15px;" />

**GRPO** (Group Relative Policy Optimization) fine-tunes the model using code-based verification instead of human judges.

## How It Works

1. Generate multiple outputs per prompt
2. NeMo Gym server scores each output (0.0 to 1.0)
3. Reinforce outputs that score above average

<!-- fold:break -->

## Setup

**Terminal 1** — Start reward server:
```bash
cd code/4-agent-customization/nemo_gym_resources/langgraph_cli
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Terminal 2** — Open the training notebook:

<button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/02_grpo_training.ipynb');"><i class="fa-solid fa-flask"></i> 02_grpo_training.ipynb</button>

<!-- fold:break -->

## Your Exercises

### Exercise 7: Create the Reward Function

<button onclick="goToLineAndSelect('code/4-agent-customization/02_grpo_training.ipynb', 'def reward_fn');"><i class="fas fa-code"></i> reward_fn</button> — The reward function calls NeMo Gym's `/verify` endpoint.

<details>
<summary>🆘 Need some help?</summary>

```python
def reward_fn(completions, prompts=None, **kwargs):
    rewards = []
    for i, completion in enumerate(completions):
        completion_text = completion[0]["content"] if completion else ""
        # ... lookup expected output ...
        verify_request = {
            "task_id": f"train-{i}",
            "task_input": {"input": user_query, "output": expected},
            "model_response": completion_text,
        }
        resp = requests.post(verify_endpoint, json=verify_request, timeout=30)
        reward = resp.json().get("reward", 0.0) if resp.status_code == 200 else 0.0
        rewards.append(reward)
    return np.array(rewards)
```

</details>

<!-- fold:break -->

### Exercise 8: Configure GRPO Training

<button onclick="goToLineAndSelect('code/4-agent-customization/02_grpo_training.ipynb', 'training_args = GRPOConfig');"><i class="fas fa-code"></i> GRPOConfig</button> — Set up the training hyperparameters.

<details>
<summary>🆘 Need some help?</summary>

```python
training_args = GRPOConfig(
    temperature=1.0,
    num_generations=4,  # Completions per prompt
    learning_rate=1e-5,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    max_steps=50,
    output_dir="outputs/grpo_langgraph_cli",
)
```

</details>

<!-- fold:break -->

### Exercise 9: Create the GRPO Trainer

<button onclick="goToLineAndSelect('code/4-agent-customization/02_grpo_training.ipynb', 'trainer = GRPOTrainer');"><i class="fas fa-code"></i> GRPOTrainer</button> — Wire up model, tokenizer, reward function, and dataset.

<details>
<summary>🆘 Need some help?</summary>

```python
trainer = GRPOTrainer(
    model=model,
    processing_class=tokenizer,
    reward_funcs=[reward_fn],
    args=training_args,
    train_dataset=train_dataset,
)
```

</details>

<!-- fold:break -->

## Run Training

After completing exercises 7-9, run `trainer.train()`:

- **GPU:** A100 80GB or H100 80GB
- **Time:** ~60-70 minutes

## Output

```
outputs/grpo_langgraph_cli/merged_model/
```

**Next:** [Running the Customized Agent](run_customized.md)
