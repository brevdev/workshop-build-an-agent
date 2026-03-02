"""
Deep Agent Factory — Module 5 Exercise File

Complete the TODO exercises below to build a production-grade deep agent.
Each exercise corresponds to a section in the Build a Deep Agent lesson.

Run the completed agent via the demo UI:
    cd demo && npm run dev          # Frontend
    cd demo/backend && uvicorn server:app --port 8000  # Backend
"""

import os
from dotenv import load_dotenv

load_dotenv()

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, LocalShellBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain_nvidia_ai_endpoints import ChatNVIDIA


# ── Configuration ─────────────────────────────────────────────────────────────

WORKSPACE_DIR = "/tmp/deepagent_workspace"
os.makedirs(WORKSPACE_DIR, exist_ok=True)

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "demo", "backend", "skills")

# Model mapping — UI model IDs to NVIDIA NIM model strings
MODEL_MAP = {
    "nemotron": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "llama": "meta/llama-3.3-70b-instruct",
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
# Use MODEL_MAP to look up the model name, and os.getenv("NVIDIA_API_KEY") for the key.
# Set temperature to 0.3.

def _get_model(model_id: str = "nemotron"):
    """Return an NVIDIA NIM chat model for the given model ID."""
    pass  # ← Replace this


# ── Exercise 2: Build the Tool Pipeline ──────────────────────────────────────

# TODO: Exercise 2
# Fill in _build_extra_tools() to add a TavilySearchResults tool
# when "websearch" is in the skill_ids list.
# Use os.getenv("TAVILY_API_KEY") for the key, and max_results=3.

def _build_extra_tools(skill_ids: list[str]) -> list:
    """Build additional tools based on user-selected skills."""
    tools = []
    pass  # ← Add web search tool here
    return tools


# ── Exercise 3: Write the System Prompt ──────────────────────────────────────

# TODO: Exercise 3
# Fill in _build_system_prompt() to create the agent's instructions.
# Include: enabled capabilities list, workspace path, critical rules.
# The prompt should tell the agent:
#   - What tools it has available
#   - To use absolute paths under WORKSPACE_DIR
#   - To never repeat the same tool call
#   - To be concise and accurate

def _build_system_prompt(skill_ids: list[str], model_id: str, hitl_enabled: bool) -> str:
    """Create a system prompt with the agent's capabilities and rules."""
    pass  # ← Build and return the prompt string


# ── Skill Loading (provided) ─────────────────────────────────────────────────

# Map skill IDs to markdown files
skill_files = {
    "superpowers": "superpowers.md",
    "cudf": "cudf.md",
    "code_review": "code_review.md",
    # TODO: Exercise 6 — Add your custom skill here
    # "my_skill": "my_skill.md",
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


# ── Exercise 4: Configure the Backend ────────────────────────────────────────

# TODO: Exercise 4
# Fill in _build_backend() to return the right backend:
#   - If "execute" is in skill_ids → LocalShellBackend (with root_dir, timeout, max_output_bytes)
#   - Otherwise → FilesystemBackend (with root_dir)
# Use WORKSPACE_DIR as the root directory.

def _build_backend(skill_ids: list[str]):
    """Build the execution backend based on selected skills."""
    pass  # ← Return the appropriate backend


# ── Exercise 5: Wire It All Together ─────────────────────────────────────────

# TODO: Exercise 5
# Fill in create_agent() to:
#   1. Call _get_model(), _build_extra_tools(), _build_system_prompt(), _build_backend()
#   2. Build the agent_kwargs dict with model, tools, system_prompt, backend, checkpointer
#   3. If hitl_enabled, add interrupt_on=INTERRUPT_TOOLS
#   4. Call create_deep_agent(**agent_kwargs) and return the result

def create_agent(
    skill_ids: list[str] | None = None,
    model_id: str = "nemotron",
    hitl_enabled: bool = False,
):
    """Create a Deep Agent with the specified configuration."""
    if skill_ids is None:
        skill_ids = []

    pass  # ← Build and return the deep agent


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
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "List all files in /tmp/deepagent_workspace"}]},
            config={"configurable": {"thread_id": "test"}},
        )

        last_msg = result["messages"][-1]
        print(f"   Response: {str(last_msg.content)[:200]}")
        print("\n🎉 Your deep agent is working!")

    asyncio.run(test())
