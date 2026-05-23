"""
NemoClaw Agent Wrapper — Module 6

Bridges the sandboxed OpenClaw agent (running inside a NemoClaw OpenShell
sandbox) to the exercise `agent_fn(prompt) -> dict` interface used by
`nemoclaw_client.py`.

Transport: `nemoclaw <sandbox> exec -- openclaw agent --agent main --json -m
"<prompt>"`. The in-sandbox `openclaw` produces the same `--json` output shape
as the host-side binary, so the JSON parsing mirrors `openclaw_wrapper`.

Usage:
    from nemoclaw_wrapper import create_nemoclaw_agent_fn

    agent_fn = create_nemoclaw_agent_fn()
    result = agent_fn("Hello")
    # result = {"text": "...", "meta": {...}, "error": None}
"""

import json as _json
import os
import re
import shutil
import subprocess
import sys
from typing import Callable, Optional


_PHASE_READY_RE = re.compile(r"^\s*Phase:\s*Ready\b", re.MULTILINE | re.IGNORECASE)
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Last reason detection failed. Surfaced by the UI for diagnostics.
LAST_DETECT_ERROR: Optional[str] = None


def _log(msg: str) -> None:
    """Write a diagnostic line to stderr so Streamlit's terminal shows it."""
    print(f"[nemoclaw_wrapper] {msg}", file=sys.stderr, flush=True)


SANDBOX_NAME = "my-assistant"
EXEC_TIMEOUT_SECONDS = 600
STATUS_TIMEOUT_SECONDS = 10

# The OpenClaw agent at `--agent main` is a heartbeat-driven autonomous agent,
# not a stateless chat model. Its bundled AGENTS.md explicitly tells it to
# respond with the sentinel "HEARTBEAT_OK" for casual banter (e.g. one-word
# greetings), since the same surface that handles user messages also handles
# heartbeat polls. Without context, the agent can't tell a NemoClaw Client
# chat from a heartbeat poll.
#
# This prefix is prepended to each user message so the agent treats it as a
# direct operator chat that warrants a real reply. Keep it short and visible —
# a learner inspecting the agent's input should see exactly what we sent.
_CHAT_FRAMING = (
    "[NemoClaw Client chat — direct operator message via chat UI. "
    "Please respond conversationally; do not emit HEARTBEAT_OK.] "
)

# When the agent ignores the framing and still emits HEARTBEAT_OK, the client
# UI surfaces an educational explanation instead of showing the bare sentinel.
HEARTBEAT_SENTINEL = "HEARTBEAT_OK"


def _find_nemoclaw_binary() -> Optional[str]:
    """Locate the nemoclaw binary across the install paths used by the workshop.

    Streamlit launched from JupyterLab may receive a stripped PATH, so we also
    probe the standard install locations directly.
    """
    found = shutil.which("nemoclaw")
    if found:
        return found
    candidates = (
        "/usr/local/bin/nemoclaw",
        "/usr/bin/nemoclaw",
        os.path.expanduser("~/.local/bin/nemoclaw"),
        os.path.expanduser("~/.npm-global/bin/nemoclaw"),
        "/home/workbench/.local/bin/nemoclaw",
        "/home/workbench/.npm-global/bin/nemoclaw",
    )
    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


_NEMOCLAW_BIN = _find_nemoclaw_binary()


def _check_nemoclaw_cli() -> bool:
    return _NEMOCLAW_BIN is not None


