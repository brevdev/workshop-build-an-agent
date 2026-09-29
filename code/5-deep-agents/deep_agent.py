"""
Deep Agent Factory — Module 5 Exercise File

Complete the TODO exercises below to build a deep agent with explicit tool permissions.
Each exercise corresponds to a section in the Build a Deep Agent lesson.

This file IS the factory the Deep Agents Client runs — demo/backend/agent.py
imports create_agent() from here, so there is nothing to copy. Until every blank
is filled it falls back to deep_agent.answers.py, and says so on startup.

Dry-run your implementation:
    cd demo/backend && source .venv/bin/activate
    python ../../code/5-deep-agents/deep_agent.py

Run it in the UI (restart the backend so it re-reads this file):
    Click "Deep Agents Client" from the JupyterLab Launcher                                          # Frontend
    cd demo/backend && source .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8000    # Backend
"""

import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

# ── Paths ────────────────────────────────────────────────────────────────────
# demo/backend/agent.py imports create_agent() from this file, so it must resolve
# its dependencies the same way however it's started — backend server, dry run,
# or any working directory.

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, os.pardir, os.pardir))
DEMO_BACKEND_DIR = os.path.join(REPO_ROOT, "demo", "backend")

# docker_sandbox.py and rag.py live with the demo backend.
if os.path.isdir(DEMO_BACKEND_DIR) and DEMO_BACKEND_DIR not in sys.path:
    sys.path.insert(0, DEMO_BACKEND_DIR)

sys.path.insert(0, os.path.join(REPO_ROOT, "code"))
from workshop_support import get_model, load_secrets
load_secrets(REPO_ROOT)

from capabilities import CapabilityMiddleware, enabled_tools, restrict_backend

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, LocalShellBackend, CompositeBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain_nvidia_ai_endpoints import ChatNVIDIA


# ── Configuration ─────────────────────────────────────────────────────────────

# Workspace directories
WORKSPACE_DIR = os.environ.get("DEEPAGENT_WORKSPACE", "/tmp/deepagent_workspace")            # Local (has sensitive files for demo)
SANDBOX_WORKSPACE_DIR = "/workspace"                  # Path INSIDE Docker container
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# Skills directory — the skill markdown ships with the demo backend, so point at
# it explicitly rather than at a folder next to this file (which would be empty).
SKILLS_DIR = os.path.join(DEMO_BACKEND_DIR, "skills")

# Shared checkpointer for all sessions (in-memory, resets on server restart)
checkpointer = MemorySaver()

# UI choices name the actual centrally configured model.
MODEL_MAP = {"nemotron": get_model("chat"), "nemotron_fast": get_model("fast_chat")}
MODEL_DISPLAY_NAMES = {"nemotron": "Nemotron Super", "nemotron_fast": "Nemotron Lightning"}

# Tools that require human approval before executing
INTERRUPT_TOOLS = {
    "write_file": True,
    "edit_file": True,
    "execute": True,
}


# ── Exercise 1: Configure the Model ──────────────────────────────────────────

# TODO: Exercise 1
# Fill in _get_model() to create a ChatNVIDIA instance.
# Use MODEL_MAP to look up the model_id, and os.getenv("NVIDIA_API_KEY") for the api_key.
# Set temperature to 0.3; keep the provided response and timeout limits.

def _get_model(model_id: str = "nemotron"):
    """Return an NVIDIA NIM chat model for the given model ID."""
    if model_id not in MODEL_MAP:
        raise ValueError(f"Unsupported model choice: {model_id}")
    api_key = ...
    model_name = ...
    print(f"[Agent] Using model: {model_name} (id={model_id})")
    return ChatNVIDIA(
        model=...,
        api_key=...,
        temperature=0.3,
        max_tokens=4096,
        timeout=90,
        model_kwargs={"chat_template_kwargs": {"enable_thinking": False}} if model_id == "nemotron_fast" else {},
    )


# ── Exercise 2: Build the Tool Pipeline ──────────────────────────────────────

# TODO: Exercise 2
# Fill in _build_extra_tools() to add a TavilySearchResults tool
# when "websearch" is in the skill_ids list.
# Use os.getenv("TAVILY_API_KEY") for the api_key, and max_results=3.

