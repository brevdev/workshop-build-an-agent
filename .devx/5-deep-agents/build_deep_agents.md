# Build a Deep Agent

<img src="_static/robots/plumber.png" alt="Build Robot" style="float:right;max-width:300px;margin:25px;" />

Time to get hands-on. In this section, you'll build a deep agent step by step by filling in the core functions that power it. We'll work through the backend code and then test everything using the interactive Deep Agent Client from the previous section.

<button onclick="openOrCreateFileInJupyterLab('code/5-deep-agents/deep_agent.py');"><i class="fa-brands fa-python"></i> code/5-deep-agents/deep_agent.py</button> is the skeleton file you'll complete. This is a mirror of the Client code in `demo/backend/agent.py` but with key sections left as exercises.

<!-- fold:break -->

## Overview

Our deep agent factory has five core functions:

1. **`_get_model()`** — Connect to an NVIDIA NIM model
2. **`_build_extra_tools()`** — Add optional tools like web search
3. **`_build_system_prompt()`** — Craft the instructions that guide the agent
4. **`_build_backend()`** — Configure file system and shell execution
5. **`create_agent()`** — Wire everything together with `create_deep_agent()`

Let's build each one.

<!-- fold:break -->

## Exercises

### Exercise: Configure the Model

The first step is connecting to an NVIDIA NIM model. Deep agents need a model that supports **tool calling** — the ability to generate structured function calls.

<button onclick="goToLineAndSelect('code/5-deep-agents/deep_agent.py', '# TODO: Exercise 1');"><i class="fas fa-code"></i> # TODO: Exercise 1</button>

Fill in `_get_model()` to create a ChatNVIDIA instance.

Use `MODEL_MAP` to look up the `model_id`, and `os.getenv("NVIDIA_API_KEY")` for the `api_key`.
Set temperature to 0.3.

<details>
<summary>🆘 Need some help?</summary>

```python
...
api_key = os.getenv("NVIDIA_API_KEY")
model_name = MODEL_MAP.get(model_id, MODEL_MAP["llama"])
print(f"[Agent] Using model: {model_name} (id={model_id})")
return ChatNVIDIA(
    model=model_name,
    api_key=api_key,
    temperature=0.3,
)
...
```

</details>

<!-- fold:break -->

### Exercise: Build the Tool Pipeline

Deep agents come with built-in tools (filesystem, planning, etc.), but we can add more. One easy and familiar addition we can make is **web search** via Tavily.

<button onclick="goToLineAndSelect('code/5-deep-agents/deep_agent.py', '# TODO: Exercise 2');"><i class="fas fa-code"></i> # TODO: Exercise 2</button>

Fill in `_build_extra_tools()` to add a `TavilySearchResults` tool when `"websearch"` is in the skill list. Use ``os.getenv("TAVILY_API_KEY")`` for the ``api_key``, and ``max_results=3``.

<details>
<summary>🆘 Need some help?</summary>

```python
...
from langchain_community.tools.tavily_search import TavilySearchResults
tavily_key = os.getenv("TAVILY_API_KEY")
if tavily_key:
    tools.append(TavilySearchResults(max_results=3, api_key=tavily_key))
...
```

</details>

<!-- fold:break -->

### Exercise: Write the System Prompt

<img src="_static/robots/spyglass.png" alt="System Prompt" style="float:right;max-width:250px;margin:15px;" />

The system prompt is critical — it tells the agent what it can do, what rules to follow, and how to behave. A well-crafted prompt prevents tool loops, ensures correct file paths, and keeps responses focused.

<button onclick="goToLineAndSelect('code/5-deep-agents/deep_agent.py', '# TODO: Exercise 3');"><i class="fas fa-code"></i> # TODO: Exercise 3</button>

Fill in ``_build_system_prompt()`` to create the agent's instructions.

The prompt should tell the agent:
- `model_name`: the name of the model
- `caps_text`: all capabilities of the agent
- `workspace`: filesystem working directory of the agent
- `rag_rule`: instructions for rag if added
- `hitl_note`: instructions for HITL if added
- `skill_section`: instructions for skills if added

<details>
<summary>🆘 Need some help?</summary>

```python
...

return f"""You are an NVIDIA Deep Agent — a powerful AI assistant built for GTC 2026.
Your soul (foundation model) is: {model_name}

Your enabled capabilities:
{caps_text}

CRITICAL RULES:
1. Answer the user's question DIRECTLY. Do NOT use the 'task' tool — respond yourself.
2. File tools require ABSOLUTE paths. Your workspace is: {workspace}
   Always use paths like: {workspace}/hello.py
3. Use web search when the user asks for current information.
4. Be concise and technically accurate.
5. You are running on NVIDIA infrastructure.{rag_rule}
{hitl_note}{skill_section}"""
```

</details>

<!-- fold:break -->

### Exercise: Configure the Backend

The **backend** determines where file operations and shell commands execute. Deep agents support different backends:

