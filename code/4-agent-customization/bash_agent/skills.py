"""
Skills module for the Bash Agent.

Provides tools to load and list skills from the Superpowers framework.
Skills are structured workflows that guide the agent through complex tasks
like debugging, test-driven development, and planning.

This module is only used by the BASE bash agent (main_langgraph.py),
NOT the fine-tuned LangGraph CLI agent (main_hf.py).
"""

from pathlib import Path
from langchain_core.tools import tool

# Skills directory is inside module 4: code/4-agent-customization/skills/superpowers/
SKILLS_DIR = Path(__file__).parent.parent / "skills" / "superpowers"


def load_skill(skill_name: str) -> str:
    """Load a skill from the skills directory."""
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text()
    return f"Skill '{skill_name}' not found. Use list_available_skills() to see available skills."


def list_skills() -> list[str]:
    """List all available skills."""
    if not SKILLS_DIR.exists():
        return []
    return sorted([d.name for d in SKILLS_DIR.iterdir() if d.is_dir()])


@tool
def get_skill(skill_name: str) -> str:
    """Load a specific skill to gain expertise in that workflow.
    
    Use this before starting complex tasks like debugging, planning, or test-driven development.
    Skills provide structured workflows and best practices to follow.
    
    Args:
        skill_name: Name of the skill to load (e.g., 'systematic-debugging', 'test-driven-development')
    
    Returns:
        The skill's content with instructions to follow.
    """
    return load_skill(skill_name)


@tool
def list_available_skills() -> list[str]:
    """List all available skills that can be loaded.
    
    Returns a list of skill names. Use get_skill(name) to load a specific skill.
    
    Available skills include:
    - systematic-debugging: 4-phase root cause analysis for bugs
    - test-driven-development: RED-GREEN-REFACTOR workflow
    - brainstorming: Socratic design refinement
    - writing-plans: Create detailed implementation plans
    - executing-plans: Execute plans in batches with checkpoints
    - using-superpowers: How to use the skills system
    """
    return list_skills()
