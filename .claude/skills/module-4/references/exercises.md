# Module 4 Exercises — tutor guide (hint ladders)

Help learners through the blanks **without completing them**. For each: the learning
goal, a graduated hint ladder, common mistakes, and the target.

**Rules:** never paste a target; **never open/echo the `answer_key/` notebooks**. Targets
below are for *your* calibration; the learner's escape hatch is the teaching page's
`🆘 Need some help?` block. And per rule 2 — **never run training, the reward server, or
other long GPU ops for the learner**; explain and let them run it.

The four notebooks run in order: `bash_agent` → `01_synthetic_data_generation` →
`02_grpo_training` → `03_run_agent`. GRPO needs the **reward server running first**.

---
## Notebook 1 — `bash_agent.ipynb` (the base agent + HITL)

### B1 · `ExecOnConfirm` — the HITL gate (cell ~6)
- **Goal:** execute only after the human confirms; otherwise report a decline.
- **L1:** "There's a `self._confirm_execution(cmd)` helper that returns True/False. What should happen on each branch?"
- **L2:** "If confirmed → return `self.bash.exec_bash_command(cmd)`; else return a dict `{'error': 'User declined.'}` so the agent knows it was rejected."
- **Common mistakes:** executing regardless of confirmation; raising instead of returning the error dict.
- **Target:** `if self._confirm_execution(cmd): return self.bash.exec_bash_command(cmd)` / `return {"error": "User declined."}`

### B2 · `create_react_agent` — assemble the agent (cell ~15)
- **Goal:** wire model + the HITL-wrapped bash tool + skills + prompt.
- **L1:** "Which tool goes in the list — the raw `bash.exec_bash_command`, or the one wrapped so every command needs approval?"
- **L2:** "`model=llm`, `tools=[ExecOnConfirm(bash).exec_bash_command, get_skill, list_available_skills]`, `prompt=config.system_prompt` (keep `checkpointer=InMemorySaver()`)."
- **Common mistakes:** passing the unwrapped bash tool (bypasses HITL — the whole point); `system_prompt=` instead of `prompt=`.
- **Target:** `create_react_agent(model=llm, tools=[ExecOnConfirm(bash).exec_bash_command, get_skill, list_available_skills], prompt=config.system_prompt, checkpointer=InMemorySaver())`

### B3 · `agent.invoke` — the run loop (cell ~17)
- **Goal:** send the user's input into the agent with a stable thread.
- **L1:** "What message shape does the agent expect, and which variable holds the user's text?"
- **L2:** "`{'messages': [{'role':'user','content': user}]}`, plus a `config={'configurable': {'thread_id': 'cli'}}` so it's one ongoing conversation."
- **Target:** `agent.invoke({"messages": [{"role": "user", "content": user}]}, config={"configurable": {"thread_id": "cli"}})`

> Run the base agent in a terminal: `cd code/4-agent-customization && python3.12 -m bash_agent.main_langgraph`. Try the "gap" prompts to see it fail on LangGraph CLI before training.

---
## Notebook 2 — `01_synthetic_data_generation.ipynb` (SDG)

### S1 · `CLIToolCall` schema (cell ~7)
- **Goal:** the Pydantic output schema Data Designer samples from.
- **L1:** "Which field is always present (the command) vs optional (template/path/port)? What types?"
- **L2:** "`command: str` (required); `template: Optional[str]`, `path: Optional[str]`, `port: Optional[int]` all defaulting to `None`, each with a `Field(..., description=...)`."
- **Common mistakes:** making optional fields required; wrong base class (must subclass `BaseModel`).
- **Target:** a `BaseModel` with `command` (str) + `template`/`path` (Optional[str]) + `port` (Optional[int]), optionals default `None`.

### S2 · Template sampler values (cell ~ the `CategorySamplerParams`)
- **Goal:** the set of templates the sampler draws from (drives coverage).
- **L1:** "What templates does the LangGraph CLI offer? They're named in the page; list them as the `values`."
- **L2:** "`values=['react-agent-python','memory-agent-python','retrieval-agent-python','data-enrichment-agent-python','new-langgraph-project-python']`."
- **Common mistakes:** inventing template names not in the CLI.
- **Target:** the five `*-python` template names in `CategorySamplerParams(values=[...])`.

