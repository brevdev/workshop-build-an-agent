"""Context — what actually enters the model's window each turn (Exercise 2).

Answer key — solved version of hermes/context.py.

The model is stateless: every turn it sees ONLY the `messages` list you send.
This module decides what goes into that list — the soul, the long-term memory,
a runtime header — and keeps the whole thing under a token budget by compacting
old turns when it grows too large.
"""
from __future__ import annotations

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
    # ── TODO: Exercise 2.1 — assemble the system prompt (SOLVED) ──
    soul = load_soul()
    memory = state.load_memory() or "(no memories yet)"
    inference = "gateway-managed (no local key)" if not config.API_KEY else config.MODEL_URL
    runtime = (
        "\n\n## Runtime\n"
        "- Date: {}\n"
        "- Workspace: {}\n"
        "- Inference: {}"
    ).format(date.today().isoformat(), config.WORKSPACE_DIR, inference)
    return soul + "\n\n## Long-term memory (MEMORY.md)\n" + memory + runtime


def estimate_tokens(messages) -> int:
    """Rough token count without tiktoken: ~4 characters per token of English.

    tiktoken is not in this environment and would be falsely precise anyway —
    Nemotron uses a different tokenizer. We only need a monotonic estimate to
    decide when to compact, not an exact count.
    """
    # ── TODO: Exercise 2.2 — estimate the window size (SOLVED) ──
    # ~4 chars/token, plus ~8 tokens of structural overhead per message.
    return sum(len(str(m.get("content") or "")) // 4 + 8 for m in messages)


def compact(messages):
    """Evict the oldest turns when over budget, leaving a one-line stub in their place.

    Returns (new_messages, n_evicted). Keeps the system message (index 0) and the
    most recent KEEP_RECENT_MESSAGES turns. Production harnesses (Module 5's
    summarization middleware, Claude Code) would summarize the evicted span with
    the model; we drop-and-stub to keep it deterministic and obvious.
    """
    if estimate_tokens(messages) <= config.CONTEXT_BUDGET_TOKENS:
        return messages, 0

    # ── TODO: Exercise 2.3 — choose what to keep, then rebuild (SOLVED) ──
    keep_from = max(1, len(messages) - config.KEEP_RECENT_MESSAGES)
    # Never separate a tool result from the assistant message that requested it:
    # if the cut lands on a 'tool' message, walk forward until it doesn't.
    while keep_from < len(messages) and messages[keep_from].get("role") == "tool":
        keep_from += 1

    evicted = messages[1:keep_from]
    stub = {
        "role": "assistant",
        "content": (
            "[Harness note: {} earlier messages were evicted to fit the "
            "{}-token context budget.]".format(len(evicted), config.CONTEXT_BUDGET_TOKENS)
        ),
    }
    return [messages[0], stub] + messages[keep_from:], len(evicted)
