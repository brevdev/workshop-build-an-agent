"""
NemoClaw Agent Wrapper — Module 6

Bridges the sandboxed OpenClaw agent (running inside a NemoClaw OpenShell
sandbox) to the exercise `agent_fn(prompt) -> dict` interface used by
`nemoclaw_client.py`.

Transport: `nemoclaw <sandbox> exec -- openclaw agent --agent main
[--session-id <id>] --json -m "<prompt>"`. The in-sandbox `openclaw` produces
the same `--json` output shape as the host-side binary, so the JSON parsing
mirrors `openclaw_wrapper`.

Usage:
    from nemoclaw_wrapper import create_nemoclaw_agent_fn

    agent_fn = create_nemoclaw_agent_fn()
    result = agent_fn("Hello")
    # result = {"text": "...", "meta": {...}, "error": None}
"""

import os
import re
import shutil
import subprocess
import sys
import uuid
from typing import Callable, Optional

from openclaw_response import normalize_openclaw_response


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
# This prefix is prepended to each message so the agent replies instead of
# treating it as a poll. It names the transport only. It must not claim who
# sent the message or what authority they have: the safety suite sends red-team
# probes through this path, and an "operator" label would present attacker text
# as trusted. Keep it short and visible — a learner inspecting the agent's input
# should see exactly what we sent.
_CHAT_FRAMING = (
    "[Message sent through the NemoClaw Client. This is not a heartbeat poll: "
    "reply to it instead of answering HEARTBEAT_OK.] "
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


def _refresh_nemoclaw_binary() -> Optional[str]:
    """Search for the nemoclaw binary again and cache the result.

    The client imports this module once, so a NemoClaw installed or moved after
    the page opened is only found by searching again.
    """
    global _NEMOCLAW_BIN
    _NEMOCLAW_BIN = _find_nemoclaw_binary()
    return _NEMOCLAW_BIN


def _nemoclaw_bin() -> Optional[str]:
    """Return the cached binary, searching again while it has not been found."""
    return _NEMOCLAW_BIN or _refresh_nemoclaw_binary()


def _check_nemoclaw_cli() -> bool:
    return _nemoclaw_bin() is not None


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

    nemoclaw_bin = _nemoclaw_bin()
    if not nemoclaw_bin:
        LAST_DETECT_ERROR = "nemoclaw binary not found on PATH or in standard locations"
        _log(LAST_DETECT_ERROR)
        return False
    try:
        result = subprocess.run(
            [nemoclaw_bin, sandbox, "status"],
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


def _send_via_nemoclaw_cli(
    prompt: str,
    sandbox: str = SANDBOX_NAME,
    timeout: int = EXEC_TIMEOUT_SECONDS,
    session_id: Optional[str] = None,
) -> dict:
    """Send a prompt to the in-sandbox OpenClaw agent and return a structured result.

    Without `session_id` the prompt joins the agent's main session, which keeps
    its history (the chat client and `openclaw tui` share it). A new
    `session_id` starts the prompt in an empty conversation.

    Returns:
        {
          "text": str,           # the agent's response text
          "meta": dict | None,   # token usage, model, duration when --json succeeds
          "error": str | None,   # error message if the call failed
        }
    """
    nemoclaw_bin = _nemoclaw_bin()
    if not nemoclaw_bin:
        return {"text": "[NemoClaw CLI not found]", "meta": None, "error": "nemoclaw binary missing"}

    # `nemoclaw exec` rejects argv entries containing newlines/CRs (gRPC
    # InvalidArgument). Flatten them — multi-line pastes from the chat input
    # are valid LLM input but invalid for this transport.
    sanitized_prompt = prompt.replace("\r", " ").replace("\n", " ")
    framed_prompt = _CHAT_FRAMING + sanitized_prompt
    cmd = [
        nemoclaw_bin, sandbox, "exec",
        "--",
        "openclaw", "agent", "--agent", "main",
    ]
    if session_id:
        cmd += ["--session-id", session_id]
    cmd += ["--json", "-m", framed_prompt]

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

    return normalize_openclaw_response(result.stdout)


def create_nemoclaw_agent_fn(sandbox: str = SANDBOX_NAME, isolate_sessions: bool = True) -> Callable[[str], dict]:
    """Return an agent_fn that sends prompts to the OpenClaw agent inside `sandbox`.

    By default every prompt starts a fresh agent session, so earlier probes and
    chats cannot change the answer and evaluation results do not depend on run
    order. The chat client passes ``isolate_sessions=False`` to keep one
    continuing conversation in the agent's main session.

    The caller is expected to verify availability via `_check_nemoclaw_cli()`
    and `_check_sandbox_running()` before using this function — the wrapper
    does not silently fall back to a mock so callers see real errors.
    """
    def agent_fn(prompt: str) -> dict:
        session_id = str(uuid.uuid4()) if isolate_sessions else None
        return _send_via_nemoclaw_cli(prompt, sandbox=sandbox, session_id=session_id)

    return agent_fn
