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

Fill in `_get_model()` to create a `ChatNVIDIA` instance using the model name from `MODEL_MAP` and the API key from the environment.

<details>
<summary>🆘 Need some help?</summary>

```python
def _get_model(model_id: str = "nemotron"):
    api_key = os.getenv("NVIDIA_API_KEY")
    model_name = MODEL_MAP.get(model_id, MODEL_MAP["nemotron"])
    return ChatNVIDIA(
        model=model_name,
        api_key=api_key,
        temperature=0.3,
    )
```

</details>

<!-- fold:break -->

### Exercise: Build the Tool Pipeline

Deep agents come with built-in tools (filesystem, planning, etc.), but we can add more. One easy and familiar addition we can make is **web search** via Tavily.

<button onclick="goToLineAndSelect('code/5-deep-agents/deep_agent.py', '# TODO: Exercise 2');"><i class="fas fa-code"></i> # TODO: Exercise 2</button>

Fill in `_build_extra_tools()` to add a `TavilySearchResults` tool when `"websearch"` is in the skill list.

<details>
<summary>🆘 Need some help?</summary>

```python
def _build_extra_tools(skill_ids: list[str]) -> list:
    tools = []
    if "websearch" in skill_ids:
        from langchain_community.tools.tavily_search import TavilySearchResults
        tavily_key = os.getenv("TAVILY_API_KEY")
        if tavily_key:
            tools.append(TavilySearchResults(max_results=3, api_key=tavily_key))
    return tools
```

</details>

<!-- fold:break -->

### Exercise: Write the System Prompt

<img src="_static/robots/spyglass.png" alt="System Prompt" style="float:right;max-width:250px;margin:15px;" />

The system prompt is critical — it tells the agent what it can do, what rules to follow, and how to behave. A well-crafted prompt prevents tool loops, ensures correct file paths, and keeps responses focused.

<button onclick="goToLineAndSelect('code/5-deep-agents/deep_agent.py', '# TODO: Exercise 3');"><i class="fas fa-code"></i> # TODO: Exercise 3</button>

Fill in `_build_system_prompt()` to:
1. List the agent's enabled capabilities (`{caps_text}`) in the workspace (`{workspace}`)
2. Set critical rules (use absolute paths, don't repeat tool calls, etc.)
3. Optionally include HITL notes (`{hitl_note}`) and skill content (`{skill_section}`)

Key rules your prompt should include:
- File tools require **absolute paths** under the workspace directory
- **Never** call the same tool with the same arguments twice
- Be concise and technically accurate

<details>
<summary>🆘 Need some help?</summary>

```python
return f"""You are an NVIDIA Deep Agent — a powerful AI assistant.

Your enabled capabilities:
{caps_text}

CRITICAL RULES:
1. Answer the user's question DIRECTLY. Do NOT use the 'task' tool — respond yourself.
2. File tools require ABSOLUTE paths. Your workspace is: {workspace}
   Always use paths like: {workspace}/hello.py
3. Use web search when the user asks for current information.
4. Be concise and technically accurate.
5. NEVER call the same tool with the same arguments twice.
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

Fill in `_build_backend()` to:
1. Use `LocalShellBackend` when shell execution is enabled
2. Fall back to `FilesystemBackend` otherwise
3. Set a `root_dir` so the agent operates in a specific workspace

<details>
<summary>🆘 Need some help?</summary>

```python
def _build_backend(skill_ids: list[str]):
    workspace = "/tmp/deepagent_workspace"
    os.makedirs(workspace, exist_ok=True)
    
    if "execute" in skill_ids:
        return LocalShellBackend(
            root_dir=workspace,
            timeout=60.0,
            max_output_bytes=50000,
            inherit_env=True,
        )
    else:
        return FilesystemBackend(root_dir=workspace)
```

</details>

<!-- fold:break -->

### Exercise: Wire It All Together

Now bring all the pieces together. The `create_agent()` function calls your other functions and passes everything to `create_deep_agent()`.

<button onclick="goToLineAndSelect('code/5-deep-agents/deep_agent.py', '# TODO: Exercise 5');"><i class="fas fa-code"></i> # TODO: Exercise 5</button>

Fill in `create_agent()` to:
1. Get the model, tools, prompt, and backend
2. Build the `agent_kwargs` dict
3. Optionally add `interrupt_on` for HITL approval
4. Call `create_deep_agent(**agent_kwargs)`

<details>
<summary>🆘 Need some help?</summary>

```python
def create_agent(skill_ids=None, model_id="nemotron", hitl_enabled=False):
    if skill_ids is None:
        skill_ids = []

    model = _get_model(model_id)
    extra_tools = _build_extra_tools(skill_ids)
    system_prompt = _build_system_prompt(skill_ids, model_id, hitl_enabled)
    backend = _build_backend(skill_ids)

    agent_kwargs = {
        "model": model,
        "tools": extra_tools if extra_tools else None,
        "system_prompt": system_prompt,
        "backend": backend,
        "checkpointer": MemorySaver(),
    }

    if hitl_enabled:
        agent_kwargs["interrupt_on"] = {
            "write_file": True, "edit_file": True, "execute": True,
        }

    return create_deep_agent(**agent_kwargs)
```

</details>

<!-- fold:break -->

### Exercise: Add a Custom Skill

<img src="_static/robots/magician.png" alt="Skills" style="float:right;max-width:250px;margin:15px;" />

Skills are markdown files that get injected into the agent's system prompt. They teach the agent domain-specific methodology without adding new tools.

**Create a new skill file** at `skills/my_skill.md` with instructions for the agent. For example, a "Code Review" skill:

```markdown
# Code Review Skill

When reviewing code:
1. Check for correctness and edge cases
2. Look for security vulnerabilities
3. Evaluate readability and naming
4. Suggest concrete improvements with examples
```

Then wire it into the agent by adding it to the `skill_files` mapping in <button onclick="goToLineAndSelect('code/5-deep-agents/deep_agent.py', 'skill_files = ');"><i class="fas fa-code"></i> skill_files</button>.

<!-- fold:break -->

## Test Your Agent

With all exercises complete, it's time to test! 

```bash
# Terminal 1: Ensure Backend is Running
cd demo/backend
source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```

Then, launch the <button onclick="launch('Deep Agents Client');"><i class="fa-solid fa-rocket"></i> Deep Agents Client</button> and try the following: 

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