def _build_extra_tools(skill_ids: list[str]) -> list:
    """Build additional tools based on user-selected skills."""
    tools = []

    if "websearch" in skill_ids:
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
            tavily_key = ...
            if tavily_key:
                tools.append(...)
                print("[Agent] Added Tavily web search tool")
        except ImportError as exc:
            raise RuntimeError("Install the backend requirements to use Web Search.") from exc
        if not tavily_key:
            raise ValueError("Web Search requires TAVILY_API_KEY in secrets.env.")

    if "rag" in skill_ids:
        try:
            from rag import get_retriever_tool
            tool = get_retriever_tool()
            if tool is None:
                raise RuntimeError("The IT knowledge base is missing.")
            tools.append(tool)
            print("[Agent] Added IT knowledge base RAG tool")
        except Exception as exc:
            raise RuntimeError("Could not load the selected RAG tool. Check the knowledge base, model setup and backend dependencies.") from exc

    return tools

# ── Skill Loading (provided) ─────────────────────────────────────────────────

# Map skill IDs to markdown files
skill_files = {
    "superpowers": "superpowers.md",
    "cudf": "cudf.md",
    "code_review": "code_review.md",
    "cuopt": "cuopt.md",
}

def _load_skill_content(skill_ids: list[str]) -> str:
    """Load skill markdown files and return their content."""
    content_parts = []
    for sid in skill_ids:
        filename = skill_files.get(sid)
        if filename:
            filepath = os.path.join(SKILLS_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    content_parts.append(f.read())
    return "\n\n---\n\n".join(content_parts)

# ── Exercise 3: Write the System Prompt ──────────────────────────────────────

# TODO: Exercise 3
# Fill in _build_system_prompt() to create the agent's instructions.
# The prompt should tell the agent:
#   - model_name: the name of the model
#   - caps_text: all capabilities of the agent
#   - workspace: filesystem working directory of the agent
#   - rag_rule: instructions for rag if added
#   - hitl_note: instructions for HITL if added
#   - skill_section: instructions for skills if added

def _build_system_prompt(skill_ids: list[str], model_id: str, hitl_enabled: bool, sandbox_enabled: bool = False) -> str:
    """Create a system prompt that includes the selected capabilities and skills."""
    model_name = MODEL_DISPLAY_NAMES.get(model_id, "AI Model")
    workspace = SANDBOX_WORKSPACE_DIR if sandbox_enabled else "/"

    enabled = []
    if "websearch" in skill_ids:
        enabled.append("- Web Search (tavily_search_results_json): search the internet")
    if "fileio" in skill_ids:
        enabled.append("- File I/O (read_file, write_file, edit_file, ls, glob, grep): manage files")
    if "execute" in skill_ids:
        enabled.append("- Shell Execution (execute): run shell commands, Python scripts, and system tools")
    if "superpowers" in skill_ids:
        enabled.append("- Superpowers: agentic software development methodology (TDD, planning, debugging)")
    if "rag" in skill_ids:
        enabled.append("- IT Knowledge Base (it_knowledge_base): search internal IT policies and procedures")

    builtin = ["- Planning (write_todos): organize tasks",
               "- Delegation (task): ask a subagent to handle a focused subtask with the same permissions"]
    all_capabilities = enabled + builtin if enabled else builtin
    caps_text = "\n".join(all_capabilities)

    rag_rule = ""
    if "rag" in skill_ids:
        rag_rule = "\n6. When the user asks about IT policies, procedures, passwords, virtual desktops, VPN, software installation, hardware, or any internal company IT questions, ALWAYS use the it_knowledge_base tool to search the knowledge base. Do NOT use file tools (ls, grep, etc.) for IT-related questions."

    hitl_note = ""
    if hitl_enabled:
        hitl_note = """
NOTE: Some tools (write_file, edit_file, execute) require human approval.
The user will be asked to approve or reject your tool calls before they execute.
Continue normally after approval — do not ask the user to approve manually."""

    # Load skill content if any skills are selected
    skill_content = _load_skill_content(skill_ids)
    skill_section = f"\n\n---\n\n{skill_content}" if skill_content else ""

    return f"""You are an NVIDIA Deep Agent — a powerful AI assistant built for GTC 2026.
Current date (UTC): {datetime.now(timezone.utc):%Y-%m-%d}
Your soul (foundation model) is: {...}

Your enabled capabilities:
{...}

CRITICAL RULES:
1. Answer simple questions directly. For independent subtasks, use task and check its result.
2. File tools require ABSOLUTE paths. Your workspace is: {...}
   For example, a file named hello.py goes under that root.
3. Use web search for current information only when that tool is enabled. Include the current date for news, check publication dates, and cite only claims supported by retrieved text. If freshness or details are unverified, say so.
4. Be concise and technically accurate.
5. You are running on NVIDIA infrastructure.{...}
{...}{...}"""


# ── Exercise 4: Configure the Backend ────────────────────────────────────────

# TODO: Exercise 4
# Fill in _build_backend() to return the right backend:
#   - If "execute" is in skill_ids → 
#         LocalShellBackend (with root_dir as workspace, 60.0 timeout, 50000 max_output_bytes, inherit_env set to False, virtual_mode=True)
#   - Otherwise → 
#         FilesystemBackend (with root_dir as workspace, virtual_mode=True)

def _build_backend(skill_ids: list[str], sandbox_map: dict[str, bool]):
    """
    Build the execution backend.
    If any tools are sandboxed, spin up a real Docker container.
    Otherwise use LocalShellBackend or FilesystemBackend.
    Returns (backend, sandbox_instance_or_None).
    """
    unsupported = [sid for sid, on in sandbox_map.items() if on and sid not in {"fileio", "execute"}]
    if unsupported:
        raise ValueError("Only File I/O and Shell Execution run inside the Docker sandbox.")
    any_sandboxed = any(sandbox_map.get(sid, False) for sid in skill_ids)
    if any_sandboxed:
        from docker_sandbox import DockerSandboxBackend
        try:
            backend = DockerSandboxBackend()
        except Exception as exc:
            raise RuntimeError("Docker sandbox could not start. No agent was created; check Docker and retry.") from exc
        return backend, backend

    # No sandbox — local execution
    workspace = WORKSPACE_DIR
    print(f"[Agent] Sandbox mode OFF — using local workspace: {workspace}")

    if "execute" in skill_ids:
        backend = ...
        print("[Agent] Shell execution enabled via LocalShellBackend")
    else:
        backend = ...
        print("[Agent] Using FilesystemBackend")

    return backend, None


# ── Exercise 5: Wire It All Together ─────────────────────────────────────────

# TODO: Exercise 5
# Fill in create_agent() to:
#   1. Call _get_model() with model_id, _build_extra_tools() with skill_ids
#   2. Build the agent_kwargs dict with model, extra_tools (if it exists), system_prompt, backend, checkpointer
#   3. If hitl_enabled, interrupt the enabled write/edit/execute tools
#   4. Call create_deep_agent on **agent_kwargs and return the result

def create_agent(
    skill_ids: list[str] | None = None,
    model_id: str = "nemotron",
    hitl_enabled: bool = False,
    sandbox_map: dict[str, bool] | None = None,
):
    """
    Create a Deep Agent with optional sandboxing, human-in-the-loop, and skills.
    Returns (agent, sandbox_instance_or_None).
    """
    if skill_ids is None:
        skill_ids = []
    if sandbox_map is None:
        sandbox_map = {}

    model = ...
    extra_tools = ...

    # A requested sandbox must start successfully before creating the agent.
    backend, sandbox = _build_backend(skill_ids, sandbox_map)
    backend = restrict_backend(backend, skill_ids)
    sandbox_active = sandbox is not None
    try:
        system_prompt = _build_system_prompt(skill_ids, model_id, hitl_enabled, sandbox_active)
    except Exception:
        if sandbox is not None:
            sandbox.delete()
        raise

    agent_kwargs: dict = {
        "model": ... ,
        "tools": ... if ... else None,
        "system_prompt": ... ,
        "backend": ... ,
        "checkpointer": ... ,
    }

    if hitl_enabled:
        agent_kwargs["interrupt_on"] = ...

    agent_kwargs["middleware"] = [CapabilityMiddleware(skill_ids)]

    try:
        agent = ...
    except Exception:
        if sandbox is not None:
            sandbox.delete()
        raise
    sandboxed = [k for k, v in sandbox_map.items() if v]
    print(f"[Agent] Created deep agent: skills={skill_ids}, hitl={hitl_enabled}, sandboxed={sandboxed}")
    return agent, sandbox


# ── Test It ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Quick test — run this file directly to verify your implementation."""
    import asyncio

    async def test():
        # create_agent returns (agent, sandbox) — sandbox is None unless a Docker
        # sandbox was requested AND started successfully.
        agent, sandbox = create_agent(
            skill_ids=["websearch", "fileio"],
            model_id="nemotron",
            hitl_enabled=False,
        )
        print("✅ Agent created successfully!")
        print(f"   Type:    {type(agent).__name__}")
        print(f"   Sandbox: {'active' if sandbox else 'none'}")

        # Test with a simple query
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "List files at the file-tool root /"}]},
            config={"configurable": {"thread_id": "test"}},
        )

        last_msg = result["messages"][-1]
        print(f"   Response: {str(last_msg.content)[:200]}")
        print("\n🎉 Your deep agent is working!")

    asyncio.run(test())
