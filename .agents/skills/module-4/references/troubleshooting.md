# Module 4 Troubleshooting — tutor reference

**Triage first.** Environment/runtime (give direct fixes), exercise blank (guide — see
`exercises.md`), or training-behavior interpretation (teaching moment — see `concepts.md`)?
Runtime/GPU fixes below are fair to give directly. **Never run training or the reward
server for the learner** — diagnose, then let them act.

## GPU selection & memory
- **Recommended:** A100/H100 (80GB) for the GRPO step — base model is
  `NVIDIA-Nemotron-Nano-9B-v2` in **bf16** (`load_in_4bit=False`, because Mamba2 kernels
  are 4-bit-incompatible), trained with LoRA + GRPO rollouts → VRAM-hungry.
- **DGX Spark (GB10):** the notebook *runs*, but training is **much slower** (memory
  bandwidth). Set expectations (~1–1.5 hr is the A100/H100 figure; expect longer on GB10).
- **OOM during training** (in order): reduce `num_generations` 4→2; `per_device_train_batch_size`→1;
  raise `gradient_accumulation_steps` to compensate; ensure gradient checkpointing on;
  reduce `max_seq_length` if prompts allow. Memory ≈ batch × num_generations × seq_length.

## The `nemotron_unsloth_patch` (a real, required patch)
`02_grpo_training.ipynb` calls `patch_nemotron_for_unsloth_grpo(model)` after
`FastLanguageModel.from_pretrained(...)` and **before** `get_peft_model(...)`. It fixes
two concrete bugs in Nemotron-H's remote modeling code:
1. **forward ignores `UNSLOTH_RETURN_HIDDEN_STATES`** — unsloth's GRPO expects hidden
   states in the `logits` field; without the patch, GRPO gets wrong tensors.
2. **`prepare_inputs_for_generation` crashes on transformers 5.x** — `TypeError: 'NoneType'
   object is not subscriptable` on `cache_position[-1]` (5.x's `_prefill()` can pass
   `cache_position=None`).
If the learner sees either symptom, confirm the patch import + call are present and
ordered correctly (after load, before PEFT).

## The reward server (NeMo Gym)
- Must be **running before GRPO** training: `cd code/4-agent-customization/nemo_gym_resources/langgraph_cli && uvicorn app:app --host 0.0.0.0 --port 8000`.
- `reward_fn` POSTs to `/verify`; **connection refused / timeout** → server not running,
  wrong port, or wrong `verify_endpoint`. Sanity-check: `curl localhost:8000/...`.
- Reward is in **[-1, 1]** (flag-accuracy: `(correct − wrong − extra)/total`, exact = 1.0).
- Test the reward path manually before a full run: `reward_fn([{"content": '{"command": "new"}'}])` should return > 0 for a valid output.

## Training behavior (interpretation — guide, don't conclude)
- **Rewards not improving / stuck near 0:** reward-fn bug, LR too low (try 2–5×), data not
  diverse, too few steps (50 is a minimum; try 100–200), or model too small. Sparse signal
  → add partial credit (granular reward).
- **Reward hacking** (training reward high, real CLI accuracy poor): the reward rewards a
  shortcut (e.g. any valid JSON → empty `{}`). Fix: more validation components / held-out test.
- **Garbage output after training:** catastrophic forgetting (LR too high → lower 5–10×),
  overfit to reward (more/diverse data), or trained too long (use an earlier checkpoint).
- **Val reward ≪ train reward:** overfitting — more data, weight decay, fewer steps.
- **Inconsistent rewards** (same output, different score): make the reward deterministic.

## SDG / NeMo Data Designer
- Uses hosted `nvidia/nemotron-3-nano-30b-a3b` via **NeMo Data Designer** (`data-designer`).
  If SDG errors or is slow/unreachable, the learner can **use the provided dataset**
  (`data/langgraph_cli/train.jsonl` = 225, `val.jsonl` = 25) and move to GRPO.
- Bad/invalid synthetic outputs will confuse training (the reward scores them as
  failures) — spot-check coverage/balance/diversity/validity before training.

## Build / dependencies (if imports fail)
- This module relies on the heavy build from `postBuild.bash`: CUDA torch, **unsloth**,
  **mamba-ssm/causal-conv1d** (compiled for the GPU arch — sm_121 on GB10, sm_80/90 on
  x86_64), and a **trl import patch**. `ImportError`/missing-kernel errors usually mean the
  container build was incomplete — rebuild (`nvwb build`) and check the build log.
- `mamba_ssm`/`causal_conv1d` must be installed with `--no-build-isolation` (handled by the
  build). 4-bit load is intentionally disabled for this Mamba2 model.

## Running the customized agent (`03_run_agent.ipynb`)
- Loads from `outputs/grpo_langgraph_cli/merged_model/` — **`FileNotFoundError`/empty** →
  training didn't finish/save. They can re-run training or (if provided) use a supplied
  checkpoint.
- **Trained model emits odd/free-form text instead of JSON CLI calls** → the runtime
  system prompt must **match the training JSON format** (the R2 exercise). Mismatch = the
  model isn't prompted the way it was trained.
- Base agent run command: `cd code/4-agent-customization && python3.12 -m bash_agent.main_langgraph`.

## Keys
`secrets.env` (repo root) needs **`NVIDIA_API_KEY`** — for SDG (hosted Data Designer model)
and to pull the base model from NGC/HF. The GRPO training itself runs **locally on the GPU**.

## "Just run/train it for me" (policy reminder, not a bug)
Decline and explain: training is ~1–1.5 hr of GPU time and is the learner's to run; the
reward server and SDG are theirs to start too. Offer the provided dataset/checkpoint
shortcuts and the A100/H100-vs-GB10 guidance instead.
