# GRPO Training

<img src="_static/robots/debug.png" alt="Training" style="float:right;max-width:250px;margin:15px;" />

## Two Ways to Train

You have your data. Now how do you teach the model?

| Approach | How It Works | Best For |
|----------|--------------|----------|
| **SFT (Supervised Fine-Tuning)** | "Memorize: input X → output Y" | Simple tasks, abundant data |
| **GRPO (RL-based)** | "Try multiple outputs, learn which score highest" | Complex tasks, verifiable correctness |

**GRPO (Group Relative Policy Optimization)** generates multiple candidate responses per prompt, scores them with a reward function, and reinforces the better ones. This exploration often discovers solutions that pure imitation would miss.

## Why Verifiable Rewards Matter

In Module 3, you learned about LLM-as-judge for evaluation. That works for subjective qualities (helpfulness, tone). But for **structured outputs**, we can do better.

CLI commands are either correct or wrong—no subjectivity. A reward server can check:
- Is the JSON valid?
- Is `command` one of `[new, dev, up, build, dockerfile]`?
- Are the parameters correct for that command type?

This is **RLVR (RL with Verifiable Rewards)**:
- **Objective** — No judge bias or inconsistency
- **Fast** — Milliseconds per verification
- **Scalable** — No human annotators needed

The NeMo Gym server runs these checks and returns reward scores to guide training.

## The Training Loop

1. Model generates 4+ responses to each prompt
2. Reward server scores each response (0.0 to 1.0)
3. GRPO computes gradients that favor higher-scoring responses
4. Repeat for 50+ steps until the model reliably produces correct outputs

## Setup

**Terminal 1** — Start reward server:
```bash
cd code/4-agent-customization/nemo_gym_resources/langgraph_cli
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Terminal 2** — Open notebook:

<button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/02_grpo_training.ipynb');"><i class="fa-solid fa-flask"></i> 02_grpo_training.ipynb</button>

<!-- fold:break -->

## Exercises

### Exercise 7: Reward Function

<button onclick="goToLineAndSelect('code/4-agent-customization/02_grpo_training.ipynb', 'def reward_fn');"><i class="fas fa-code"></i> reward_fn</button> — Call NeMo Gym `/verify` endpoint.

<details>
<summary>🆘 Hint</summary>

```python
resp = requests.post(verify_endpoint, json=verify_request)
reward = resp.json().get("reward", 0.0)
```
</details>

<!-- fold:break -->

### Exercise 8: Config

<button onclick="goToLineAndSelect('code/4-agent-customization/02_grpo_training.ipynb', 'training_args = GRPOConfig');"><i class="fas fa-code"></i> GRPOConfig</button>

<details>
<summary>🆘 Hint</summary>

```python
training_args = GRPOConfig(
    num_generations=4,
    learning_rate=1e-5,
    max_steps=50,
)
```
</details>

<!-- fold:break -->

### Exercise 9: Trainer

<button onclick="goToLineAndSelect('code/4-agent-customization/02_grpo_training.ipynb', 'trainer = GRPOTrainer');"><i class="fas fa-code"></i> GRPOTrainer</button>

<details>
<summary>🆘 Hint</summary>

```python
trainer = GRPOTrainer(
    model=model,
    reward_funcs=[reward_fn],
    train_dataset=train_dataset,
)
```
</details>

## Run

Run `trainer.train()` — **~60-70 min** on A100/H100.

Output: `outputs/grpo_langgraph_cli/merged_model/`

**Next:** [Run Customized Agent](run_customized.md)
