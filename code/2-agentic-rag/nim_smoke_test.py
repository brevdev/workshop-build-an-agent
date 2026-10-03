"""Check local NIM readiness, automatic tool calling, and use of a real tool result."""

import argparse
import json
import secrets
import sys

import requests

MODEL = "nvidia/nemotron-3-nano"
TOOL = {
    "type": "function",
    "function": {
        "name": "read_workshop_code",
        "description": "Read the current workshop verification code. Only this tool knows the code.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}


def completion(session: requests.Session, base_url: str, messages: list[dict], tool_choice: str) -> dict:
    response = session.post(
        base_url + "/chat/completions",
        json={
            "model": MODEL, "messages": messages, "tools": [TOOL],
            "tool_choice": tool_choice, "temperature": 0, "max_tokens": 2048,
        },
        timeout=(10, 180),
    )
    if not response.ok:
        raise RuntimeError(
            f"NIM returned HTTP {response.status_code}: {response.text[:1000]}. "
            "For automatic-tool-choice errors, launch with --enable-auto-tool-choice "
            "--tool-call-parser qwen3_coder --reasoning-parser nemotron_v3."
        )
    choices = response.json().get("choices", [])
    if not choices or choices[0].get("finish_reason") == "length":
        raise RuntimeError("NIM returned no complete choice (or exhausted its output budget); the smoke test did not pass.")
    return choices[0]["message"]


def check_visible_content(message: dict) -> None:
    content = message.get("content") or ""
    if any(marker in content for marker in ("<think>", "</think>", "<tool_call>")):
        raise RuntimeError("Unparsed reasoning/tool markup reached content. Check the model-specific parser flags.")


def smoke_test(base_url: str, session: requests.Session) -> str:
    base_url = base_url.rstrip("/")
    ready = session.get(base_url + "/health/ready", timeout=10)
    if ready.status_code != 200:
        raise RuntimeError(f"NIM is not ready (HTTP {ready.status_code}); check docker logs nemotron and retry after loading.")
    messages = [
        {"role": "system", "content": "Use the supplied tool to read the current verification code. After receiving its result, reply with that code only."},
        {"role": "user", "content": "What is the current workshop verification code? Call read_workshop_code to find out."},
    ]
    first = completion(session, base_url, messages, "auto")
    check_visible_content(first)
    calls = first.get("tool_calls") or []
    if len(calls) != 1:
        raise RuntimeError(f"Expected one parsed tool call; got {len(calls)}. A plain chat response is not a passing agent test.")
    call = calls[0]
    if call.get("type") != "function" or call.get("function", {}).get("name") != "read_workshop_code" or not call.get("id"):
        raise RuntimeError("The model returned an unexpected tool or no tool-call ID.")
    if json.loads(call["function"].get("arguments", "")) != {}:
        raise RuntimeError("The verification tool takes no arguments.")
    # Generate only after the call: the model cannot know this value from its prompt.
    code = "workshop-" + secrets.token_hex(8)
    messages.extend([
        {"role": "assistant", "content": first.get("content") or "", "tool_calls": calls},
        {"role": "tool", "tool_call_id": call["id"], "content": json.dumps({"verification_code": code})},
    ])
    final = completion(session, base_url, messages, "none")
    check_visible_content(final)
    if final.get("tool_calls") or (final.get("content") or "").strip() != code:
        raise RuntimeError("The final answer did not reproduce the tool result exactly; the round trip did not pass.")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://nemotron:8000/v1")
    args = parser.parse_args()
    try:
        with requests.Session() as session:
            code = smoke_test(args.base_url, session)
    except (requests.RequestException, RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(f"NIM smoke test failed: {exc}", file=sys.stderr)
        return 1
    print("PASS: readiness, automatic tool call, matching tool-call ID, and final answer from the tool result.")
    print(f"Verification code: {code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