def _check_sandbox_running(sandbox: str = SANDBOX_NAME, timeout: int = STATUS_TIMEOUT_SECONDS) -> bool:
    """Return True if `nemoclaw <sandbox> status` reports the sandbox as ready.

    Readiness is signaled by a `Phase: Ready` line in the status output. The
    `Connected:` field reflects whether an interactive `nemoclaw connect`
    session is active and is not a usability signal.

    Diagnostic notes about why detection failed are written to stderr and
    cached on `LAST_DETECT_ERROR` so the UI can surface them.
    """
    global LAST_DETECT_ERROR
    LAST_DETECT_ERROR = None

    if not _NEMOCLAW_BIN:
        LAST_DETECT_ERROR = "nemoclaw binary not found on PATH or in standard locations"
        _log(LAST_DETECT_ERROR)
        return False
    try:
        result = subprocess.run(
            [_NEMOCLAW_BIN, sandbox, "status"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        LAST_DETECT_ERROR = f"`nemoclaw {sandbox} status` timed out after {timeout}s"
        _log(LAST_DETECT_ERROR)
        return False
    except OSError as e:
        LAST_DETECT_ERROR = f"failed to invoke nemoclaw: {e}"
        _log(LAST_DETECT_ERROR)
        return False

    combined = _ANSI_RE.sub("", (result.stdout or "") + "\n" + (result.stderr or ""))

    if result.returncode != 0:
        snippet = combined[:200].replace("\n", " | ")
        LAST_DETECT_ERROR = f"`nemoclaw status` exited {result.returncode}: {snippet}"
        _log(LAST_DETECT_ERROR)
        return False

    if not _PHASE_READY_RE.search(combined):
        snippet = combined[:200].replace("\n", " | ")
        LAST_DETECT_ERROR = (
            f"`nemoclaw status` succeeded but no `Phase: Ready` line found. "
            f"First 200 chars: {snippet!r}"
        )
        _log(LAST_DETECT_ERROR)
        return False

    return True


def _send_via_nemoclaw_cli(prompt: str, sandbox: str = SANDBOX_NAME, timeout: int = EXEC_TIMEOUT_SECONDS) -> dict:
    """Send a prompt to the in-sandbox OpenClaw agent and return a structured result.

    Returns:
        {
          "text": str,           # the agent's response text
          "meta": dict | None,   # token usage, model, duration when --json succeeds
          "error": str | None,   # error message if the call failed
        }
    """
    if not _NEMOCLAW_BIN:
        return {"text": "[NemoClaw CLI not found]", "meta": None, "error": "nemoclaw binary missing"}

    # `nemoclaw exec` rejects argv entries containing newlines/CRs (gRPC
    # InvalidArgument). Flatten them — multi-line pastes from the chat input
    # are valid LLM input but invalid for this transport.
    sanitized_prompt = prompt.replace("\r", " ").replace("\n", " ")
    framed_prompt = _CHAT_FRAMING + sanitized_prompt
    cmd = [
        _NEMOCLAW_BIN, sandbox, "exec",
        "--",
        "openclaw", "agent", "--agent", "main", "--json", "-m", framed_prompt,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {
            "text": f"[Sandbox agent timed out after {timeout}s]",
            "meta": None,
            "error": "timeout",
        }
    except OSError as e:
        return {"text": f"[Failed to invoke nemoclaw: {e}]", "meta": None, "error": str(e)}

    if result.returncode != 0:
        error = (result.stderr or result.stdout or "Unknown error").strip()
        return {"text": f"[Sandbox agent error: {error}]", "meta": None, "error": error}

    stdout = (result.stdout or "").strip()
    try:
        data = _json.loads(stdout)
        result_data = data.get("result", {})
        payloads = result_data.get("payloads", [])
        text = payloads[0].get("text", "") if payloads else str(data)
        meta = result_data.get("meta")
        return {"text": text, "meta": meta, "error": None}
    except (ValueError, TypeError):
        return {"text": stdout, "meta": None, "error": None}


def create_nemoclaw_agent_fn(sandbox: str = SANDBOX_NAME) -> Callable[[str], dict]:
    """Return an agent_fn that sends prompts to the OpenClaw agent inside `sandbox`.

    The caller is expected to verify availability via `_check_nemoclaw_cli()`
    and `_check_sandbox_running()` before using this function — the wrapper
    does not silently fall back to a mock so callers see real errors.
    """
    def agent_fn(prompt: str) -> dict:
        return _send_via_nemoclaw_cli(prompt, sandbox=sandbox)

    return agent_fn
