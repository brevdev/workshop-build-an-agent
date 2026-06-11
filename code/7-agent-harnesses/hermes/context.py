"""Context — what actually enters the model's window each turn (Exercise 2).

The model is stateless: every turn it sees ONLY the `messages` list you send.
This module decides what goes into that list — the soul, the long-term memory,
a runtime header — and keeps the whole thing under a token budget by compacting
old turns when it grows too large.

Your job in Exercise 2: fill in the three TODOs below. Until you do, each
function returns a safe placeholder so `python -m hermes` keeps running (the
harness falls back to a default prompt and skips compaction).
"""
from __future__ import annotations

import json
from datetime import date

from . import config, state


def load_soul() -> str:
    """Return HERMES.md, or '' if it is missing."""
    if config.SOUL_PATH.exists():
        return config.SOUL_PATH.read_text(encoding="utf-8")
    return ""


def build_system_prompt() -> str:
    """Assemble the system message: identity, then memory, then a runtime header.

    Order matters and runs stable -> volatile (soul never changes mid-session,
    the runtime header changes every turn). Stable-first content is also more
    cache-friendly for the model server.
    """
    # ── TODO: Exercise 2.1 — assemble the system prompt ──
    # Build it in three parts, in this order, and return the joined string:
    #   1. soul    = load_soul()
    #   2. memory  = state.load_memory() or "(no memories yet)"
    #   3. runtime = a "## Runtime" header with the date (date.today().isoformat()),
    #      config.WORKSPACE_DIR, and the inference mode — which is
    #      "gateway-managed (no local key)" when config.API_KEY is empty,
    #      otherwise config.MODEL_URL.
    # Return: soul + "\n\n## Long-term memory (MEMORY.md)\n" + memory + runtime
    return ...  # replace with the assembled system prompt (a string)


def estimate_tokens(messages) -> int:
    """Rough token count without tiktoken: ~4 characters per token of English.

    tiktoken is not in this environment and would be falsely precise anyway —
    Nemotron uses a different tokenizer. We only need a monotonic estimate to
    decide when to compact, not an exact count.
    """
    # ── TODO: Exercise 2.2 — estimate the window size ──
    # Sum, over every message: len(str(content)) // 4  (the ~4 chars/token rule)
    # plus 8 tokens of structural overhead. Return an int.
    # Hint: sum(len(str(m.get("content") or "")) // 4 + 8 for m in messages)
    return ...  # replace with your estimate (an int)


def compact(messages):
    """Evict the oldest turns when over budget, leaving a one-line stub in their place.

    Returns (new_messages, n_evicted). Keeps the system message (index 0) and the
    most recent KEEP_RECENT_MESSAGES turns. Production harnesses (Module 5's
    summarization middleware, Claude Code) would summarize the evicted span with
    the model; we drop-and-stub to keep it deterministic and obvious.
    """
    if estimate_tokens(messages) <= config.CONTEXT_BUDGET_TOKENS:
        return messages, 0

    # ── TODO: Exercise 2.3 — evict the oldest turns, leave a one-line stub ──
    # Steps:
    #   1. keep_from = max(1, len(messages) - config.KEEP_RECENT_MESSAGES)
    #   2. While messages[keep_from] is a "tool" result, do keep_from += 1
    #      (never separate a tool result from the assistant call that requested it)
    #   3. evicted = messages[1:keep_from]
    #   4. stub = an assistant message noting how many messages were evicted
    #   5. return [messages[0], stub] + messages[keep_from:], len(evicted)
    return messages, 0  # replace this line with your implementation
