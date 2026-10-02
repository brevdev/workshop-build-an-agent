<div class="dx-hero" data-eyebrow="MODULE 04 / 01 - CONCEPTS" data-title="Introduction to Customization" data-meta="READ::15 min|CONCEPTS::3"></div>

In Module 3, you learned to **measure** agent performance — faithfulness, relevance, tone, and so on. But what happens when the metrics reveal problems?

Typically, you have three overarching levers:

<div class="dx-island dx-reveal">
  <p class="dx-island-title">THREE WAYS TO IMPROVE AN AGENT</p>
  <ul>
    <li><span class="dx-chip">PROMPT ENGINEERING</span> tweak the agent's instructions - quick, but limited.</li>
    <li><span class="dx-chip">ADD TOOLS / SKILLS</span> give the agent more functionality - expands capability.</li>
    <li><span class="dx-chip">TRAIN THE MODEL</span> update its weights to improve a measured task.</li>
  </ul>
</div>

Options 1 and 2 were covered in Modules 1 and 2. When errors remain, compare those approaches with training using the same evaluation tasks.

<!-- fold:break -->

## Model Customization

Before diving into the specifics, let's build intuition for what "training" actually means in this context. Let's begin with models. 

A pretrained model has already learned useful language and task patterns. Customization updates those weights for your task. A small dataset can help with a narrow task, but improvement and regressions both need evaluation.

There are two main approaches to training:

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>SFT - SUPERVISED FINE-TUNING</h4>Learn from supervised input/output examples. Works well with abundant, high-quality examples.</div>
  <div class="dx-cell is-wide"><h4>GRPO - RL-BASED</h4>Try multiple answers, learn which score highest. Useful when you can programmatically score correctness.</div>
</div>

Both methods can generalize or overfit. Here we explore **GRPO** because CLI output can be scored with code.

<!-- fold:break -->

## Agent Customization

<img src="_static/robots/study.png" alt="Customization" style="float:right;max-width:250px;margin:15px;" />

Now, let's apply this to agents. When your agent needs domain expertise, you have two architectural choices:

### Path A: Skills & MCP (Runtime Knowledge)

In Module 2, you added **Skills** (dynamic instructions the agent loads) and **MCP** (tools the agent calls). This works well for:

- General-purpose capabilities (web search, calendar, email)
- Workflows that are repeatable and/or change frequently
- Knowledge that's too large to train on
- Use cases that can afford a bit of latency

**The limitation**: More tools and instructions can make selection harder. Measure errors for your task instead of relying on a fixed tool-count limit.

> 💡 **Key question**: Do prompts and tools already meet your task's quality target? If they do, training's added data, compute and maintenance may not be justified.

<!-- fold:break -->

### Path B: Training (Baked-in Knowledge)

Training writes knowledge directly into the model's weights. It can learn useful output patterns, but expertise still needs evaluation. This works well for:

- Stable, well-defined domains (your specific CLI, your API)
- Workflows that are one-time, set-and-forget, or don't change frequently
- Tasks requiring precise structured output
- High-frequency use cases where latency matters

**The trade-off**: Upfront investment in data and compute, plus evaluation and maintenance when the domain changes.

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>SKILLS / MCP</h4><span class="dx-chip">BREADTH</span> Best for many simple tools and changing procedures - flexibility at runtime.</div>
  <div class="dx-cell is-wide"><h4>TRAINING</h4><span class="dx-chip">DEPTH</span> Best for your core domain and structured outputs - learned output patterns that need evaluation.</div>
</div>

> 💡 **Rule of thumb**: Use Skills/MCP for breadth. Use training for depth. Many production systems combine both.

<!-- fold:break -->

<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">Your agent already does the job with good prompts and a couple of tools, and the metrics look fine. Should you train it?</p>
  <button class="dx-quiz-opt" data-right data-fb="Right. If prompts and tools meet your quality target, training adds cost without an established need. Evaluate it when important errors remain.">Probably not - if prompts and tools already work, training's upfront cost isn't justified</button>
  <button class="dx-quiz-opt" data-fb="Training is not a free upgrade - it costs data and compute. Reach for it only when prompting and tools genuinely fall short.">Yes - training always improves performance</button>
  <button class="dx-quiz-opt" data-fb="They are complementary, not exclusive. Many production systems use prompts and tools for breadth and training for depth.">Yes - training replaces prompts and tools</button>
  <button class="dx-quiz-opt" data-fb="Hardware is a logistics question, not the deciding factor. The real question is whether the model lacks domain understanding that prompts and tools cannot supply.">Only if you have a spare GPU</button>
</div>

<!-- fold:break -->

## The Customization Pipeline

Training an agent requires three components working together:

![Customization Pipeline](img/customization_pipeline_dark.svg)

<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>1 &middot; GENERATE DATA</h4><span class="dx-chip">NeMo Data Designer</span> Sample the command cases you define, then review coverage and labels.</div>
  <div class="dx-cell"><h4>2 &middot; DEFINE REWARDS</h4><span class="dx-chip">NeMo Gym</span> Code-based verification scores each output - deterministic, fast, no judge drift.</div>
  <div class="dx-cell"><h4>3 &middot; TRAIN</h4><span class="dx-chip">GRPO</span> The model generates candidates, the reward server scores them, the best are reinforced.</div>
</div>

### 1. Training Data (NeMo Data Designer)

You need examples of what the agent should do. For a CLI agent:
- **Input**: "Create a new react agent project in ./myapp"
- **Output**: `{"command": "new", "template": "react-agent-python", "path": "./myapp"}`

**The cold-start problem**: You don't have real user logs yet. **Synthetic Data Generation (SDG)** solves this by programmatically creating diverse, realistic examples from templates and variations.

<!-- fold:break -->

### 2. Success Metrics (NeMo Gym)

How does the model know if its output is good? In Module 3, you used LLM-as-judge. For well-structured outputs like CLI commands, we can do better: **code-based verification**.

A reward server checks:
- Is the JSON valid?
- Is `<command>` a real CLI command?
- Are the parameters correct for that command?

This is **RLVR (Reinforcement Learning with Verifiable Rewards)** — deterministic, consistent, and scalable.

<!-- fold:break -->

### 3. Training Algorithm (GRPO)

Supervised fine-tuning learns from target answers. **GRPO (Group Relative Policy Optimization)** instead samples answers and uses their relative rewards. Either method can generalize or overfit; measure both on held-out tasks.

This notebook generates 4 candidate responses per prompt. The reward server scores each one, and relative scores guide updates toward higher-reward outputs. That does not guarantee an advantage over SFT on another task.

| Step | Tool | What It Does |
|------|------|--------------|
| Generate data | **NeMo Data Designer** | Creates input/output training pairs |
| Define rewards | **NeMo Gym** | Verifies outputs with code |
| Train model | **GRPO** | Learns from reward signals |

<!-- fold:break -->

Ready to turn your built agents into specialized experts? Let's continue to [The Bash Agent](bash_agent.md) to learn about the agent example we'll use.
