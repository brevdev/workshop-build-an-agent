"""Hermes configuration — every knob the harness has, in one place.

Answer key — Module 7. This file ships complete (no exercises); it is the
same in the student package and here. Everything is overridable by an
environment variable so Exercise 5 can repoint Hermes at the sandbox gateway
without editing code.
"""
from __future__ import annotations

import os
from pathlib import Path

# ── Model (the same endpoint and model you used in Module 1) ──────────────
# HERMES_BASE_URL lets Exercise 5 swap in the sandbox gateway (inference.local).
MODEL_URL = os.environ.get("HERMES_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_NAME = os.environ.get("HERMES_MODEL", "nvidia/nemotron-3-super-120b-a12b")
# Empty inside the sandbox — that is the point. The gateway injects the real key.
API_KEY = os.environ.get("NVIDIA_API_KEY", "")
REQUEST_TIMEOUT = 120
TEMPERATURE = 0.6
MAX_TOKENS = 2048

# ── Context budget (Exercise 2) ───────────────────────────────────────────
# Set HERMES_BUDGET=500 to watch compaction trigger after a few turns.
CONTEXT_BUDGET_TOKENS = int(os.environ.get("HERMES_BUDGET", "4000"))
# How many of the most recent messages compaction always keeps (the last two
# user/assistant exchanges). Compaction can only evict messages OLDER than this,
# so the window may sit a little above budget until enough turns accumulate.
KEEP_RECENT_MESSAGES = 4

# ── Behavior flags ────────────────────────────────────────────────────────
AUTO_APPROVE = os.environ.get("HERMES_AUTO_APPROVE", "") == "1"
TLS_INSECURE = os.environ.get("HERMES_TLS_INSECURE", "") == "1"

# ── Paths (work unchanged on the host AND at /sandbox/hermes) ─────────────
PACKAGE_DIR = Path(__file__).resolve().parent
HERMES_HOME = Path(os.environ.get("HERMES_HOME", PACKAGE_DIR.parent))
WORKSPACE_DIR = HERMES_HOME / "workspace"
SOUL_PATH = PACKAGE_DIR / "HERMES.md"
MEMORY_PATH = WORKSPACE_DIR / "MEMORY.md"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# How many times the model may call tools before we force a final answer.
MAX_TOOL_ROUNDS = 8
