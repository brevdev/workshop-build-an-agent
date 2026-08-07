# Module 4 NVIDIA technologies — tutor reference

NVIDIA vs third-party for the customization module. This one matters: learners often assume
the *training* tools (unsloth, TRL) are NVIDIA — they aren't.

## NVIDIA
- **NeMo Data Designer** — NVIDIA's synthetic-data-generation tool (the `data-designer`
  package). Stage 1 of the pipeline; generates the LangGraph-CLI training data via a hosted
  model (`nvidia/nemotron-3-nano-30b-a3b` as the `command-generator`). Resource: build.nvidia.com.
- **NeMo Gym** — NVIDIA's environment/reward framework for RL. Here it's the **reward server**
  (`nemo_gym_resources/langgraph_cli/app.py`, a FastAPI `/verify` endpoint) that scores CLI
  outputs for RLVR. Stage 2.
- **NVIDIA Nemotron Nano** — two distinct ones:
  - **Training base:** `nvidia/NVIDIA-Nemotron-Nano-9B-v2` (a 9B **Mamba2** hybrid; loaded
    via unsloth `FastLanguageModel`, bf16, `load_in_4bit=False`). This is what GRPO fine-tunes.
  - **SDG generator:** `nvidia/nemotron-3-nano-30b-a3b` (hosted) writes the user phrasings.
- **NIM / NGC** — hosted SDG inference + `NVIDIA_API_KEY` (also pulls the base model).
- **`nemotron_unsloth_patch.py`** — NVIDIA-authored runtime patch so the Nemotron-H model
  works with unsloth's GRPO (hidden-states flag) and transformers 5.x (`cache_position`).

## Third-party (NOT NVIDIA — common confusion)
- **unsloth** — open-source library for fast/memory-efficient fine-tuning (`FastLanguageModel`,
  `get_peft_model`). It *trains NVIDIA models* but is not an NVIDIA product.
- **TRL (Transformers Reinforcement Learning)** — HuggingFace's RL library: `GRPOTrainer`,
  `GRPOConfig`. GRPO the *algorithm* originated with DeepSeek; TRL is the implementation here.
- **LoRA / PEFT** — parameter-efficient fine-tuning (HuggingFace `peft`); `r=16`.
- **vLLM** — fast inference engine for the generation/rollout step.
- **HuggingFace** — `transformers`, `datasets`, `HuggingFaceLLM` (run step), model hub.
- **Superpowers** — a third-party skills framework (github.com/obra/superpowers) bundled into
  the bash agent.

> Clarifications learners ask: *"Is unsloth/TRL NVIDIA?"* → no — they're open-source training
> tools; what's NVIDIA here is the *models* (Nemotron Nano), the *data tool* (NeMo Data
> Designer), and the *reward framework* (NeMo Gym). *"What's GRPO?"* → the RL algorithm
> (Group Relative Policy Optimization), implemented via TRL's `GRPOTrainer`.
