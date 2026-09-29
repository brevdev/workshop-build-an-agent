"""Normalize gateway replies from the workshop's pinned OpenClaw 2026.5.20.

The gateway CLI returns ``result.payloads`` in output order. Payloads can carry
``text``, ``mediaUrl(s)`` and ``isError``; a zero exit status alone is not success.
See that release's src/commands/agent-via-gateway.ts and
src/agents/pi-embedded-runner/types.ts. Bare embedded/local fallback output is
not a gateway result and must not silently replace the agent being evaluated.
"""

import json


def normalize_openclaw_response(stdout: str) -> dict:
    """Return the complete reply, or an explicit error for an ungradable run.

    Keep all textual payloads in order, including text before/after an error.
    Media references remain visible, but this text-only suite cannot assess
    their contents. Never turn raw JSON, missing output or a partial failure
    into an apparently successful answer.
    """
    parts, errors = [], []
    meta = None

    def result():
        text = "\n\n".join(parts)
        error = " ".join(dict.fromkeys(errors)) or None
        if error:
            notice = f"[Agent response error: {error}]"
            text = f"{text}\n\n{notice}" if text else notice
        return {"text": text, "meta": meta, "error": error}

    try:
        data = json.loads(stdout)
    except (ValueError, TypeError):
        errors.append("OpenClaw returned invalid JSON.")
        return result()
    if not isinstance(data, dict) or not isinstance(data.get("result"), dict):
        errors.append("OpenClaw returned no valid gateway result object.")
        return result()

    reply = data["result"]
    meta = reply.get("meta")
    if meta is not None and not isinstance(meta, dict):
        meta = None
        errors.append("OpenClaw returned invalid result metadata.")
    if "status" in data and data["status"] != "ok":
        errors.append("OpenClaw did not report a successful gateway run.")
    if meta and (meta.get("error") or meta.get("aborted")):
        errors.append("OpenClaw reported a failed or aborted run.")

    payloads = reply.get("payloads")
    if not isinstance(payloads, list) or not payloads:
        errors.append("OpenClaw returned no nonempty payload list.")
        return result()

    for index, payload in enumerate(payloads, 1):
        if not isinstance(payload, dict):
            errors.append(f"OpenClaw payload {index} is not an object.")
            continue
        if "isError" in payload and not isinstance(payload["isError"], bool):
            errors.append(f"OpenClaw payload {index} has an invalid error flag.")
        elif payload.get("isError"):
            errors.append(f"OpenClaw payload {index} reports an error.")

        text = payload.get("text")
        if "text" in payload and not isinstance(text, str):
            errors.append(f"OpenClaw payload {index} has invalid text.")
        elif text:
            parts.append(text)

        media = payload.get("mediaUrl")
        media_list = payload.get("mediaUrls", [])
        if (media is not None and not isinstance(media, str)) or not isinstance(media_list, list) or any(
            not isinstance(url, str) for url in media_list
        ):
            errors.append(f"OpenClaw payload {index} has invalid media references.")
        else:
            references = [url for url in [media, *media_list] if url]
            parts.extend(f"MEDIA:{url}" for url in references)
            if references:
                errors.append("The text-only safety suite cannot assess media contents.")
        if not any(key in payload for key in ("text", "mediaUrl", "mediaUrls")) and not payload.get("isError"):
            errors.append(f"OpenClaw payload {index} has no reply content.")

    if not any(part.strip() for part in parts):
        errors.append("OpenClaw returned no answer.")
    return result()
