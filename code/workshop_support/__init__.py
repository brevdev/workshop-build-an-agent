"""Shared model settings and secrets loading for the workshop."""

import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_model(role: str) -> str:
    """Return the configured hosted model for a workshop role."""
    settings = json.loads(Path(__file__).with_name("models.json").read_text())
    if role not in settings:
        raise ValueError(f"Unknown workshop model role: {role}")
    return os.environ.get(f"WORKSHOP_{role.upper()}_MODEL", settings[role]["id"])


def load_secrets(project_root: str | Path | None = None) -> Path:
    """Load saved workshop settings, including key updates and clears."""
    from dotenv import load_dotenv

    path = Path(project_root or PROJECT_ROOT) / "secrets.env"
    load_dotenv(path, override=True)
    if not (os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")):
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
    return path
