"""Deep Agent factory — thin adapter over the Module 5 exercise file.

The factory lives in ``code/5-deep-agents/deep_agent.py``; this module re-exports
``create_agent`` from it so the learner's completed exercises are what the Deep
Agents Client runs — no copy-paste step, no second copy to drift.

Module 5 has you use the client *before* you build the agent, so an unfinished
exercise file must not take the demo down: ``deep_agent.py`` is used once its
blanks are filled, ``deep_agent.answers.py`` until then. The active choice is
printed at import and reported by ``active_implementation()``.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys
from types import ModuleType

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir, os.pardir))
_MODULE_5_DIR = os.path.join(_REPO_ROOT, "code", "5-deep-agents")

_EXERCISE_FILE = os.path.join(_MODULE_5_DIR, "deep_agent.py")
_ANSWERS_FILE = os.path.join(_MODULE_5_DIR, "deep_agent.answers.py")

# The functions the lesson asks the learner to fill in.
_EXERCISE_FUNCS = (
    "_get_model",
    "_build_extra_tools",
    "_build_system_prompt",
    "_build_backend",
    "create_agent",
)


def _unfilled_exercises(path: str) -> list[str] | None:
    """Names of exercise functions that still contain a ``...`` placeholder.

    Returns None when the file cannot be read or parsed at all. The blanks are
    literal ``Ellipsis`` expressions that parse fine and only fail at call time,
    so this static check is reliable and free of side effects.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
    except (OSError, SyntaxError):
        return None

    unfilled = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in _EXERCISE_FUNCS
            and any(
                isinstance(sub, ast.Constant) and sub.value is Ellipsis
                for sub in ast.walk(node)
            )
        ):
            unfilled.add(node.name)
    return sorted(unfilled)


def _load(path: str, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _select() -> tuple[ModuleType, str, list[str]]:
    """Return (module, which, unfilled) where which is 'exercise' or 'answers'."""
    unfilled = _unfilled_exercises(_EXERCISE_FILE)

    if unfilled == []:  # parsed cleanly, and every blank is filled in
        try:
            return _load(_EXERCISE_FILE, "deep_agent_impl"), "exercise", []
        except Exception as exc:
            print("=" * 72)
            print("[Agent] Your deep_agent.py raised while importing:")
            print(f"[Agent]     {type(exc).__name__}: {exc}")
            print("[Agent] Falling back to the reference implementation.")
            print("=" * 72)

    if not os.path.isfile(_ANSWERS_FILE):  # pragma: no cover - ships with the repo
        raise ImportError(
            f"Neither a completed {_EXERCISE_FILE} nor {_ANSWERS_FILE} is usable."
        )
    return _load(_ANSWERS_FILE, "deep_agent_impl"), "answers", unfilled or []


_impl, _which, _unfilled = _select()

if _which == "exercise":
    print("[Agent] Using YOUR implementation: code/5-deep-agents/deep_agent.py")
else:
    _detail = (
        f"exercises still open: {', '.join(_unfilled)}"
        if _unfilled
        else "deep_agent.py could not be parsed"
    )
    print(
        "[Agent] Using the REFERENCE implementation "
        f"(code/5-deep-agents/deep_agent.answers.py) — {_detail}."
    )
    print(
        "[Agent] Finish the exercises in code/5-deep-agents/deep_agent.py and "
        "restart the backend to run your own."
    )


def active_implementation() -> dict:
    """Which factory is live — surfaced so the demo never overstates things."""
    return {
        "which": _which,
        "path": _EXERCISE_FILE if _which == "exercise" else _ANSWERS_FILE,
        "unfilled_exercises": _unfilled,
    }


# Re-export the factory plus the names the demo and lesson refer to directly.
create_agent = _impl.create_agent

MODEL_MAP = _impl.MODEL_MAP
MODEL_DISPLAY_NAMES = _impl.MODEL_DISPLAY_NAMES
INTERRUPT_TOOLS = _impl.INTERRUPT_TOOLS
WORKSPACE_DIR = _impl.WORKSPACE_DIR
SANDBOX_WORKSPACE_DIR = _impl.SANDBOX_WORKSPACE_DIR
SKILLS_DIR = _impl.SKILLS_DIR
checkpointer = _impl.checkpointer

__all__ = [
    "create_agent",
    "active_implementation",
    "MODEL_MAP",
    "MODEL_DISPLAY_NAMES",
    "INTERRUPT_TOOLS",
    "WORKSPACE_DIR",
    "SANDBOX_WORKSPACE_DIR",
    "SKILLS_DIR",
    "checkpointer",
]
