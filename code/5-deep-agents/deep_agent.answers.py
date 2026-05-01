"""
Deep Agent Factory — Module 5 Exercise File

Complete the TODO exercises below to build a production-grade deep agent.
Each exercise corresponds to a section in the Build a Deep Agent lesson.

Run the completed agent via the demo UI:
    Click "Deep Agents Client" tile from the Jupyterlab Launcher page                                # Frontend
    cd demo/backend && source .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8000    # Backend
"""

import os
from dotenv import load_dotenv

load_dotenv()

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, LocalShellBackend, CompositeBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain_nvidia_ai_endpoints import ChatNVIDIA


# ── Configuration ─────────────────────────────────────────────────────────────

# Workspace directories
WORKSPACE_DIR = "/tmp/deepagent_workspace"            # Local (has sensitive files for demo)
SANDBOX_WORKSPACE_DIR = "/workspace"                  # Path INSIDE Docker container
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# Skills directory
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")
os.makedirs(SKILLS_DIR, exist_ok=True)

# Shared checkpointer for all sessions (in-memory, resets on server restart)
checkpointer = MemorySaver()

# Map UI model IDs to NVIDIA NIM model strings (verified available)
MODEL_MAP = {
    "nemotron": "nvidia/nemotron-3-super-120b-a12b",
    "llama": "meta/llama-3.3-70b-instruct",
    "deepseek": "deepseek-ai/deepseek-r1-0528",
    "claude": "meta/llama-3.3-70b-instruct",
}

MODEL_DISPLAY_NAMES = {
    "nemotron": "Nemotron (NVIDIA)",
    "llama": "Llama 3.3 (Meta)",
    "deepseek": "DeepSeek R1 (DeepSeek)",
    "claude": "Claude-style (Anthropic fallback)",
}

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
# Set temperature to 0.3.

def _get_model(model_id: str = "llama"):
    """Return an NVIDIA NIM chat model for the given model ID."""
    api_key = os.getenv("NVIDIA_API_KEY")
    model_name = MODEL_MAP.get(model_id, MODEL_MAP["llama"])
    print(f"[Agent] Using model: {model_name} (id={model_id})")
    return ChatNVIDIA(
        model=model_name,
        api_key=api_key,
        temperature=0.3,
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
            tavily_key = os.getenv("TAVILY_API_KEY")
            if tavily_key:
                tools.append(TavilySearchResults(max_results=3, api_key=tavily_key))
                print("[Agent] Added Tavily web search tool")
        except ImportError:
            print("[Agent] Tavily not available")

    if "rag" in skill_ids:
        try:
            from rag import get_retriever_tool
            tool = get_retriever_tool()
            if tool:
                tools.append(tool)
                print("[Agent] Added IT knowledge base RAG tool")
        except Exception as e:
            print(f"[Agent] RAG tool not available: {e}")

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

def _get_skill_sources() -> list[str]:
    """Get list of skill source directories if any skills exist."""
    if os.path.exists(SKILLS_DIR) and os.listdir(SKILLS_DIR):
        return ["/skills/"]
    return []


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
    workspace = SANDBOX_WORKSPACE_DIR if sandbox_enabled else WORKSPACE_DIR

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

    builtin = ["- Planning (write_todos): organize tasks"]
    all_capabilities = enabled + builtin if enabled else builtin
    caps_text = "\n".join(all_capabilities)

    rag_rule = ""
    if "rag" in skill_ids:
        rag_rule = "\n6. When the user asks about IT policies, procedures, passwords, virtual desktops, VPN, software installation, hardware, or any internal company IT questions, ALWAYS use the it_knowledge_base tool to search the knowledge base. Do NOT use file tools (ls, grep, etc.) for IT-related questions."

    hitl_note = ""
    if hitl_enabled:
        hitl_note = """
NOTE: Some tools (write_file, edit_file, execute) require human approval.
The user will be asked to approve, edit, or reject your tool calls before they execute.
Continue normally after approval — do not ask the user to approve manually."""

    # Load skill content if any skills are selected
    skill_content = _load_skill_content(skill_ids)
    skill_section = f"\n\n---\n\n{skill_content}" if skill_content else ""

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


# ── Exercise 4: Configure the Backend ────────────────────────────────────────

# TODO: Exercise 4
# Fill in _build_backend() to return the right backend:
#   - If "execute" is in skill_ids → 
#         LocalShellBackend (with root_dir as workspace, 60.0 timeout, 50000 max_output_bytes, inherit_env set to True)
#   - Otherwise → 
#         FilesystemBackend (with root_dir as workspace)

def _build_backend(skill_ids: list[str], sandbox_map: dict[str, bool]):
    """
    Build the execution backend.
    If any tools are sandboxed, spin up a real Docker container.
    Otherwise use LocalShellBackend or FilesystemBackend.
    Returns (backend, sandbox_instance_or_None).
    """
    any_sandboxed = any(sandbox_map.get(sid, False) for sid in skill_ids)

    if any_sandboxed:
        try:
            from docker_sandbox import DockerSandboxBackend

            backend = DockerSandboxBackend()
            sandboxed_tools = [k for k, v in sandbox_map.items() if v]
            print(f"[Agent] Docker sandbox created for tools: {sandboxed_tools}")
            return backend, backend  # backend IS the sandbox (has .delete())
        except Exception as e:
            print(f"[Agent] WARNING: Failed to create Docker sandbox: {e}. Falling back to local.")

    # No sandbox — local execution
    workspace = WORKSPACE_DIR
    print(f"[Agent] Sandbox mode OFF — using local workspace: {workspace}")

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

    return backend, None


# ── Exercise 5: Wire It All Together ─────────────────────────────────────────

# TODO: Exercise 5
# Fill in create_agent() to:
#   1. Call _get_model() with model_id, _build_extra_tools() with skill_ids
#   2. Build the agent_kwargs dict with model, extra_tools (if it exists), system_prompt, backend, checkpointer
#   3. If hitl_enabled, add interrupt_on=INTERRUPT_TOOLS
#   4. Call create_deep_agent on **agent_kwargs and return the result

def create_agent(
    skill_ids: list[str] | None = None,
    model_id: str = "llama",
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
    sandboxed = [k for k, v in sandbox_map.items() if v]
    print(f"[Agent] Created deep agent: skills={skill_ids}, hitl={hitl_enabled}, sandboxed={sandboxed}")
    return agent, sandbox


# ── Test It ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Quick test — run this file directly to verify your implementation."""
    import asyncio

    async def test():
        agent = create_agent(
            skill_ids=["websearch", "fileio"],
            model_id="nemotron",
            hitl_enabled=False,
        )
        print("✅ Agent created successfully!")
        print(f"   Type: {type(agent).__name__}")

        # Test with a simple query
        result = await agent[0].ainvoke(
            {"messages": [{"role": "user", "content": "List all files in /tmp/deepagent_workspace"}]},
            config={"configurable": {"thread_id": "test"}},
        )

        last_msg = result["messages"][-1]
        print(f"   Response: {str(last_msg.content)[:200]}")
        print("\n🎉 Your deep agent is working!")

    asyncio.run(test())
