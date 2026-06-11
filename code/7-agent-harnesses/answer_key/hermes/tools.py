"""Tools — what the model can ask the harness to DO (Exercise 3).

Answer key — solved version of hermes/tools.py.

The model never runs anything itself. It emits a structured request ("call
write_file with these arguments"); the harness looks the name up in this
registry and executes the matching Python function. Capability is exactly the
set of tools you register here — nothing more.
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
    # ── TODO: Exercise 3.2 — look up and run the tool (SOLVED) ──
    entry = TOOLS.get(name)
    if entry is None:
        return "[tool error] unknown tool: {}".format(name)
    try:
        return str(entry["fn"](**args))
    except Exception as e:  # Landlock's PermissionError lands HERE in Exercise 5
        return "[tool error] {}: {}".format(type(e).__name__, e)


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
            "required": ["path", "content"],   # ── TODO: Exercise 3.1 (SOLVED)
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
                "url": {"type": "string", "description": "Full URL including https://"}  # ── TODO: Exercise 3.1 (SOLVED)
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


# ── Register the tool set (Exercise 3.1) ───────────────────────────────────
# read_file is the worked example: safe (reading never changes the world).
register("read_file", read_file, READ_FILE_SCHEMA, dangerous=False)
# ── TODO: Exercise 3.1 — register the other three (SOLVED) ──
register("write_file", write_file, WRITE_FILE_SCHEMA, dangerous=True)   # writes change the world
register("fetch_url", fetch_url, FETCH_URL_SCHEMA, dangerous=True)      # reaches the network
register("remember", state.remember, REMEMBER_SCHEMA, dangerous=False)  # appending to your own memory is safe
