"""State — long-term memory that survives a restart (Exercise 2).

Short-term memory is just the `messages` list living in the harness (you built
that in Exercise 1). Long-term memory is a file: MEMORY.md. The same idea
OpenClaw uses in Module 6 — and the same file Module 6's Probe 4 poisoned.

Your job in Exercise 2: fill in the TODO in `remember()`.
"""
from __future__ import annotations

from datetime import date

from . import config


def load_memory() -> str:
    """Return the contents of MEMORY.md, or '' if it does not exist yet."""
    if config.MEMORY_PATH.exists():
        return config.MEMORY_PATH.read_text(encoding="utf-8")
    return ""


def memory_note_count() -> int:
    """Count stored notes (lines that begin with the '- [' bullet marker)."""
    return sum(1 for line in load_memory().splitlines() if line.startswith("- ["))


def remember(note: str) -> str:
    """Append one durable fact to MEMORY.md and confirm.

    Used two ways: the human types `/remember ...` in the REPL (Exercise 2), and
    the model calls this as the `remember` tool (Exercise 3).
    """
    new_file = not config.MEMORY_PATH.exists()
    with config.MEMORY_PATH.open("a", encoding="utf-8") as f:
        if new_file:
            f.write("# MEMORY.md — Hermes long-term memory\n\n")
        # ── TODO: Exercise 2.4 — append the note as a dated bullet ──
        # Write one line so it survives a restart and reloads via build_system_prompt().
        f.write(...)  # Hint: "- [{}] {}\n".format(date.today().isoformat(), note.strip())
    return "Noted. MEMORY.md now has {} entries.".format(memory_note_count())
