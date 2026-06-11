"""The wire — a model client in pure stdlib (Exercise 1).

Module 1 used the `openai` SDK, which hid the HTTP request and response behind
`client.chat.completions.create(...)`. Here we make that call by hand with
`urllib.request` so you can see the literal JSON going over the wire — and so
the exact same file runs inside the Module 6 sandbox, where only Python and the
standard library are guaranteed (no pip installs).

Your job in Exercise 1: fill in the two TODOs in `chat()` below.
"""
from __future__ import annotations

import json
import socket
import ssl
import sys
import urllib.error
import urllib.request

from . import config


class ModelHTTPError(Exception):
    """The endpoint answered with an HTTP 4xx/5xx status."""

    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__("HTTP {}: {}".format(status, body))


class ModelConnectionError(Exception):
    """We could not reach the endpoint at all (DNS, refused, proxy denial, timeout)."""


def _ssl_context():
    """Default verified TLS, unless HERMES_TLS_INSECURE=1 (sandbox fallback only)."""
    if config.TLS_INSECURE:
        sys.stderr.write(
            "[client] WARNING: TLS verification disabled (HERMES_TLS_INSECURE=1). "
            "Only use this inside the sandbox if the gateway CA is missing.\n"
        )
        return ssl._create_unverified_context()
    return None  # urlopen uses the default verified context


def chat(messages, tools=None, temperature=None, max_tokens=None) -> dict:
    """POST one chat-completion request and return a normalized assistant message.

    The returned dict has the SAME shape Module 1's `call_llm` produced:
        {"role": "assistant", "content": str | None,
         "tool_calls": [{"id", "type": "function",
                         "function": {"name", "arguments"}}]}   # only if tools were called
    `arguments` is a JSON *string*, exactly as the model emits it.
    """
    if temperature is None:
        temperature = config.TEMPERATURE
    if max_tokens is None:
        max_tokens = config.MAX_TOKENS

    # ── TODO: Exercise 1.1 — build the request payload ──
    # The payload is the JSON body of the request. Module 1 handed these same
    # fields to the SDK; here you assemble the dict yourself. Add a "tools" key
    # ONLY when tools were passed in (an empty list confuses some servers).
    payload = {
        "model": ...,           # Hint: config.MODEL_NAME
        "messages": ...,        # Hint: the messages list, verbatim — this IS the context window
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload[...] = ...      # Hint: key "tools", value tools — the same schema list from Module 1

    url = config.MODEL_URL.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    # Attach the key ONLY if we have one. In the sandbox it is empty and the
    # gateway injects credentials — so we must not send a bogus header.
    if config.API_KEY:
        headers["Authorization"] = "Bearer " + config.API_KEY

    # ── TODO: Exercise 1.2 — send the request and parse the reply ──
    # Encode the payload as JSON bytes, POST it, and JSON-decode the response.
    # The try/except below already turns failures into friendly exceptions.
    data = ...                  # Hint: json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=config.REQUEST_TIMEOUT, context=_ssl_context()) as resp:
            body = ...          # Hint: json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 4xx/5xx: the body usually carries a useful JSON error. Read it before raising.
        detail = e.read().decode("utf-8", "replace")[:400]
        raise ModelHTTPError(e.code, detail)
    except urllib.error.URLError as e:
        # No HTTP response at all. Inside the sandbox a denied CONNECT lands here.
        raise ModelConnectionError("cannot reach {}: {}".format(config.MODEL_URL, e.reason))
    except (TimeoutError, socket.timeout):
        raise ModelConnectionError("timed out after {}s".format(config.REQUEST_TIMEOUT))

    message = body["choices"][0]["message"]   # the raw wire shape the SDK hid from you

    # Normalize into Module 1's dict. Tool calls (if any) get copied verbatim.
    # (Provided — study it: this is exactly what the SDK did for you before.)
    result = {"role": "assistant", "content": message.get("content")}
    tool_calls = message.get("tool_calls")
    if tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.get("id"),
                "type": "function",
                "function": {
                    "name": tc["function"]["name"],
                    "arguments": tc["function"].get("arguments", "{}"),
                },
            }
            for tc in tool_calls
        ]
        result["content"] = None
    return result


def strip_reasoning(text) -> str:
    """Drop Nemotron's <think>...</think> block so the user sees only the answer.

    The transcript keeps the raw content; we strip only at the display boundary.
    """
    if not text:
        return ""
    return text.split("</think>")[-1].strip()
