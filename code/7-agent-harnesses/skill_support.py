"""Validate skill metadata and keep generated files in the lab skills folder."""

from pathlib import Path
import re

import yaml


def parse_frontmatter(skill_md: str, expected_name: str | None = None) -> dict:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", skill_md, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md needs YAML frontmatter between --- lines")
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError("SKILL.md frontmatter is not valid YAML") from exc
    if not isinstance(meta, dict):
        raise ValueError("Frontmatter must contain name and description fields")
    name, description = meta.get("name"), meta.get("description")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        raise ValueError("Use a name of up to 64 lowercase letters, numbers, and single hyphens")
    if expected_name is not None and name != expected_name:
        raise ValueError("The skill name must match its folder name")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        raise ValueError("Use a nonempty description of up to 1024 characters")
    return {**meta, "description": " ".join(description.split())}


def skill_target(skills_dir: Path, name: str) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        raise ValueError("Invalid skill name")
    root = Path(skills_dir).resolve()
    target = root / name / "SKILL.md"
    if not target.resolve().is_relative_to(root):
        raise ValueError("The skill path points outside the skills folder")
    return target


def read_skill_text(skill_file: Path, skills_dir: Path) -> str:
    target = skill_target(skills_dir, skill_file.parent.name)
    text = target.read_text()
    parse_frontmatter(text, expected_name=skill_file.parent.name)
    return text
