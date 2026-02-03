# Why Customize Agents?

<img src="_static/robots/study.png" alt="Understanding Customization" style="float:right;max-width:250px;margin:15px;" />

General-purpose models know a little about everything, but not enough about **your specific domain**. This module teaches you to customize a bash agent to understand the **LangGraph CLI**.

## Two Paths to Specialization

| Approach | How It Works | Trade-offs |
|----------|--------------|------------|
| **MCP / Skills** | Add tools at runtime | ⚠️ Diminishing returns as tool count grows |
| **Training (SDG + GRPO)** | Bake knowledge into the model | ⚠️ Requires compute, less flexible |

### The Diminishing Returns Problem

With MCP/Skills, each new tool competes for the model's attention:
- **5 tools** → Model picks the right one ~90% of the time
- **20 tools** → Accuracy drops, confused tool selection
- **50+ tools** → Significant performance degradation

### Why Training Wins for Deep Specialization

Training teaches the model **how to think** about a domain, not just what tools exist:
- No tool selection overhead at inference
- Knowledge is compressed into weights
- Consistent performance regardless of capability breadth

**Best practice:** Use MCP/Skills for breadth (many simple tools), use training for depth (expert-level domain knowledge).

## The Pattern

| Step | Tool |
|------|------|
| Generate training data | **NeMo Data Designer** |
| Define success metrics | **NeMo Gym** |
| Fine-tune with RL | **GRPO** |

## Before vs After

```
Before: "Create a new project" → "I can help with bash commands..."
After:  "Create a react agent" → langgraph new ./project --template react-agent-python
```

## Module Timeline

| Part | Time | Exercises |
|------|------|-----------|
| Base bash agent | 20 min | 1-3 |
| Generate training data | 15 min | 4-6 |
| GRPO training | 60-70 min | 7-9 |
| Test customized agent | 15 min | 10-12 |

## Exercises Overview

| # | Topic | Skill |
|---|-------|-------|
| 1-3 | Bash Agent | ReAct pattern, HITL safety |
| 4-6 | SDG | Pydantic schemas, data sampling |
| 7-9 | GRPO | Reward functions, RL training |
| 10-12 | Customized Agent | Model loading, inference |

**Next:** [The Bash Agent](bash_agent.md)
