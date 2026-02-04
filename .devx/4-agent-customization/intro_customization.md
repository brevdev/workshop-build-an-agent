# Why Customize Agents?

<img src="_static/robots/study.png" alt="Understanding Customization" style="float:right;max-width:250px;margin:15px;" />

## From Evaluation to Improvement

In Module 3, you learned to **measure** agent performance—faithfulness, relevance, tool usage. But what happens when the metrics reveal problems?

You have three options:
1. **Prompt engineering** — Tweak instructions (quick but limited)
2. **Add tools/skills** — Give the model more capabilities (Module 2 approach)
3. **Train the model** — Fundamentally improve its understanding (this module)

This module teaches option 3: how to **customize a model** so it natively understands your domain. We'll take a bash agent and train it to expertly handle the **LangGraph CLI**.

## Two Paths to Specialization

When your agent needs domain expertise, you have two architectural choices:

### Path A: Skills & MCP (Runtime Knowledge)

In Module 2, you added **Skills** (instructions the agent loads) and **MCP** (tools the agent calls). This works well for:

- General-purpose capabilities (web search, calendar, email)
- Procedures that change frequently
- Knowledge that's too large to train on

**The limitation**: Every skill and tool competes for the model's attention. With 5 tools, selection is easy. With 50+, models start picking wrong tools, hallucinating parameters, or forgetting which tool does what.

### Path B: Training (Baked-in Knowledge)

Training writes knowledge directly into the model's weights. The model doesn't *consult* an expert—it *becomes* one. This works well for:

- Stable, well-defined domains (your CLI, your API)
- Tasks requiring precise structured output
- High-frequency use cases where latency matters

**The trade-off**: Upfront investment in data and compute, but permanent capability with no runtime overhead.

| Approach | Best For | When to Use |
|----------|----------|-------------|
| **Skills/MCP** | Breadth, flexibility | Many simple tools, changing procedures |
| **Training** | Depth, precision | Your core domain, structured outputs |

> 💡 **Rule of thumb**: Use Skills/MCP for breadth. Use training for depth. Many production systems combine both.

## The Customization Pipeline

Training an agent requires three components working together:

### 1. Training Data (NeMo Data Designer)

You need examples of what the agent should do. For a CLI agent:
- **Input**: "Create a new react agent project"
- **Output**: `{"command": "new", "template": "react-agent-python", "path": "./myapp"}`

**The cold-start problem**: You don't have real user logs yet. **Synthetic Data Generation (SDG)** solves this by programmatically creating diverse, realistic examples from templates and variations.

### 2. Success Metrics (NeMo Gym)

How does the model know if its output is good? In Module 3, you used LLM-as-judge. For structured outputs like CLI commands, we can do better: **code-based verification**.

A reward server checks:
- Is the JSON valid?
- Is `command` a real CLI command?
- Are the parameters correct for that command?

This is **RLVR (Reinforcement Learning with Verifiable Rewards)**—objective, consistent, and scalable.

### 3. Training Algorithm (GRPO)

Traditional fine-tuning says "memorize this answer." **GRPO (Group Relative Policy Optimization)** says "try multiple answers and learn which ones score higher."

The model generates 4+ responses per prompt. The reward server scores each one. The model learns to produce higher-scoring outputs. This exploration-based learning often beats pure imitation.

| Step | Tool | What It Does |
|------|------|--------------|
| Generate data | **NeMo Data Designer** | Creates input/output training pairs |
| Define rewards | **NeMo Gym** | Verifies outputs with code |
| Train model | **GRPO** | Learns from reward signals |

## Timeline

| Part | Time |
|------|------|
| Base bash agent | 20 min |
| SDG *(or skip)* | 15 min |
| GRPO training | 60-70 min |
| Test agent | 15 min |

> 💡 **Short on time?** Pre-generated data included—skip straight to GRPO.

**Next:** [The Bash Agent](bash_agent.md)
