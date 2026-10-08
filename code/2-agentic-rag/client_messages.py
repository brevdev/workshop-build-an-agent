"""Small, UI-independent helpers for LangGraph state and error events."""

import hashlib
import json
import re


def content_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(block if isinstance(block, str) else block["text"]
                         for block in content
                         if isinstance(block, str) or
                         (isinstance(block, dict) and isinstance(block.get("text"), str)))
    return ""


def normalize_message(message):
    role = message.get("type", message.get("role", "ai"))
    if role in ("human", "user", "system"):
        return None
    text = content_text(message.get("content", ""))
    reasoning = content_text(message.get("additional_kwargs", {}).get("reasoning_content", ""))
    if "</think>" in text:
        thought, text = text.split("</think>", 1)
        reasoning = reasoning or thought.removeprefix("<think>").strip()
    if not text.strip() and not reasoning.strip():
        return None
    identity = message.get("id") or hashlib.sha256(json.dumps(message, sort_keys=True, default=str).encode()).hexdigest()
    return {"id": identity, "role": "tool" if role == "tool" else "ai",
            "name": message.get("name", "tool"), "content": text.strip(), "think": reasoning.strip()}


def stream_error(data):
    """Retain a known HTTP status, never a provider payload or credential URL."""
    kind = data.get("error", "RunError") if isinstance(data, dict) else "RunError"
    kind = re.sub(r"[^a-zA-Z0-9_.-]", "", str(kind))[:80] or "RunError"
    detail = data.get("message", "") if isinstance(data, dict) else ""
    if "do not have a corresponding ToolMessage" in str(detail):
        # A tool failed mid-run; this thread can never accept another message.
        return ("This conversation has an unfinished tool call from a failed run and cannot continue. "
                "Click New conversation in the sidebar, then ask again.")
    if "maximum context length" in str(detail):
        # vLLM rejects a request whose history plus max_tokens exceeds the model's window.
        return ("This conversation no longer fits in the model's context window. "
                "Click New conversation in the sidebar, then ask again.")
    status = re.search(r"\b(401|403|404|410|429|500|502|503|504)\b", str(detail))
    if status:
        kind = f"HTTP {status.group(1)}"
    return (f"Agent run failed ({kind}). Check Workshop Health and the agent server logs, then retry. "
            "If the same error repeats, click New conversation in the sidebar.")
