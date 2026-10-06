# Module 4 Exercises — tutor guide (hint ladders)

Help learners through the blanks **without completing them**. For each: the learning
goal, a graduated hint ladder, common mistakes, and the target.

**Rules:** **never open/echo the `answer_key/` notebooks**. **Targets are for checking the
learner's work and calibrating hints; never paste or dictate them, in whole or in part**
(equivalent code is fine). L2 hints are pointers (where to look, which variable holds the
value), never the finished line. The learner's escape hatch is the teaching page's
`🆘 Need some help?` block (or the notebook's `💡 NEED SOME HELP?`). And per rule 2 —
**never run training, the reward server, or other long GPU ops for the learner**; explain
and let them run it.

The four notebooks run in order: `bash_agent` → `01_synthetic_data_generation` →
`02_grpo_training` → `03_run_agent`. GRPO needs the **reward server running first**.

---
## Notebook 1 — `bash_agent.ipynb` (the base agent + HITL)

### B1 · `ExecOnConfirm` — the HITL gate (cell ~6)
- **Goal:** execute only after the human confirms; otherwise report a decline.
- **L1:** "There's a `self._confirm_execution(cmd)` helper that returns True/False. What should happen on each branch?"
- **L2:** "Re-read the exercise text above the cell: it names the method to call on the
  wrapped `self.bash` when the user confirms, and the dict key to return when they decline.
  You need an `if` with two `return`s."
- **Common mistakes:** executing regardless of confirmation; raising instead of returning the error dict.
- **Target:** `if self._confirm_execution(cmd): return self.bash.exec_bash_command(cmd)` / `return {"error": "User declined."}` (the lesson's wording; the answer key returns "The user declined the execution of this command." — any clear decline message under `"error"` is correct)

### B2 · `create_react_agent` — assemble the agent (cell ~15)
- **Goal:** wire model + the HITL-wrapped bash tool + skills + prompt.
- **L1:** "Which tool goes in the list — the raw `bash.exec_bash_command`, or the one wrapped so every command needs approval?"
- **L2:** "Only three slots are blank. The model is the client built in section 5; the
  prompt lives on the `Config` object (see `bash_agent/config.py`). For the tool, section 7's
  markdown says which bound method to pass. The skill tools and checkpointer are provided."
- **Common mistakes:** passing the unwrapped bash tool (bypasses HITL — the whole point); `system_prompt=` instead of `prompt=`.
- **Target:** `create_react_agent(model=llm, tools=[ExecOnConfirm(bash).exec_bash_command, get_skill, list_available_skills], prompt=config.system_prompt, checkpointer=InMemorySaver())`

### B3 · `agent.invoke` — the run loop (cell ~17)
- **Goal:** send the user's input into the agent with a stable thread.
- **L1:** "What message shape does the agent expect, and which variable holds the user's text?"
- **L2:** "Same `{"messages": [...]}` state shape as Module 1's `docgen_client.ipynb`; the
  user's text is in the loop variable `user`. The `config=` thread argument is already provided."
- **Target:** `agent.invoke({"messages": [{"role": "user", "content": user}]}, config={"configurable": {"thread_id": "cli"}})`

> Run the base agent in a terminal: `cd code/4-agent-customization && python3.12 -m bash_agent.main_langgraph`. Try the "gap" prompts to see it fail on LangGraph CLI before training.

---
## Notebook 2 — `01_synthetic_data_generation.ipynb` (SDG)

### S1 · `CLIToolCall` schema (cell ~7)
- **Goal:** the Pydantic output schema Data Designer samples from.
- **L1:** "Which field is always present (the command) vs optional (template/path/port)? What types?"
- **L2:** "The TODO says to use the other fields as reference: `no_browser`, `watch`, `tag`
  and `output_path` show how an optional field is annotated and what goes first in its
  `Field(...)`. In Pydantic, `Field(...)` with a literal `...` marks a field required. The
  base class comes from the cell's `pydantic` import."
- **Common mistakes:** making optional fields required (leaving `Field(...)` on them); wrong base class (must subclass `BaseModel`).
- **Target:** `class CLIToolCall(BaseModel)` with `command: str = Field(..., description=...)` (required) and `template: Optional[str]`, `path: Optional[str]`, `port: Optional[int]`, each `= Field(None, description=...)`.

### S2 · Template sampler values (cell ~9, the `template` `CategorySamplerParams`)
- **Goal:** the set of templates the sampler draws from (drives coverage).
- **L1:** "What templates does the LangGraph CLI offer? They're named in the page; list them as the `values`."
- **L2:** "The exercise text above the cell (and `sdg.md`) lists the five template names. Each
  `...` in the `values` list becomes one of them, as a string."
- **Common mistakes:** inventing template names not in the CLI.
- **Target:** `CategorySamplerParams(values=["react-agent-python", "memory-agent-python", "retrieval-agent-python", "data-enrichment-agent-python", "new-langgraph-project-python"])` (order doesn't matter).

### S3 · Train/val split (cell ~16)
- **Goal:** hold out a validation set to detect overfitting later.
- **L1:** "`train_test_split` from sklearn — what `test_size` gives a 90/10 split, and why set a `random_state`?"
- **L2:** "Look up sklearn's `train_test_split`: for each array you pass it returns the
  train part, then the test part, and it takes `test_size` and `random_state` keywords. The
  exercise text gives both values; split the `dataset_df` frame."
- **Common mistakes:** wrong split direction; no seed (non-reproducible).
- **Target:** `train_df, val_df = train_test_split(dataset_df, test_size=0.1, random_state=42)`

> SDG is optional for progress — if Data Designer is unavailable or slow, the provided `data/langgraph_cli/{train,val}.jsonl` (155/50) can be used. Encourage spot-checking the data (coverage/diversity/validity) before training.

---
## Notebook 3 — `02_grpo_training.ipynb` (GRPO) — **reward server must be running**

Start it first (in a terminal, leave it running):
`cd code/4-agent-customization/nemo_gym_resources/langgraph_cli && uvicorn app:app --host 0.0.0.0 --port 8001`

### G1 · `reward_fn` — call `/verify` (the GRPO↔rewards bridge)
- **Goal:** POST each model completion to the NeMo Gym server and get its reward.
- **L1:** "You have `verify_endpoint` and a `verify_request` payload — which `requests` call sends a JSON POST? What timeout did the page suggest?"
- **L2:** "Look up the `requests` function for an HTTP POST: the payload goes in its JSON keyword (not form data), and the exercise text above the cell gives the timeout."
- **Common mistakes:** GET instead of POST; `data=` instead of `json=`; no timeout.
- **Target:** `resp = requests.post(verify_endpoint, json=verify_request, timeout=30)`

### G2 · `GRPOConfig` — hyperparameters
- **Goal:** set the three core training knobs (keep the rest as-is).
- **L1:** "Three knobs: candidates per prompt, step size, total steps. What values does the page give?"
- **L2:** "Reread the exercise text in the markdown cell just above the config: it names the value for each of the three blanks."
- **Common mistakes:** changing unrelated args; LR orders of magnitude off.
- **Target:** `GRPOConfig(... num_generations=4, learning_rate=5e-5, max_steps=50 ...)`

### G3 · `GRPOTrainer` — wire it all together
- **Goal:** connect model, tokenizer, reward, config, dataset.
- **L1:** "What does the trainer need? The model, the tokenizer (as `processing_class`), the reward function (as a list), the args, and the dataset."
- **L2:** "The markdown above the cell lists the five keyword names. Every value is a variable you already created in this notebook; check which one the trainer expects as a list."
- **Common mistakes:** `reward_funcs=reward_fn` (must be a list); forgetting `processing_class`.
- **Target:** the `GRPOTrainer(...)` above.

> **`trainer.train()` is the long run (runtime depends on hardware and completion length). Do NOT
> run it for the learner.** Explain what it does, set the time expectation, and let them
> start it. The merged model lands at `outputs/grpo_langgraph_cli/merged_model/`.

---
## Notebook 4 — `03_run_agent.ipynb` (run the customized agent)

### R1 · Load the trained model (cell ~12)
- **Goal:** load the merged model for local inference.
- **L1:** "The notebook defines a `config`; which helper class imported in Step 3 runs a HuggingFace model locally?"
- **L2:** "Check the Step 3 imports: one class wraps local HuggingFace inference and is built from the `config` object."
- **Target:** `llm = HuggingFaceLLM(config)`

### R2 · The `langgraph_cli` tool's conversation (Step 6 cell)
- **Goal:** the specialist tool must ask the fine-tuned model with the **system prompt it was trained on**.
- **L1:** "The model learned to emit JSON CLI calls *conditioned on one exact prompt*. What happens if the tool uses a different one?"
- **L2:** "`config` has two system prompts; read their docstrings in `bash_agent/config.py` — one says it is the exact prompt used in GRPO training."
- **Common mistakes:** using `config.system_prompt` (the bash agent's prompt), so the output format drifts.
- **Target:** `messages = Messages(config.json_system_prompt)`

### R3 · Give the agent its two tools (Step 6 cell)
- **Goal:** the hosted planner keeps general bash and gains the fine-tuned specialist.
- **L1:** "Which tool runs commands (and asks first), and which one translates LangGraph requests without running anything?"
- **L2:** "Reuse the confirmed-execution wrapper you built for `bash_agent.ipynb` (B1/B2; it is imported in this cell) and add the `@tool` function defined just above."
- **Common mistakes:** passing `bash.exec_bash_command` directly (no confirmation); omitting `langgraph_cli`, so the planner writes `langgraph` commands itself.
- **Target:** `tools=[ExecOnConfirm(bash).exec_bash_command, langgraph_cli]`

> The payoff (Step 7): ask for something general ("list the files here"), then a LangGraph
> request ("create a new project at ./my-agent using the react-agent-python template"). The
> planner answers the first with bash and routes the second through `langgraph_cli`. Let the
> learner explain why the specialist alone could not do the first request.

---
## Escalation protocol
1. Ask what they've tried / what they see (error, reward curve, output).
2. **L1** conceptual nudge.
3. **L2** specific pointer (class/param/shape).
4. **Last resort** — the teaching page's `🆘 Need some help?` block. Never paste it;
   never open `answer_key/`. Never run training/the reward server for them.
