# Module 7 NVIDIA technologies — tutor reference

What each NVIDIA (and adjacent third-party) technology is, its role in *this* module, and
where to learn more. Module 7 is unusually full of **non-NVIDIA** names (seven harnesses) —
learners conflate them, so be precise. The module's thesis: NVIDIA's bet is *not* to own the
harness, but to make **every** harness better — engine (Nemotron), safety (NemoClaw), and
portable capability (Verified Skills).

## NVIDIA
- **Nemotron** (`nvidia/nemotron-3-super-120b-a12b`) — the **engine** under every harness in
  the lab: the minimal harness, Hermes, OpenClaw all call it. Resource: https://build.nvidia.com.
- **NIM / API Catalog** — hosted inference at `https://integrate.api.nvidia.com/v1`
  (OpenAI-compatible). What lets the whole module run with just an `NVIDIA_API_KEY`.
- **ChatNVIDIA** (`langchain_nvidia_ai_endpoints`) — NVIDIA's official LangChain integration;
  the client the lab uses to talk to Nemotron. (LangChain itself is third-party; this package is NVIDIA's.)
- **NVIDIA Verified Skills** — [`github.com/NVIDIA/skills`](https://github.com/NVIDIA/skills):
  official, signed skills teaching agents to use NVIDIA software optimally (cuOpt, **cuDF**,
  CUDA-Q, NeMo, Dynamo, Holoscan, Earth2Studio, PhysicsNeMo…), synced daily. The governance
  pipeline: review → **SkillSpector** security scan → evaluation → **skill card** → **OpenSSF
  Model Signing** (`skill.oms.sig`) → catalog → sync. Docs: https://docs.nvidia.com/skills;
  blog: developer.nvidia.com (NVIDIA Verified Agent Skills).
- **cuDF / RAPIDS / CUDA-X** — the GPU DataFrame library behind Exercise 4 (`cudf.pandas`, the
  100K-row gate). NVIDIA's accelerated-computing stack; this is what lights up `nvidia-smi`.
  Docs: https://docs.rapids.ai/api/cudf/stable/.
- **NemoClaw + the NemoClaw-for-Hermes blueprint** — the Module 6 safety stack; it powers the
  open harnesses (OpenClaw, Hermes). Blueprint: https://build.nvidia.com/nvidia/nemoclaw-for-hermes-agent.

## Third-party / open (clarify when asked — NOT NVIDIA)
- **pi** — the *minimal* open harness (Mario Zechner & Armin Ronacher); sub-1k prompt, four
  tools, lazy skills, live self-extension. Inspired Exercises 2 and 5. github.com/badlogic/pi-mono.
- **Hermes** — the *curated, self-improving* open harness from **NousResearch**; the one the lab
  drives. Has `NVIDIA/skills` as a built-in tap, but Hermes itself is not NVIDIA.
  hermes-agent.nousresearch.com.
- **OpenClaw** — the open, config-first autonomous-agent framework (Module 6's harness). NemoClaw
  *wraps* it; OpenClaw is not NVIDIA.
- **OpenCode** — the open "own every layer" harness.
- **Claude Code** (Anthropic) and **Codex** (OpenAI) — the two *subscription* harnesses;
  closed-source, frontier models. They consume the open skills format too (the optional Ex 4 track).
- **Cursor, Kiro** — other harnesses/editors that consume the open spec.
- **Agent Skills spec** — [agentskills.io](https://agentskills.io): the **open** spec behind
  skill portability. Community/open, not NVIDIA-owned — that's *why* one skill runs everywhere.
- **Skill marketplaces** — skills.sh, ClawHub, Hermes Hub, the Claude Code/Codex plugin
  ecosystems. NVIDIA skills syndicate *out* to these.
- **tiktoken** — OpenAI's tokenizer library (`cl100k_base`), used in Exercise 2 to *measure* the
  context tax. A measurement tool, not the model.
- **LangChain** (`langchain_core`: `HumanMessage`/`SystemMessage`/`ToolMessage`/`@tool`/
  `convert_to_openai_tool`) — the framework the minimal harness is built with.

> **Frequent confusions:**
> - *"Are skills an NVIDIA thing?"* The **spec is open** (agentskills.io); NVIDIA contributes
>   **verified** skills to it. Any harness can read any skill.
> - *"Is Hermes / pi / OpenClaw NVIDIA?"* No — they're independent open harnesses. NVIDIA's
>   contribution is the engine (Nemotron), the safety stack (NemoClaw), and verified skills that
>   work *with* them.
> - *"Does my GPU only work in NVIDIA's own harness?"* No — a verified skill drives your GPU in
>   *any* harness, including Claude Code and Codex (the GPU work runs locally).