- `FilesystemBackend` — File-only operations (read, write, edit, ls, glob, grep)
- `LocalShellBackend` — File operations **plus** shell execution (extends FilesystemBackend)
- `DockerSandboxBackend` — Everything runs inside an isolated Docker container

<button onclick="goToLineAndSelect('code/5-deep-agents/deep_agent.py', '# TODO: Exercise 4');"><i class="fas fa-code"></i> # TODO: Exercise 4</button>

Fill in ``_build_backend()`` to return the right backend:

* If "execute" is in ``skill_ids`` → ``LocalShellBackend`` (with root_dir as workspace, 60.0 timeout, 50000 max_output_bytes, inherit_env set to True)
* Otherwise → ``FilesystemBackend`` (with root_dir as workspace)

<details>
<summary>🆘 Need some help?</summary>

```python
...
if "execute" in skill_ids:
    backend = LocalShellBackend(
        root_dir=workspace,
        timeout=60.0,
        max_output_bytes=50000,
        inherit_env=True,
    )
    print("[Agent] Shell execution enabled via LocalShellBackend")
else:
    backend = FilesystemBackend(root_dir=workspace)
    print("[Agent] Using FilesystemBackend")
...
```

</details>

<!-- fold:break -->

### Exercise: Wire It All Together

Now bring all the pieces together. The `create_agent()` function calls your other functions and passes everything to `create_deep_agent()`.

<button onclick="goToLineAndSelect('code/5-deep-agents/deep_agent.py', '# TODO: Exercise 5');"><i class="fas fa-code"></i> # TODO: Exercise 5</button>

Fill in ``create_agent()`` to:

1. Call ``_get_model()`` with model_id, ``_build_extra_tools()`` with skill_ids
2. Build the ``agent_kwargs`` dict with model, extra_tools (if it exists), system_prompt, backend, checkpointer
3. If ``hitl_enabled``, add interrupt_on=INTERRUPT_TOOLS
4. Call ``create_deep_agent`` on **agent_kwargs and return the result

<details>
<summary>🆘 Need some help?</summary>

```python
...
model = _get_model(model_id)
extra_tools = _build_extra_tools(skill_ids)
any_sandboxed = any(sandbox_map.get(sid, False) for sid in skill_ids)
system_prompt = _build_system_prompt(skill_ids, model_id, hitl_enabled, any_sandboxed)
skill_sources = _get_skill_sources()

backend, sandbox = _build_backend(skill_ids, sandbox_map)

agent_kwargs: dict = {
    "model": model,
    "tools": extra_tools if extra_tools else None,
    "system_prompt": system_prompt,
    "backend": backend,
    "checkpointer": checkpointer,
}

if hitl_enabled:
    agent_kwargs["interrupt_on"] = INTERRUPT_TOOLS

if skill_sources:
    agent_kwargs["skills"] = skill_sources

agent = create_deep_agent(**agent_kwargs)
...
```

</details>

<!-- fold:break -->

## Test Your Agent

With all exercises complete, it's time to test. Let's see if your agent is working!

Open a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> and execute the built-in dry run. 

```bash
cd demo/backend
source .venv/bin/activate
python ../../code/5-deep-agents/deep_agent.py
```

If successful, you should see a "Your deep agent is working!" message at the end of the test. 

<!-- fold:break -->

## Run Your Agent

> If you would like to use this agent you just created in the main Deep Agent Client, copy the entire file contents you just wrote from ``code/5-deep-agents/deep_agent.py`` into ``demo/backend/agent.py``. 

Re-launch the backend with this agent implementation: 

```bash
# Terminal 1: Ensure Backend is Running
cd demo/backend
source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```

<!-- fold:break -->

With the backend running, launch the <button onclick="launch('Deep Agents Client');"><i class="fa-solid fa-rocket"></i> Deep Agents Client</button> and try the following: 

1. **Pick Nemotron** as your model
2. **Drag tools** onto the agent — Web Search, File I/O, Shell Execution
3. **Click Build** — watch the build animation
4. **Chat** — try these prompts:
   - *"List all files in the workspace"*
   - *"Write a hello world Python script and run it"*
   - *"Search for the latest NVIDIA GPU specs"*

Watch the tool traces in real-time — you'll see each tool call, its input, output, and duration.

<!-- fold:break -->

## What Just Happened?

When you clicked Build, the frontend sent your deep agent configuration to the backend:

```
POST /api/agent
{
  "model_id": "nemotron",
  "skill_ids": ["websearch", "fileio", "execute"],
  "hitl_enabled": true,
  "sandbox_map": {}
}
```

The backend ran your `create_agent()` function, which:
1. Connected to NVIDIA Nemotron via NIM
2. Added Tavily web search as an extra tool
3. Built a system prompt with all capabilities listed
4. Configured a `LocalShellBackend` for file/shell operations
5. Called `create_deep_agent()` to assemble the full middleware pipeline

Every chat message streams through `astream_events`, giving you real-time token streaming and tool execution traces.

> Your agent is alive! Now let's talk about keeping it safe. Head to [Sandboxing and Security](sandboxing_security) →
