# Module 4 Concepts — tutor reference

Answer conceptual questions accurately and in the workshop's voice. For the
authoritative narrative, read the teaching pages in `.devx/4-agent-customization/`.
Explaining concepts is teaching — do it freely.

## When to customize (`intro_customization.md`)
Three levers to improve an agent: **prompt engineering** (quick, limited), **tools/
skills** (more capability — Modules 1–2), and **training** (specialize the weights).
- **Path A — Skills/MCP (runtime knowledge):** best for breadth — many general
  capabilities, changing/large knowledge, latency-tolerant. Limit: every tool competes
  for attention; use evaluation to detect selection errors.
- **Path B — Training (baked-in knowledge):** best for depth — stable well-defined
  domains, precise structured output, latency-sensitive. Trade-off: upfront data +
  compute, and the need to re-evaluate when the domain changes.
- **Rule of thumb:** Skills/MCP for breadth, training for depth; many systems combine
  both. Train when measured failures justify it. Here we test structured LangGraph CLI output.

**SFT vs GRPO** (two ways to train):
| | SFT | GRPO |
|---|---|---|
| Signal | "copy this exact output" | "outputs like this score higher" |
| Needs | gold input→output pairs | a reward signal (can be noisy) |
| Exploration | none (imitation) | yes (tries variations) |
| Best for | abundant gold data, one right format | **verifiable correctness, structured output** |
Here GRPO is one way to optimize a code-scored CLI task; compare it with simpler prompting or SFT.

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
- **The gap to measure:** does the same local Nano-9B produce more correct CLI JSON after training? The hosted starter is a different model, so its behavior is not the training baseline.

## Synthetic data generation (`sdg.md`)
- **The cold-start problem:** a brand-new CLI has no real user logs. **SDG** breaks the
  cycle by generating realistic examples programmatically.
- **Schema and samplers:** sample seed values, generate a user request, then generate schema-constrained CLI JSON from that request. Schema validation checks structure; inspect the pairs for label errors. Random sampling does not guarantee every combination appears.
- **SDG model:** Data Designer's `command-generator` uses hosted
  `nvidia/nemotron-3.5-lightning-30b-a3b` to phrase the inputs.
- **Data quality (matters more than quantity):** coverage (every command/flag appears,
  edge cases), balance (no command > ~40% unless realistic), diversity (varied phrasing,
  not just slot values), validity (all outputs parse + pass schema). Aim ~100–300
  examples as a starting point, then measure held-out performance. Generated rows go
  under `data/langgraph_cli/generated/`; training defaults to the reviewed shipped
  `train.jsonl` / `val.jsonl` (155 / 50). Select reviewed generated data with `DATA_DIR`.

## Verifiable rewards + NeMo Gym (`grpo_training.md`)
- **RLVR (RL with Verifiable Rewards):** for structured outputs, score with **code, not
  an LLM judge** — objective, fast (ms), scalable. This reward compares a reference command and flags; it does not run the CLI or accept every equivalent command.
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
(`(reward − mean)/(std + epsilon)`; equal scores give zero advantage), ④ update weights to make above-average outputs more likely.
"Group relative" adapts to the model's current ability — even when all outputs are poor
it reinforces the relatively-better ones. Whether this improves held-out performance must be measured.
- **Training setup:** base `nvidia/NVIDIA-Nemotron-Nano-9B-v2` via **unsloth**
  `FastLanguageModel` (`max_seq_length=1024`, `load_in_4bit=False` — Mamba2 kernels are
  incompatible with 4-bit), patched by `nemotron_unsloth_patch.py`, then **LoRA**
  (`r=16`, `alpha=32`) via `get_peft_model`. Trainer: TRL `GRPOTrainer`/`GRPOConfig`.
- **Health metrics:** inspect reward, completion length, KL, gradients, and held-out exact match together. Zero reward variance gives no within-group learning signal; GRPO loss need not decrease steadily. High train reward alone is not evidence of generalization.
- **Resources:** training requires substantial free GPU memory; check available memory and CUDA/Mamba compatibility before starting. Output:
  `outputs/grpo_langgraph_cli/merged_model/`.

## Running the customized agent (`run_customized.md`)
Load the trained Nano-9B (`HuggingFaceLLM`) and run the agent with the **same JSON
system prompt used in training**, inspect `held_out_comparison.json` from the same-model before/after evaluation, then try new requests. Improvement is an experimental result, not a guarantee.

## Source map
- Concepts → `intro_customization.md`, `bash_agent.md`, `sdg.md`, `grpo_training.md`
- Code → the 4 notebooks; reward server `nemo_gym_resources/langgraph_cli/app.py`; patch `nemotron_unsloth_patch.py`; agent `bash_agent/`
