"""Gates — the harness asking permission before a dangerous tool runs (Exercise 3).

This is human-in-the-loop approval, the same idea as Module 4's bash agent and
Module 5's deep agent. Read it carefully and notice what it is: about ten lines
of Python that print a prompt and read y/N. Nothing but this process enforces
it. That is the whole point of Exercise 5 — a kernel does NOT ask.

Your job in Exercise 3: fill in the TODO in `check_gate`.
"""
from __future__ import annotations

import sys

from . import config

_SAFE_NOTICE_SHOWN = set()
_BOX_WIDTH = 58


def _box_line(text: str) -> str:
    """One interior row of the gate box, padded/truncated to a fixed width."""
    return "  | {:<{w}} |".format(text[:_BOX_WIDTH], w=_BOX_WIDTH)


def render_gate_prompt(name: str, args: dict) -> str:
    """Build the approval prompt shown in the terminal."""
    border = "  +" + "-" * (_BOX_WIDTH + 2) + "+"
    lines = [border, _box_line("PERMISSION GATE"), _box_line("Hermes wants to run: " + name)]
    for key, value in args.items():
        shown = repr(value)
        if len(shown) > 34:
            shown = shown[:31] + "...'"
        lines.append(_box_line("  {} = {}".format(key, shown)))
    lines.append(_box_line(""))
    lines.append(_box_line("This gate is ~10 lines of Python in gates.py."))
    lines.append(_box_line("Nothing but this process enforces it."))
    lines.append(border)
    lines.append("  Approve? [y/N]: ")
    return "\n".join(lines)


def denial_message(name: str) -> str:
    """The tool result returned to the model when the user says no."""
    return "[gate] The user declined permission to run {}.".format(name)


def check_gate(name: str, args: dict, auto_approve: bool = False) -> bool:
    """Return True if the tool may run.

    Safe tools always pass. Dangerous tools require approval: an explicit
    auto-approve flag, or an interactive y/N. With no TTY and no auto-approve we
    fail closed (deny) — the safe default for unattended runs.
    """
    from . import tools  # local import avoids a circular dependency at module load

    if not tools.is_dangerous(name):
        if name not in _SAFE_NOTICE_SHOWN:
            print("[gate] {} is marked safe — no approval needed.".format(name))
            _SAFE_NOTICE_SHOWN.add(name)
        return True

    if auto_approve or config.AUTO_APPROVE:
        print("[gate] AUTO-APPROVED {} (HERMES_AUTO_APPROVE).".format(name))
        return True

    if not sys.stdin.isatty():
        print("[gate] no TTY and no auto-approve — denying {} (fail closed).".format(name))
        return False

    # ── TODO: Exercise 3.3 — ask the human and read the answer ──
    # Print the gate prompt, read a line, and return True ONLY for "y".
    # This y/N is the ENTIRE enforcement. Module 6's kernel did not ask.
    answer = ...  # Hint: input(render_gate_prompt(name, args))
    return ...    # Hint: answer.strip().lower() == "y"
