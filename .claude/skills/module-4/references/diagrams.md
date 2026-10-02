# Module 4 Diagrams — tutor reference

Help a learner read the customization figures. Diagrams in `.devx/4-agent-customization/img/`.

## customization_pipeline (`customization_pipeline_dark.svg`, `intro_customization.md`)
- **Depicts:** the three-stage pipeline — `1. Generate Data (SDG / NeMo Data Designer) →
  2. Define Rewards (NeMo Gym) → 3. Train (GRPO)`.
- **Takeaway:** the spine of the whole module — data, then a way to score it, then RL. Each
  later page builds one stage.

## sdg_pipeline (`sdg_pipeline_dark.svg`, `sdg.md`)
- **Depicts:** `Schema + Seed Values → Generate User Request → Generate CLI JSON → Review + Split Pairs`.
- **Takeaway:** samplers guide coverage and a schema checks output shape. The generated labels still need review against the requests.

## grpo_training_loop (`grpo_training_loop_dark.svg`, `grpo_training.md`)
- **Depicts:** `Training Prompt → Model Generates 4+ Outputs → Reward Server Scores → GRPO
  Reinforces Best Ones`, looping "repeat for 50+ steps."
- **Takeaway:** GRPO = generate several candidates, score each (NeMo Gym `/verify`),
  reinforce the above-average ones. The "4+ outputs" is `num_generations`; the loop is
  `max_steps`. Exploration, not imitation.

## hitl_flow (`hitl_flow_dark.svg`, `bash_agent.md`)
- **Depicts:** `User Request → Agent Proposes Command → Human Reviews & Approves → Execute
  or Abort`, with a dashed "Reject + refine → new request."
- **Takeaway:** the agent **never executes directly** — it proposes and waits (`ExecOnConfirm`).
  Failing safely > succeeding quickly. (Previews Module 5/6 layered safety.)

## inference_pipeline (`inference_pipeline_dark.svg`, `run_customized.md`)
- **Depicts:** `User Input (NL) → Trained Model (HuggingFace) → JSON Tool-Call Output
  (structured) → HITL Confirm & Execute`.
- **Takeaway:** at run time the *trained* model emits the structured JSON CLI call (the thing
  training optimized) — which is why the runtime system prompt must match the training format.

## react_loop (`react_loop_dark.svg`, `bash_agent.md`)
- The Module 1 ReAct loop, applied to the bash agent (reason → propose tool → observe → repeat).

## Common confusions
- SDG samples seed values, then uses two LLM columns: request first, structured output second. Schema validity does not prove label accuracy.
- In grpo_training_loop the **Reward Server** is a *separate process* (NeMo Gym, `uvicorn`),
  not part of the model — it must be running before training.
