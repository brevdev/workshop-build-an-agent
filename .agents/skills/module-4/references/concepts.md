# Module 4 Concepts — tutor reference

Answer conceptual questions accurately and in the workshop's voice. For the
authoritative narrative, read the teaching pages in `.devx/4-agent-customization/`.
Explaining concepts is teaching — do it freely.

## When to customize (`intro_customization.md`)
Three levers to improve an agent: **prompt engineering** (quick, limited), **tools/
skills** (more capability — Modules 1–2), and **training** (specialize the weights).
- **Path A — Skills/MCP (runtime knowledge):** best for breadth — many general
  capabilities, changing/large knowledge, latency-tolerant. Limit: every tool competes
  for attention; 50+ tools and the model mis-selects.
- **Path B — Training (baked-in knowledge):** best for depth — stable well-defined
  domains, precise structured output, latency-sensitive. Trade-off: upfront data +
  compute, but permanent capability, no runtime overhead.
- **Rule of thumb:** Skills/MCP for breadth, training for depth; many systems combine
  both. **If prompts + tools get you ~90%, don't train.** Train when the model
  fundamentally lacks the domain — here it knows generic bash but not the LangGraph CLI.

**SFT vs GRPO** (two ways to train):
| | SFT | GRPO |
|---|---|---|
| Signal | "copy this exact output" | "outputs like this score higher" |
| Needs | gold input→output pairs | a reward signal (can be noisy) |
| Exploration | none (imitation) | yes (tries variations) |
| Best for | abundant gold data, one right format | **verifiable correctness, structured output** |
CLI commands are verifiable and have multiple valid phrasings → **GRPO**.

**The pipeline:** ① generate data (**NeMo Data Designer**) → ② define rewards
(**NeMo Gym**, code-based / RLVR) → ③ train (**GRPO**).

## The bash agent + HITL (`bash_agent.md`)
The agent being customized: a ReAct bash agent (LangGraph) that turns natural language
into shell commands. Chosen because shell commands are **observable/verifiable**, the
gap (knows bash, not the LangGraph CLI) is **measurable**, and it's real-world.
- **Human-in-the-loop (HITL):** the agent **never executes directly** — it proposes a
  command and waits for approval (`ExecOnConfirm` wraps the `Bash` tool). "Failing
  safely > succeeding quickly." Defense-in-depth beyond HITL: allowlists, input
  validation, sandboxing (Module 5), audit logging.
- **Superpowers skills:** bundled structured workflows (systematic-debugging, TDD,
  brainstorming, writing-plans, executing-plans) the agent loads on demand via
  `get_skill`/`list_available_skills` (in `skills/superpowers`).
- **The gap to close:** base model on "create a new react project" → hallucinates;
  should be `langgraph new ./myapp --template react-agent-python`. After training, it
  reliably produces correct LangGraph CLI commands.

## Synthetic data generation (`sdg.md`)
- **The cold-start problem:** a brand-new CLI has no real user logs. **SDG** breaks the
  cycle by generating realistic examples programmatically.
- **Schema-first (the key idea):** define a Pydantic **output** schema (`CLIToolCall`),
  *sample outputs from it* (valid by construction), then have an LLM write a matching
  natural-language input. This is why Data Designer beats "ask an LLM for 200 examples":
  LLM-first generation can invent commands/flags that don't exist; schema-first
  guarantees validity, and samplers guarantee coverage. (Quiz: outputs first → every
  example valid.)
- **SDG model:** Data Designer's `command-generator` uses hosted
  `nvidia/nemotron-3-nano-30b-a3b` to phrase the inputs.
- **Data quality (matters more than quantity):** coverage (every command/flag appears,
  edge cases), balance (no command > ~40% unless realistic), diversity (varied phrasing,
  not just slot values), validity (all outputs parse + pass schema). Aim ~100–300
  examples; diminishing returns past 500–1000. Output:
  `data/langgraph_cli/{train.jsonl, val.jsonl}` (225 / 25).

## Verifiable rewards + NeMo Gym (`grpo_training.md`)
- **RLVR (RL with Verifiable Rewards):** for structured outputs, score with **code, not
  an LLM judge** — objective, fast (ms), scalable. CLI commands are right or wrong.
- **The reward server (NeMo Gym):** `nemo_gym_resources/langgraph_cli/app.py`, a FastAPI
  service exposing `/verify`; given a predicted vs reference CLI JSON it returns a
  **reward in [-1, 1]**. It is **gate-then-grade**, NOT a weighted sum: invalid JSON → −1;
  wrong command → −1; otherwise `(correct − wrong − extra) / total_flags` (clipped to
  [-1, 1]), exact match = 1.0. (There are no JSON/command/flag weights — do NOT invent
  0.2/0.3/0.5 composite weights; `grpo_training.md` explains *why gates instead of a
  weighted sum*.)
- **Reward-engineering principles:** **verifiable** (code), **granular on flags** (partial
  credit for getting *some* flags right) but the **JSON and command are hard gates** — a
  wrong command scores −1, not partial credit, precisely to avoid **reward hacking**;
  **aligned** (reward what you want — e.g. rewarding *any* valid JSON would let an empty
  `{}` score perfectly). Always test the reward on edge cases first.

## GRPO (`grpo_training.md`)
**Group Relative Policy Optimization** — for each prompt: ① generate several candidates
(here `num_generations=4`), ② score each with the reward server, ③ compute each
candidate's **advantage** = how far above/below the *group mean* it is
(`(reward − mean)/std`), ④ update weights to make above-average outputs more likely.
"Group relative" adapts to the model's current ability — even when all outputs are poor
it reinforces the relatively-better ones. This exploration often beats pure imitation.
- **Training setup:** base `nvidia/NVIDIA-Nemotron-Nano-9B-v2` via **unsloth**
  `FastLanguageModel` (`max_seq_length=1024`, `load_in_4bit=False` — Mamba2 kernels are
  incompatible with 4-bit), patched by `nemotron_unsloth_patch.py`, then **LoRA**
  (`r=16`, `alpha=32`) via `get_peft_model`. Trainer: TRL `GRPOTrainer`/`GRPOConfig`.
- **Health metrics:** mean reward ↑, reward std ↓, loss ↓ then stable, grad norm stable
  (<10). Red flags: reward stuck near 0 (sparse → add partial credit), high train reward
  but poor real perf (reward hacking → more validation), wild oscillation (LR too high).
- **Cost:** ~1–1.5 hr on A100/H100; GB10 works but slow. Output:
  `outputs/grpo_langgraph_cli/merged_model/`.

## Running the customized agent (`run_customized.md`)
Load the trained Nano-9B (`HuggingFaceLLM`) and run the agent with the **same JSON
system prompt used in training**, then compare base vs customized on the gap prompts
(new project / dev server / docker build) — the trained model now produces correct
LangGraph CLI commands.

## Source map
- Concepts → `intro_customization.md`, `bash_agent.md`, `sdg.md`, `grpo_training.md`
- Code → the 4 notebooks; reward server `nemo_gym_resources/langgraph_cli/app.py`; patch `nemotron_unsloth_patch.py`; agent `bash_agent/`
