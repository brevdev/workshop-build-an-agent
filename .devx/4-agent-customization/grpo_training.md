# GRPO Training

<img src="_static/robots/debug.png" alt="Training" style="float:right;max-width:250px;margin:15px;" />

## What It Does

**GRPO (Group Relative Policy Optimization)** teaches the model through trial and feedback. The model generates multiple answers, a verifier scores them, and the model learns to produce higher-scoring outputs.

## Why GRPO Works

Traditional fine-tuning says *"memorize this answer."* GRPO says *"try things and learn what works."*

- **Verifiable rewards** — Code checks if the output is valid JSON, has correct fields, uses real CLI commands. No human judges needed.
- **Multiple attempts** — Model generates 4+ responses per prompt, learns from the best ones.
- **Reinforcement signal** — Good outputs get reinforced, bad outputs get suppressed.

This is **RLVR (RL with Verifiable Rewards)**—perfect for structured outputs like CLI commands where correctness is objective.

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