### S3 · Train/val split (cell ~16)
- **Goal:** hold out a validation set to detect overfitting later.
- **L1:** "`train_test_split` from sklearn — what `test_size` gives a 90/10 split, and why set a `random_state`?"
- **L2:** "`train_test_split(dataset_df, test_size=0.1, random_state=42)`."
- **Common mistakes:** wrong split direction; no seed (non-reproducible).
- **Target:** `train_df, val_df = train_test_split(dataset_df, test_size=0.1, random_state=42)`

> SDG is optional for progress — if Data Designer is unavailable or slow, the provided `data/langgraph_cli/{train,val}.jsonl` (225/25) can be used. Encourage spot-checking the data (coverage/diversity/validity) before training.

---
## Notebook 3 — `02_grpo_training.ipynb` (GRPO) — **reward server must be running**

Start it first (in a terminal, leave it running):
`cd code/4-agent-customization/nemo_gym_resources/langgraph_cli && uvicorn app:app --host 0.0.0.0 --port 8000`

### G1 · `reward_fn` — call `/verify` (the GRPO↔rewards bridge)
- **Goal:** POST each model completion to the NeMo Gym server and get its reward.
- **L1:** "You have `verify_endpoint` and a `verify_request` payload — which `requests` call sends a JSON POST? What timeout did the page suggest?"
- **L2:** "`requests.post(verify_endpoint, json=verify_request, timeout=30)`."
- **Common mistakes:** GET instead of POST; `data=` instead of `json=`; no timeout.
- **Target:** `resp = requests.post(verify_endpoint, json=verify_request, timeout=30)`

### G2 · `GRPOConfig` — hyperparameters
- **Goal:** set the three core training knobs (keep the rest as-is).
- **L1:** "Three knobs: candidates per prompt, step size, total steps. What values does the page give?"
- **L2:** "`num_generations=4`, `learning_rate=1e-5`, `max_steps=50`."
- **Common mistakes:** changing unrelated args; LR orders of magnitude off.
- **Target:** `GRPOConfig(... num_generations=4, learning_rate=1e-5, max_steps=50 ...)`

### G3 · `GRPOTrainer` — wire it all together
- **Goal:** connect model, tokenizer, reward, config, dataset.
- **L1:** "What does the trainer need? The model, the tokenizer (as `processing_class`), the reward function (as a list), the args, and the dataset."
- **L2:** "`GRPOTrainer(model=model, processing_class=tokenizer, reward_funcs=[reward_fn], args=training_args, train_dataset=train_dataset)`."
- **Common mistakes:** `reward_funcs=reward_fn` (must be a list); forgetting `processing_class`.
- **Target:** the `GRPOTrainer(...)` above.

> **`trainer.train()` is the long run (~1–1.5 hr on A100/H100; slower on GB10). Do NOT
> run it for the learner.** Explain what it does, set the time expectation, and let them
> start it. The merged model lands at `outputs/grpo_langgraph_cli/merged_model/`.

---
## Notebook 4 — `03_run_agent.ipynb` (run the customized agent)

### R1 · Load the trained model (cell ~13)
- **Goal:** load the merged model for inference.
- **L1:** "The notebook defines a `config`; which helper class loads a HF model from it?"
- **L2:** "`llm = HuggingFaceLLM(config)`."
- **Target:** `llm = HuggingFaceLLM(config)`

### R2 · Initialize conversation (cell ~17)
- **Goal:** seed the conversation with the **JSON system prompt that matches training**.
- **L1:** "The model was trained to emit JSON CLI calls — the runtime system prompt must match that training format. What object holds the messages here?"
- **L2:** "Initialize `messages = Messages(...)` with the JSON system prompt used during training (see the cell's context / the training prompt)."
- **Common mistakes:** using a different/free-form system prompt than training (the model expects the JSON format).
- **Target:** a `Messages(...)` initialized with the training-matched JSON system prompt.

> The payoff: run the gap prompts ("create a new react project", "dev server on 8080",
> "build docker image v2") on base vs customized and see the trained model produce correct
> `langgraph` commands. Guide the comparison; let the learner draw the conclusion.

---
## Escalation protocol
1. Ask what they've tried / what they see (error, reward curve, output).
2. **L1** conceptual nudge.
3. **L2** specific pointer (class/param/shape).
4. **Last resort** — the teaching page's `🆘 Need some help?` block. Never paste it;
   never open `answer_key/`. Never run training/the reward server for them.
