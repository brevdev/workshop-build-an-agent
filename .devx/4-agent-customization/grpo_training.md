<div class="dx-hero" data-eyebrow="MODULE 04 / 04 - GRPO TRAINING" data-title="GRPO Training" data-meta="TIME::75 min|EXERCISES::3|GPU::A100-80GB+"></div>

You have your dataset. Now how do you teach the model with it?

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>SFT - SUPERVISED FINE-TUNING</h4>Memorize: input X produces output Y. Best for simple tasks with abundant data.</div>
  <div class="dx-cell is-wide"><h4>GRPO - RL-BASED</h4>Try multiple outputs, learn which score highest. Best for complex tasks with verifiable correctness.</div>
</div>

**GRPO (Group Relative Policy Optimization)** is a form of reinforcement learning with verifiable rewards (RLVR) that generates multiple candidate responses per prompt, scores them with a reward function, and reinforces the better ones. This exploration often discovers solutions that pure imitation would miss.

<!-- fold:break -->

## Verifiable Rewards

In Module 3, you learned about LLM-as-judge for evaluation. That works for subjective qualities (helpfulness, tone). But for **structured outputs**, we can do better.

CLI commands are either correct or wrong—no subjectivity. A reward server can check:
- Is the JSON valid?
- Is `command` one of `[new, dev, up, build, dockerfile]`?
- Are the parameters correct for that command type?

<div class="dx-island dx-reveal">
  <p class="dx-island-title">RLVR - RL WITH VERIFIABLE REWARDS</p>
  <ul>
    <li><span class="dx-chip">OBJECTIVE</span> no judge bias or inconsistency.</li>
    <li><span class="dx-chip">FAST</span> milliseconds per verification.</li>
    <li><span class="dx-chip">SCALABLE</span> no human annotators needed.</li>
  </ul>
</div>

The NeMo Gym server runs these checks and returns reward scores to guide training.

<!-- fold:break -->

## Understanding GRPO

**Click on each of the following questions to learn more.**

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-grpo_training-1">How does GRPO actually work?</button>
<div id="aside-grpo_training-1" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-grpo_training-1" popovertargetaction="hide" aria-label="Close">×</button>

GRPO (Group Relative Policy Optimization) is a form of reinforcement learning that learns from *relative* performance within a group of outputs:

1. **Generates multiple outputs** (typically 4-8) for each training prompt
2. **Scores each output** using a reward function (in our case, the NeMo Gym verifier)
3. **Computes advantages** — how much better each output is compared to the group average
4. **Updates weights** to increase probability of higher-reward outputs

**The key insight**: Instead of saying "memorize this exact answer," GRPO says "explore the output space and learn which patterns score higher." This exploration often discovers better solutions than pure imitation.

**Mathematical intuition**:
```
Advantage = (reward - group_mean) / group_std
Loss = -log(probability) * advantage
```

Outputs that score above the group average get reinforced; below-average outputs get suppressed. The model learns *what makes outputs good*, not just specific answers.

**Why "Group Relative"?** By comparing within a group rather than to a fixed baseline, GRPO adapts to the model's current ability level. Early in training when all outputs are poor, it still finds the *relatively* better ones to reinforce.

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-grpo_training-2">SFT vs GRPO: When to use which?</button>
<div id="aside-grpo_training-2" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-grpo_training-2" popovertargetaction="hide" aria-label="Close">×</button>

| Aspect | SFT (Supervised Fine-Tuning) | GRPO (RL-based) |
|--------|------------------------------|-----------------|
| **Learning signal** | "Copy this exact output" | "Outputs like this score higher" |
| **Data requirement** | Need perfect gold outputs | Need reward signal (can be noisy) |
| **Exploration** | None — imitates only | Yes — tries variations |
| **Overfitting risk** | High if data is small | Lower due to exploration |
| **Best for** | Abundant high-quality data | Verifiable correctness, structured outputs |

**Use SFT when:**
- You have thousands of human-verified examples
- The task has one clearly correct answer format
- You want fast, predictable training

**Use GRPO when:**
- You can programmatically verify correctness
- The output space has multiple valid solutions
- You want the model to discover optimal patterns

