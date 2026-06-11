"""Tools — what the model can ask the harness to DO (Exercise 3).

The model never runs anything itself. It emits a structured request ("call
write_file with these arguments"); the harness looks the name up in this
registry and executes the matching Python function. Capability is exactly the
set of tools you register here — nothing more.

Your job in Exercise 3: complete the schemas, register the tools (3.1), and
write `dispatch` (3.2). The tool functions themselves are provided.
Until you register tools, the model is told about none, so Exercises 1-2 still
run with no tool behavior.
"""
from __future__ import annotations

import urllib.error
import urllib.request

from . import client, config, state

# name -> {"schema": <JSON schema dict>, "fn": <callable>, "dangerous": <bool>}
TOOLS: dict = {}


def register(name: str, fn, schema: dict, dangerous: bool) -> None:
    """Add one tool to the registry."""
    TOOLS[name] = {"schema": schema, "fn": fn, "dangerous": dangerous}


def tool_schemas() -> list:
    """The list of schemas advertised to the model on every request."""
    return [t["schema"] for t in TOOLS.values()]


def is_dangerous(name: str) -> bool:
    entry = TOOLS.get(name)
    return bool(entry and entry["dangerous"])


def dispatch(name: str, args: dict) -> str:
    """Execute a tool by name and return its result as a string.

    A tool that raises (including a kernel PermissionError from Landlock in the
    sandbox) is caught here and reported back to the model as a tool result, so
    the conversation continues instead of crashing.
    """
    # ── TODO: Exercise 3.2 — look up and run the tool ──
    # 1. entry = TOOLS.get(name); if None, return "[tool error] unknown tool: ..."
    # 2. In a try/except, return str(entry["fn"](**args)).
    # 3. On Exception e, return "[tool error] {type}: {e}".
    #    (In Exercise 5, Landlock's PermissionError lands in exactly this except.)
    entry = ...  # Hint: TOOLS.get(name)
    if entry is None:
        return "[tool error] unknown tool: {}".format(name)
    try:
        return ...  # Hint: str(entry["fn"](**args))
    except Exception as e:
        return ...  # Hint: "[tool error] {}: {}".format(type(e).__name__, e)


# ── Tool implementations (provided in full) ───────────────────────────────
def _resolve(path: str) -> str:
    """Absolute paths pass through; bare names resolve inside the workspace."""
    if path.startswith("/"):
        return path
    return str(config.WORKSPACE_DIR.joinpath(path))


def read_file(path: str) -> str:
    """Read a text file (first 4000 chars)."""
    with open(_resolve(path), encoding="utf-8") as f:
        return f.read()[:4000]


def write_file(path: str, content: str) -> str:
    """Write text to a file. No directories are created — write where you can."""
    target = _resolve(path)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    return "Wrote {} chars to {}".format(len(content), target)


def fetch_url(url: str) -> str:
    """GET a URL (first 500 bytes). Renders kernel denials in plain language."""
    try:
        with urllib.request.urlopen(url, timeout=15, context=client._ssl_context()) as r:
            return r.read(500).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return (
            "[fetch denied] HTTP {} for {} — a 403 here is the sandbox proxy refusing "
            "egress AFTER your harness gate approved. The harness asks; the kernel enforces.".format(e.code, url)
        )
    except urllib.error.URLError as e:
        return (
            "[fetch failed] {} — outbound to {} was refused. Inside the sandbox this is "
            "the kernel network policy, not Hermes.".format(e.reason, url)
        )


# ── Tool schemas (Module 1 format) ────────────────────────────────────────
# read_file is the complete worked example. Use it as the template for the
# two TODO holes below.
READ_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a text file from disk (first 4000 chars).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or workspace-relative path"}
            },
            "required": ["path"],
        },
    },
}

WRITE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write text to a file on disk.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or workspace-relative path"},
                "content": {"type": "string", "description": "Text to write"},
            },
            "required": ...,  # ── TODO: Exercise 3.1 — which fields are required? Hint: ["path", "content"]
        },
    },
}

FETCH_URL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "fetch_url",
        "description": "HTTP GET a URL and return the first 500 bytes.",
        "parameters": {
            "type": "object",
            "properties": {
                # ── TODO: Exercise 3.1 — describe the one parameter, "url"
                "url": ...,  # Hint: {"type": "string", "description": "Full URL including https://"}
            },
            "required": ["url"],
        },
    },
}

REMEMBER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "remember",
        "description": "Store one durable fact about the user in long-term memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "note": {"type": "string", "description": "One durable fact to store in MEMORY.md"}
            },
            "required": ["note"],
        },
    },
}


# ── Register the tool set ──────────────────────────────────────────────────
# ── TODO: Exercise 3.1 — register all four tools ──
# Replace the `...` below with four register(name, fn, schema, dangerous) calls.
# The first is given as the worked example — type it in as-is, then add the
# other three by analogy. Decide each one's `dangerous` flag: can it change the
# world or reach outside this process? Writing files and fetching URLs can, so
# they need the gate you build in 3.3; reading a file and appending to your own
# memory are safe.
#
#   register("read_file", read_file, READ_FILE_SCHEMA, dangerous=False)   # worked example
#
# (Until you register tools, the model is told about none, so Exercises 1-2 run
# with no tool behavior — that is why you can leave this for last.)
...
