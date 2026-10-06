# Module 5 Exercises — tutor guide (hint ladders)

Help learners through the five `# TODO: Exercise N` blanks in
`code/5-deep-agents/deep_agent.py` **without completing them**. For each: the learning
goal, a graduated hint ladder, common mistakes, and the target.

**Rules:** **never open/echo `deep_agent.answers.py`**. **Targets are for checking the
learner's work and calibrating hints; never paste or dictate them, in whole or in part**
(equivalent code is fine). L2 hints are pointers (where to look, which variable holds the
value), never the finished line. The learner's escape hatch is the teaching page's
`🆘 Need some help?` block. Per rule 2 — **don't run the dry-run, the backend, or the agent
for the learner.**

`deep_agent.py` is a factory of five functions: `_get_model` → `_build_extra_tools` →
`_build_system_prompt` → `_build_backend` → `create_agent`. Constants are provided
(`MODEL_MAP`, `MODEL_DISPLAY_NAMES`, `INTERRUPT_TOOLS`, `WORKSPACE_DIR`).

---
### E1 · `_get_model()` — connect to a NIM model
- **Goal:** return a `ChatNVIDIA` for the chosen `model_id`.
- **L1:** "Two lookups: the API key comes from an env var; the model string comes from `MODEL_MAP` after validating the choice. Which env var and dictionary key?"
- **L2:** "The `# TODO: Exercise 1` comment above the function names both sources (a dict
  lookup and an environment read). The two variables you set are then exactly what the
  `ChatNVIDIA(...)` call's two blank keywords need. Its other arguments are provided — keep them."
- **Common mistakes:** hardcoding a model; silently substituting a different model; changing the provided temperature/limits.
- **Target:** `api_key = os.getenv("NVIDIA_API_KEY")`; `model_name = MODEL_MAP[model_id]`; `ChatNVIDIA(model=model_name, api_key=api_key, …)` with the provided `temperature=0.3`, `max_tokens=4096`, `timeout=90` and `model_kwargs` line unchanged.

### E2 · `_build_extra_tools()` — add web search
- **Goal:** append a Tavily tool when `"websearch"` is selected.
- **L1:** "Inside the `if 'websearch' in skill_ids` block — where does the Tavily key come from? (The `if tavily_key:` guard and the missing-key error are provided.)"
- **L2:** "The `# TODO: Exercise 2` comment names the environment variable and the result
  count. The class to instantiate is imported on the line above the blank; pass it the key
  variable and that count."
- **Common mistakes:** reading the wrong env var; wrong `max_results`; appending the class instead of an instance.
- **Target:** `tavily_key = os.getenv("TAVILY_API_KEY")`; inside the provided `if tavily_key:` guard, `tools.append(TavilySearchResults(max_results=3, api_key=tavily_key))`.

### E3 · `_build_system_prompt()` — fill the prompt template
- **Goal:** insert the six computed values into the f-string (the surrounding logic that
  computes them is provided).
- **L1:** "Every value is already computed above the `return` — `model_name`, `caps_text`,
  `workspace`, `rag_rule`, `hitl_note`, `skill_section`. Match each to its placeholder."
- **L2:** "Read the words around each `{...}`: 'Your soul (foundation model) is', 'Your
  enabled capabilities', 'Your workspace is'. Each names one computed variable. The other
  three slots take the optional extras (RAG rule, HITL note, skill text), which are empty
  strings when unused. The `# TODO: Exercise 3` comment describes each variable."
