# Why Customize Agents?

<img src="_static/robots/study.png" alt="Understanding Customization" style="float:right;max-width:250px;margin:15px;" />

General-purpose models know a little about everything, but not enough about **your specific domain**. This module teaches you to customize a bash agent to understand the **LangGraph CLI**.

## MCP/Skills vs Training

When specializing an agent, you have two paths:

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **MCP / Skills** | Breadth (many simple tools) | Each tool competes for attention |
| **Training** | Depth (expert-level domain knowledge) | Upfront investment, permanent capability |

**Why not just add more tools?** Every tool you add increases the decision space. With 5 tools, selection is easy. With 50+, models start picking wrong tools, hallucinating parameters, or getting confused about which tool handles what. This is **diminishing returns**—more tools means worse per-tool accuracy.

**Training solves this differently.** Instead of giving the model a menu of 50 options at runtime, you bake the knowledge directly into the weights. The model *becomes* an expert rather than *consulting* expert tools. No selection overhead, no parameter confusion—just native understanding.

> 💡 **Rule of thumb**: Use MCP/Skills for breadth (calendar, email, search). Use training for depth (your CLI, your API, your domain).

## The Pattern

| Step | Tool |
|------|------|
| Generate training data | **NeMo Data Designer** |
| Define success metrics | **NeMo Gym** |
| Fine-tune with RL | **GRPO** |

## Timeline

| Part | Time |
|------|------|
| Base bash agent | 20 min |
| SDG *(or skip)* | 15 min |
| GRPO training | 60-70 min |
| Test agent | 15 min |

> 💡 **Short on time?** Pre-generated data included—skip straight to GRPO.

**Next:** [The Bash Agent](bash_agent.md)