**For CLI agents**: GRPO excels because CLI commands are verifiable (they either parse correctly or don't), and there may be multiple valid ways to express the same command.

</div>
</div>

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-grpo_training-3">How do I know training is working?</button>
<div id="aside-grpo_training-3" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-grpo_training-3" popovertargetaction="hide" aria-label="Close">×</button>

**Key metrics to monitor during training:**

| Metric | Healthy Range | Warning Signs |
|--------|---------------|---------------|
| **Mean Reward** | Increasing over steps | Flat or decreasing after warmup |
| **Reward Std** | Decreasing over time | Remains high (model still uncertain) |
| **Loss** | Decreasing, then stabilizing | Oscillating wildly or exploding |
| **Gradient Norm** | Stable, typically < 10 | Exploding (> 100) or vanishing (< 0.001) |

**Red flags and what they mean:**

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| **Sparse rewards** | Mean reward stuck near 0 | Add partial credit for almost-correct outputs |
| **Reward hacking** | High training reward, poor real performance | Add more validation components; test on held-out data |
| **Inconsistent rewards** | Same output gets different scores | Ensure reward function is deterministic |
| **High Learning Rate** | Rewards spike and then crash | Learning rate too high; reduce by 2-5x |
| **Slow verification** | Training takes forever | Optimize reward code; batch requests to server |
| **Reward scale issues** | Gradients explode or vanish | Normalize rewards to [0, 1] range |

</div>
</div>

<!-- fold:break -->

## Reward Engineering

<img src="_static/robots/debug.png" alt="Reward Engineering" style="float:right;max-width:250px;margin:15px;" />

Your reward function is the most important piece of GRPO training. It defines what "good" means—get it wrong, and your model learns the wrong behaviors.

### Principles of Good Rewards

**Click on each of the following principles to learn more.**

<details class="dx-peek">
<summary>1. Verifiable — Check with code, not vibes</summary>

The power of RLVR is that rewards are *objective*. For CLI commands:

```python
# Good: Code-verifiable
def reward(output):
    try:
        parsed = json.loads(output)
        if parsed["command"] in VALID_COMMANDS:
            return 1.0
    except:
        pass
    return 0.0

# Bad: Subjective (requires LLM judge)
def reward(output):
    return llm_judge("Is this a good CLI command?", output)
```

LLM judges add latency, cost, and inconsistency. For structured outputs, code verification is always better.

</details>

<details class="dx-peek">
<summary>2. Granular — Partial credit beats binary pass/fail</summary>

A binary reward (1.0 or 0.0) provides sparse signal. The model doesn't know *how close* it was.

```python
# Binary (sparse signal)
reward = 1.0 if perfect_match else 0.0

# Granular (rich signal)
reward = (
    0.2 * json_is_valid +      # Got the format right
    0.3 * command_is_valid +    # Picked a real command
    0.5 * flags_are_correct     # Parameters match
)
```

With granular rewards, a response with correct JSON but wrong command scores 0.2 instead of 0.0. This gradient helps the model learn incrementally.

</details>

<details class="dx-peek">
<summary>3. Aligned — Reward what you actually care about</summary>

Models optimize for the reward you give, not the reward you intended. Be careful of:

- **Reward hacking**: Model finds shortcuts that score high but miss the point
- **Proxy gaming**: Optimizing a measurable proxy instead of true goal
- **Distributional shift**: Training rewards don't match deployment conditions

**Example of misaligned reward:**
```python
# Intended: Reward correct CLI commands
# Actual: Rewards ANY valid JSON
def bad_reward(output):
    try:
        json.loads(output)
        return 1.0  # Oops—empty {} scores perfectly!
    except:
        return 0.0
```

Always test your reward function on edge cases before training.

</details>

<!-- fold:break -->

### Anatomy of Our Reward Function

The NeMo Gym verifier computes a **composite reward** with multiple components:

<div class="dx-island dx-reveal">
  <p class="dx-island-title">COMPOSITE REWARD - WHERE THE POINTS COME FROM</p>
  <div class="dx-tax">
    <div class="dx-tax-row" style="--dx-w:20"><span class="dx-tax-name">json_format</span><div class="dx-tax-track"><div class="dx-tax-fill">0.2</div></div><span class="dx-tax-note">is it valid JSON?</span></div>
    <div class="dx-tax-row" style="--dx-w:30"><span class="dx-tax-name">command</span><div class="dx-tax-track"><div class="dx-tax-fill">0.3</div></div><span class="dx-tax-note">a real CLI command?</span></div>
    <div class="dx-tax-row" style="--dx-w:50"><span class="dx-tax-name">flag_accuracy</span><div class="dx-tax-track"><div class="dx-tax-fill">0.5</div></div><span class="dx-tax-note">flags correct for that command?</span></div>
  </div>
</div>

**Why these weights?** Flags carry the most information (many possible values), so they get the highest weight. JSON format is easiest, so it gets the lowest. Commands are intermediate.

<!-- fold:break -->

<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">Your reward returns 1.0 for any output that parses as valid JSON. Training reward soars, but real CLI accuracy is terrible. What happened?</p>
  <button class="dx-quiz-opt" data-right data-fb="Reward hacking. The model found a shortcut - e.g. emitting an empty {} - that scores high without doing the task. The reward is misaligned with the goal.">Reward hacking - the model maximizes the metric without doing the task</button>
  <button class="dx-quiz-opt" data-fb="The learning rate isn't the issue - the reward itself rewards the wrong thing. Even a perfect LR would just optimize the shortcut faster.">The learning rate is too high</button>
  <button class="dx-quiz-opt" data-fb="GRPO works fine for CLI tasks - that's the whole module. The failure is in reward design, not the algorithm.">GRPO doesn't work for CLI tasks</button>
  <button class="dx-quiz-opt" data-fb="An LLM judge is slower and less consistent, and wouldn't fix this. The fix is a granular, aligned code reward (format + command + flags).">You need an LLM judge instead of code</button>
</div>

<!-- fold:break -->

## The Full Training Loop

![GRPO Training Loop](img/grpo_training_loop_dark.svg)

To make this concrete, here's what happens in a single training step. The model sees: *"Create a new project with the react template"* and generates 4 candidates:

<div class="dx-term dx-reveal">
  <span class="dx-term-title">grpo-step</span>
  <span class="dx-term-line" data-kind="prompt">Create a new project with the react template</span>
  <span class="dx-term-line" data-kind="think" data-delay="300">Generate 4 candidates, score each with the NeMo Gym verifier, reinforce the best.</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[1] {command: new, template: react-agent-python, path: ./myapp}   reward 0.95</span>
  <span class="dx-term-line" data-kind="tool" data-delay="200">[2] {command: new, template: wrong-template}   reward 0.50</span>
  <span class="dx-term-line" data-kind="tool" data-delay="200">[3] {command: create, template: react}   reward 0.20</span>
  <span class="dx-term-line" data-kind="tool" data-delay="200">[4] not valid json   reward 0.00</span>
  <span class="dx-term-line" data-kind="think" data-delay="350">Candidate 1 is above the group average -> reinforce; candidate 4 far below -> suppress.</span>
  <span class="dx-term-line" data-kind="answer" data-delay="400">Over 50+ steps the model converges on candidate-1-style outputs.</span>
</div>

GRPO computes that Response #1 scored above the group average and reinforces its patterns. Response #4 scored far below, so those patterns are suppressed. Over many steps, the model converges toward reliably producing correct outputs.

<!-- fold:break -->

## GRPO: Hands-on Implementation

Open a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> window — Start reward server:

```bash
cd code/4-agent-customization/nemo_gym_resources/langgraph_cli && uvicorn app:app --host 0.0.0.0 --port 8000
```

Then open the following notebook: <button onclick="openOrCreateFileInJupyterLab('code/4-agent-customization/02_grpo_training.ipynb');"><i class="fa-solid fa-flask"></i> 02_grpo_training.ipynb</button>

<!-- fold:break -->

### Exercise: Reward Function

<button onclick="goToLineAndSelect('code/4-agent-customization/02_grpo_training.ipynb', 'def reward_fn');"><i class="fas fa-code"></i> reward_fn</button> — Call the NeMo Gym `/verify` endpoint to score model outputs.

Implement the reward function by making a call to the `/verify` endpoint. 

This is the bridge between GRPO and verifiable rewards: each model completion gets sent to the NeMo Gym server, which returns a composite reward score (JSON format + command correctness + flag accuracy). Implement `resp` by posting a request to `verify_endpoint` with `json` set to `verify_request` and the `timeout` set to 30s.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
resp = requests.post(verify_endpoint, json=verify_request, timeout=30)
```
</details>

<!-- fold:break -->

### Exercise: Training Config

<button onclick="goToLineAndSelect('code/4-agent-customization/02_grpo_training.ipynb', 'training_args = GRPOConfig');"><i class="fas fa-code"></i> GRPOConfig</button> — Configure the GRPO hyperparameters.

Implement some key training configuration parameters. 

These three settings control the core training dynamics: `num_generations` is how many candidate outputs GRPO generates per prompt (more = richer comparison signal), `learning_rate` controls the step size for weight updates, and `max_steps` caps the total training iterations. Implement `training_args` with `num_generations=4`, `learning_rate=1e-5`, and `max_steps=50`.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
training_args = GRPOConfig(
    ... # Keep other args as-is
    num_generations=4,
    ...
    learning_rate=1e-5,
    ...
    max_steps=50,
    ...
)
```
</details>

<!-- fold:break -->

### Exercise: GRPO Trainer

<button onclick="goToLineAndSelect('code/4-agent-customization/02_grpo_training.ipynb', 'trainer = GRPOTrainer');"><i class="fas fa-code"></i> GRPOTrainer</button> — Wire up the model, reward function, and dataset into the trainer.

Implement the `trainer` as a `GRPOTrainer` and wire up everything we've defined so far. 

The `GRPOTrainer` orchestrates the full training loop shown above: generate completions, score them via the reward function, and reinforce the best ones. Implement `trainer` with `model`, `processing_class` set to `tokenizer`, `reward_funcs` as a single-item list containing `reward_fn`, `args` set to `training_args`, and the `train_dataset`.

<details class="dx-peek is-solution">
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

### Train the Agent

Run `trainer.train()` notebook cell — depending on the number of iterations, this cell should take around **1 - 1.5 hours** to complete on an A100/H100.

> While the notebook should run on a DGX Spark (GB10), we highly recommend an A100/H100 GPU instance for faster training due to memory bandwidth constraints. 

The customized model should appear in this location when completed: `outputs/grpo_langgraph_cli/merged_model/`. 

<!-- fold:break -->

## Troubleshooting

If you're running into issues, click on any of the following to learn more. 

<details class="dx-peek is-solution">
<summary>Rewards not improving</summary>

**Possible causes and fixes:**

1. **Reward function bug**
   - Test manually: `reward_fn([{"content": '{"command": "new"}'}])`
   - Should return > 0 for valid outputs

2. **Learning rate too low**
   - Try increasing by 2x or 5x
   - Default 1e-5 is conservative; 5e-5 often works better

3. **Data lacks diversity**
   - Check: Are all training examples similar?
   - SDG should produce varied phrasings and command types

4. **Not enough training steps**
   - 50 steps is a minimum; try 100-200 for complex tasks

5. **Model capacity too small**
   - Larger base models learn faster (but cost more)

</details>

<details class="dx-peek is-solution">
<summary>Training crashes with OOM (Out of Memory)</summary>

**Solutions in order of preference:**

1. Reduce `num_generations` from 4 to 2
2. Reduce `per_device_train_batch_size` to 1
3. Increase `gradient_accumulation_steps` to compensate
4. Enable gradient checkpointing (usually on by default)
5. Use 8-bit or 4-bit quantization if model supports it
6. Reduce `max_seq_length` if your prompts allow

**Memory usage scales with:** batch_size × num_generations × seq_length

</details>

<details class="dx-peek is-solution">
<summary>Model outputs garbage after training</summary>

**Possible causes:**

1. **Catastrophic forgetting** — Learning rate too high destroyed base capabilities
   - Solution: Lower learning rate by 5-10x

2. **Overfit to reward function** — Model found degenerate solutions
   - Solution: Add more diverse training data; regularize

3. **Trained too long** — Passed optimal point
   - Solution: Use validation set to detect overfitting; save checkpoints

**Recovery:**
- Start from an earlier checkpoint (before degradation)
- Reduce learning rate significantly
- Add more training data variety

</details>

<details class="dx-peek is-solution">
<summary>Validation reward much lower than training reward</summary>

This indicates **overfitting** — the model memorized training examples rather than learning generalizable patterns.

**Solutions:**
1. Add more training data (SDG can generate more)
2. Increase `weight_decay` for regularization
3. Reduce training steps / use early stopping
4. Ensure training and validation have similar distributions

</details>

<!-- fold:break -->

<img src="_static/robots/wrench.png" alt="Bash Agent" style="float:right;max-width:300px;margin:15px;" />

Congrats, you now have successfully customized your Bash agent using Reinforcement Learning with Verifiable Rewards (RLVR) and Group Relative Policy Optimization (GRPO)!

Now that we've completed training the agent, let's run it again and see whether or not it's learned the new Langgraph CLI domain. Head over to [Run Customized Agent](run_customized.md) and get started!