- **Common mistakes:** hardcoding the workspace path instead of `{workspace}`; dropping
  `rag_rule`/`hitl_note`/`skill_section` (they're empty strings when unused — safe to include).
- **Target:** the provided f-string with `{model_name}` (after "Your soul (foundation model) is:"), `{caps_text}` (under "Your enabled capabilities:"), `{workspace}` (rule 2), `{rag_rule}` (end of rule 5), and `{hitl_note}{skill_section}` (final line). An unfilled `{...}` doesn't raise — the prompt just contains the text `Ellipsis`.

### E4 · `_build_backend()` — pick the execution backend
- **Goal:** shell-capable backend when `"execute"` is enabled, else file-only. (The Docker
  sandbox branch above is provided.)
- **L1:** "Two backends here: one runs shell on the host workspace, one is file-only. Which
  matches `'execute'`? What params does the page specify for the shell one?"
- **L2:** "The `# TODO: Exercise 4` comment lists each backend's settings. Both classes are
  imported from `deepagents.backends` at the top of the file. Check their constructor
  keyword names (e.g. `help(LocalShellBackend)`) so each value lands on the right keyword.
  The root directory is the `workspace` variable set just above."
- **Common mistakes:** swapping the two; omitting params; reaching for `DockerSandboxBackend`
  here (that's the sandbox branch, already handled above).
- **Teaching hook:** this is the security lever — `LocalShellBackend` runs on the host;
  its file and shell tools share real absolute paths. File-only mode uses a virtual
  `/`; Docker uses `/workspace` and isolates execution. Connect to the sandboxing lesson.
- **Target:** execute branch `backend = LocalShellBackend(root_dir=workspace, timeout=60.0, max_output_bytes=50000, inherit_env=False, virtual_mode=False)`; else `backend = FilesystemBackend(root_dir=workspace, virtual_mode=True)`.

### E5 · `create_agent()` — assemble with `create_deep_agent`
- **Goal:** call the factory functions and pass everything to `create_deep_agent`.
- **L1:** "This function wires together the helpers you wrote. Which two haven't been called
  yet when the function starts? What does `create_deep_agent` need, and when should HITL
  interrupts be added?"
- **L2:** "Every dict value already exists by that point: the two helper results at the top
  of the function, the `system_prompt` and `backend` built in between, and the module-level
  `checkpointer`. For `interrupt_on`, combine the `INTERRUPT_TOOLS` constant with
  `enabled_tools()` from `demo/backend/capabilities.py`. Approval applies only to tools that
  are interruptible *and* enabled; the page's step 3 shows the dict shape. Then unpack the
  dict into the imported factory."
- **Common mistakes:** filling the provided `... if ... else None` with anything other than
  the extra-tools list in both slots; interrupting every `INTERRUPT_TOOLS` entry instead of
  only the enabled ones; forgetting to unpack `**agent_kwargs`.
- **Target:** `model = _get_model(model_id)`; `extra_tools = _build_extra_tools(skill_ids)`; `agent_kwargs` values `model`, `extra_tools if extra_tools else None`, `system_prompt`, `backend`, `checkpointer`; under `if hitl_enabled:` `agent_kwargs["interrupt_on"] = {name: True for name in INTERRUPT_TOOLS if name in enabled_tools(skill_ids)}`; `agent = create_deep_agent(**agent_kwargs)`.

---
## Running & testing (guide; don't run it for them)
- **Dry-run test:** `cd demo/backend && source .venv/bin/activate && python ../../code/5-deep-agents/deep_agent.py` → success prints "🎉 Your deep agent is working!".
- **Use it in the UI:** no copying — `demo/backend/agent.py` imports `create_agent()` from
  `code/5-deep-agents/deep_agent.py`. Restart the backend so it re-reads the file
  (`cd demo/backend && source .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8000`),
  and launch the **Deep Agents Client** tile. Check the backend's first lines: `Using YOUR
  implementation` means their code is live; `Using the REFERENCE implementation` lists the
  exercise functions that still contain a `...` blank — that's the diagnostic to point a
  stuck learner at. In the Client: pick a model (Nemotron), drag
  tools (Web Search / File I/O / Shell Execution), Build, then chat ("list files in the
  workspace", "write and run a hello world", "search latest GPU specs"). Watch the tool traces.
- **Sandbox demo:** toggle Sandbox Mode in the Client and re-ask "what files are in my
  workspace?" — sandboxed → empty `/workspace` (no host files); un-sandboxed → sees the
  seeded demo files. This is the security lesson; let the learner run and observe it.

## Escalation protocol
1. Ask what they've tried / what the dry-run or trace shows.
2. **L1** conceptual nudge (which function/value/backend).
3. **L2** specific pointer (the kwarg/param/shape).
4. **Last resort** — the teaching page's `🆘 Need some help?` block. Never paste it; never
   open `deep_agent.answers.py`; never run the agent for them.
