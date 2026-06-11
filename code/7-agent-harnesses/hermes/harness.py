"""The harness — the loop that turns a stateless model into Hermes.

This is the machine. It assembles the context, calls the model, runs any tools
the model asks for (behind the gate), and keeps the conversation in a list. The
REPL is just a thin terminal wrapper around `Harness.send()`.

Your job: Exercise 1 wires up `send()` and the REPL (TODOs 1.3, 1.4).
Exercise 3 wires the gate into the tool loop (TODO 3.4).
"""
from __future__ import annotations

import json

from . import __version__, client, config, context, gates, state, tools

# Used in Exercise 1, before context.build_system_prompt() is wired up.
DEFAULT_SYSTEM_PROMPT = "You are Hermes, a helpful assistant."


def banner() -> str:
    """A startup banner that reports which subsystems are wired up yet."""
    sp = context.build_system_prompt()
    if isinstance(sp, str) and sp.strip():
        soul_line = "HERMES.md loaded ({} lines)".format(len(config.SOUL_PATH.read_text().splitlines())) \
            if config.SOUL_PATH.exists() else "default prompt (HERMES.md missing)"
        mem_line = "{} notes in workspace/MEMORY.md".format(state.memory_note_count())
    else:
        soul_line = "not wired (Exercise 2)"
        mem_line = "not wired (Exercise 2)"

    n_tools = len(tools.TOOLS)
    if n_tools:
        n_gated = sum(1 for t in tools.TOOLS.values() if t["dangerous"])
        tools_line = "{} registered ({} gated)".format(n_tools, n_gated)
    else:
        tools_line = "none registered (Exercise 3)"

    inference = "gateway-managed (no local key)" if not config.API_KEY else config.MODEL_URL
    return (
        "Hermes v{} - a glass-box agent harness\n"
        "  model : {} @ {}\n"
        "  soul  : {}\n"
        "  memory: {}\n"
        "  tools : {}\n"
        "  /quit /remember <text> /memory /context /history"
    ).format(__version__, config.MODEL_NAME, inference, soul_line, mem_line, tools_line)


class Harness:
    """One conversation: a system message plus everything that follows."""

    def __init__(self, system_prompt=None, auto_approve=False):
        sp = system_prompt or context.build_system_prompt()
        if not isinstance(sp, str):
            # build_system_prompt() still returns ... before Exercise 2 is done.
            print("[context] HERMES.md not wired yet (Exercise 2) — using a bland default prompt.")
            sp = DEFAULT_SYSTEM_PROMPT
        self.messages = [{"role": "system", "content": sp}]
        self.auto_approve = auto_approve

    def send(self, user_text: str) -> str:
        """Run one user turn end to end and return the assistant's final text."""
        # 0. Keep the window under budget (provided; inert until Exercise 2's
        #    estimate_tokens() returns a real int).
        est = context.estimate_tokens(self.messages)
        if isinstance(est, int) and est > config.CONTEXT_BUDGET_TOKENS:
            self.messages, n = context.compact(self.messages)
            if n:
                noun = "message" if n == 1 else "messages"
                print("[context] compacted {} old {} (est {} -> {} tokens, budget {})".format(
                    n, noun, est, context.estimate_tokens(self.messages), config.CONTEXT_BUDGET_TOKENS))

        # 1. ── TODO: Exercise 1.3 — add the user's message, call the model, keep the reply ──
        # The messages list IS the model's entire memory. Append the user turn,
        # call the model with the current tool schemas, and append its reply.
        self.messages.append(...)   # Hint: {"role": "user", "content": user_text}
        reply = ...                 # Hint: client.chat(self.messages, tools=tools.tool_schemas())
        self.messages.append(reply)

        # 2. Tool loop (scaffold provided; you complete the gate step in Exercise 3.4).
        #    Until you register tools in Exercise 3.1, reply has no tool_calls and
        #    this loop never runs — so Exercises 1-2 are unaffected.
        rounds = 0
        while reply.get("tool_calls") and rounds < config.MAX_TOOL_ROUNDS:
            for call in reply["tool_calls"]:
                name = call["function"]["name"]
                try:
                    args = json.loads(call["function"]["arguments"] or "{}")  # arguments is a STRING
                except (ValueError, TypeError):
                    args = {}
                # ── TODO: Exercise 3.4 — gate the call, then dispatch it ──
                # If check_gate approves, run the tool; otherwise return the denial
                # text so the model can recover gracefully.
                if gates.check_gate(name, args, self.auto_approve):
                    result = ...   # Hint: tools.dispatch(name, args)
                else:
                    result = gates.denial_message(name)
                print("[tool] {} -> {}".format(name, str(result)[:120]))
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": name,
                    "content": str(result),
                })
            reply = client.chat(self.messages, tools=tools.tool_schemas())
            self.messages.append(reply)
            rounds += 1

        # 3. Return the final answer (reasoning stripped for display).
        return client.strip_reasoning(reply.get("content") or "")

    def repl(self) -> None:
        """Interactive terminal loop."""
        print(banner())
        while True:
            try:
                line = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                continue
            if line in ("/quit", "/exit"):
                break
            if line.startswith("/remember "):
                print(state.remember(line[len("/remember "):]))
                continue
            if line == "/memory":
                print(state.load_memory() or "(no memories yet)")
                continue
            if line == "/context":
                print("messages: {} | est tokens: {} | budget: {}".format(
                    len(self.messages), context.estimate_tokens(self.messages),
                    config.CONTEXT_BUDGET_TOKENS))
                continue
            if line == "/history":
                for m in self.messages:
                    preview = str(m.get("content") or m.get("tool_calls") or "")[:80]
                    print("  {:<9} {}".format(m.get("role", "?"), preview))
                continue
            # ── TODO: Exercise 1.4 — answer the user ──
            # Send the line through the harness and print the reply.
            print("hermes>", ...)  # Hint: self.send(line)
