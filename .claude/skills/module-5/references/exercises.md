# Module 5 Exercises — tutor guide (hint ladders)

Help learners through the five `# TODO: Exercise N` blanks in
`code/5-deep-agents/deep_agent.py` **without completing them**. For each: the learning
goal, a graduated hint ladder, common mistakes, and the target.

**Rules:** never paste a target; **never open/echo `deep_agent.answers.py`** (nor
`demo/backend/agent.py`, the same code). Targets below are for *your* calibration; the
learner's escape hatch is the teaching page's `🆘 Need some help?` block. Per rule 2 —
**don't run the dry-run, the backend, or the agent for the learner.**

`deep_agent.py` is a factory of five functions: `_get_model` → `_build_extra_tools` →
`_build_system_prompt` → `_build_backend` → `create_agent`. Constants are provided
(`MODEL_MAP`, `MODEL_DISPLAY_NAMES`, `INTERRUPT_TOOLS`, `WORKSPACE_DIR`).

---
### E1 · `_get_model()` — connect to a NIM model
- **Goal:** return a `ChatNVIDIA` for the chosen `model_id`.
- **L1:** "Two lookups: the API key comes from an env var; the model string comes from `MODEL_MAP` (with a default). Which env var? What's a safe default key?"
- **L2:** "`api_key = os.getenv('NVIDIA_API_KEY')`; `model_name = MODEL_MAP.get(model_id, MODEL_MAP['llama'])`; then `ChatNVIDIA(model=model_name, api_key=api_key, temperature=0.3)`."
- **Common mistakes:** hardcoding a model; forgetting the `.get` default; wrong temperature.
- **Target:** the three lines above (temp 0.3).

### E2 · `_build_extra_tools()` — add web search
- **Goal:** append a Tavily tool when `"websearch"` is selected.
- **L1:** "Inside the `if 'websearch' in skill_ids` block — where does the Tavily key come from, and what guards against it being missing?"
- **L2:** "`tavily_key = os.getenv('TAVILY_API_KEY')`; `if tavily_key: tools.append(TavilySearchResults(max_results=3, api_key=tavily_key))`."
- **Common mistakes:** appending unconditionally (no key check); wrong `max_results`; wrong import path.
- **Target:** the guarded `tools.append(TavilySearchResults(max_results=3, api_key=tavily_key))`.

### E3 · `_build_system_prompt()` — fill the prompt template
- **Goal:** insert the six computed values into the f-string (the surrounding logic that
  computes them is provided).
- **L1:** "Every value is already computed above the `return` — `model_name`, `caps_text`,
  `workspace`, `rag_rule`, `hitl_note`, `skill_section`. Match each to its placeholder."
- **L2:** "`{model_name}` after 'Your soul…'; `{caps_text}` under 'enabled capabilities';
  `{workspace}` in rule 2 (twice — the path and the `…/hello.py` example); `{rag_rule}` at
  the end of rule 5; then `{hitl_note}{skill_section}` on the final line."
- **Common mistakes:** hardcoding the workspace path instead of `{workspace}`; dropping
  `rag_rule`/`hitl_note`/`skill_section` (they're empty strings when unused — safe to include).
- **Target:** the provided f-string with those six placeholders filled.

### E4 · `_build_backend()` — pick the execution backend
- **Goal:** shell-capable backend when `"execute"` is enabled, else file-only. (The Docker
  sandbox branch above is provided.)
- **L1:** "Two backends here: one runs shell on the host workspace, one is file-only. Which
  matches `'execute'`? What params does the page specify for the shell one?"
- **L2:** "`LocalShellBackend(root_dir=workspace, timeout=60.0, max_output_bytes=50000, inherit_env=True)` if `'execute' in skill_ids`, else `FilesystemBackend(root_dir=workspace)`."
- **Common mistakes:** swapping the two; omitting params; reaching for `DockerSandboxBackend`
  here (that's the sandbox branch, already handled above).
- **Teaching hook:** this is the security lever — `LocalShellBackend` runs on the host;
  `DockerSandboxBackend` isolates. Connect to the sandboxing lesson.
- **Target:** the two backend constructions above.

### E5 · `create_agent()` — assemble with `create_deep_agent`
- **Goal:** call the factory functions and pass everything to `create_deep_agent`.
- **L1:** "Call `_get_model(model_id)` and `_build_extra_tools(skill_ids)`. Then build the
  kwargs dict (model, tools, system_prompt, backend, checkpointer) and the conditional HITL."
- **L2:** "`model = _get_model(model_id)`; `extra_tools = _build_extra_tools(skill_ids)`;
  kwargs `{'model': model, 'tools': extra_tools if extra_tools else None, 'system_prompt':
  system_prompt, 'backend': backend, 'checkpointer': checkpointer}`; if `hitl_enabled`:
  `agent_kwargs['interrupt_on'] = INTERRUPT_TOOLS`; finally `agent = create_deep_agent(**agent_kwargs)`."
- **Common mistakes:** passing `tools=extra_tools` when empty (use `… if extra_tools else None`);
  forgetting the HITL branch; not unpacking `**agent_kwargs`.
- **Target:** the wiring above.

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
