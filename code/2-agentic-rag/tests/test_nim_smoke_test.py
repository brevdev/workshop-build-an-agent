"""Exercise smoke-test failure modes without downloading a model."""

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nim_smoke_test import smoke_test


class Response:
    def __init__(self, body, status=200):
        self.body = body
        self.status_code = status
        self.ok = status < 400
        self.text = json.dumps(body)

    def json(self):
        return self.body


def choice(message, finish_reason="stop"):
    return Response({"choices": [{"message": message, "finish_reason": finish_reason}]})


CALL = {
    "id": "call-verification", "type": "function",
    "function": {"name": "read_workshop_code", "arguments": "{}"},
}


class Session:
    def __init__(self, first=None, final=None, ready=200):
        self.first = first or choice({"role": "assistant", "content": None, "tool_calls": [copy.deepcopy(CALL)]}, "tool_calls")
        self.final = final
        self.ready = ready
        self.requests = []

    def get(self, url, **kwargs):
        return Response({}, self.ready)

    def post(self, url, **kwargs):
        payload = kwargs["json"]
        self.requests.append(copy.deepcopy(payload))
        if len(self.requests) == 1:
            return self.first
        tool_result = payload["messages"][-1]
        assert tool_result["role"] == "tool"
        assert tool_result["tool_call_id"] == CALL["id"]
        code = json.loads(tool_result["content"])["verification_code"]
        return self.final or choice({"role": "assistant", "content": code})


class SmokeTestTests(unittest.TestCase):
    def test_final_answer_must_use_new_tool_result_with_matching_id(self):
        session = Session()
        code = smoke_test("http://nim/v1", session)
        self.assertTrue(code.startswith("workshop-"))
        self.assertNotIn(code, json.dumps(session.requests[0]))
        self.assertEqual([r["tool_choice"] for r in session.requests], ["auto", "none"])

    def test_ready_is_not_a_chat_or_agent_success(self):
        session = Session(ready=503)
        with self.assertRaisesRegex(RuntimeError, "not ready"):
            smoke_test("http://nim/v1", session)
        self.assertEqual(session.requests, [])

    def test_original_auto_tool_choice_http_400_fails(self):
        session = Session(first=Response({"error": "auto tool choice requires --enable-auto-tool-choice"}, 400))
        with self.assertRaisesRegex(RuntimeError, "HTTP 400"):
            smoke_test("http://nim/v1", session)

    def test_plain_chat_without_a_tool_call_fails(self):
        session = Session(first=choice({"role": "assistant", "content": "Here is your code."}))
        with self.assertRaisesRegex(RuntimeError, "Expected one parsed tool call"):
            smoke_test("http://nim/v1", session)

    def test_truncation_is_not_a_passing_response(self):
        session = Session(first=choice({"content": "Thinking..."}, "length"))
        with self.assertRaisesRegex(RuntimeError, "output budget"):
            smoke_test("http://nim/v1", session)

    def test_unknown_tool_is_not_executed(self):
        call = copy.deepcopy(CALL)
        call["function"]["name"] = "delete_files"
        session = Session(first=choice({"tool_calls": [call]}))
        with self.assertRaisesRegex(RuntimeError, "unexpected tool"):
            smoke_test("http://nim/v1", session)
        self.assertEqual(len(session.requests), 1)

    def test_invented_final_answer_fails(self):
        session = Session(final=choice({"content": "workshop-made-up"}))
        with self.assertRaisesRegex(RuntimeError, "did not reproduce the tool result"):
            smoke_test("http://nim/v1", session)

    def test_visible_reasoning_markup_fails(self):
        session = Session(final=choice({"content": "<think>private reasoning</think>"}))
        with self.assertRaisesRegex(RuntimeError, "Unparsed reasoning"):
            smoke_test("http://nim/v1", session)


if __name__ == "__main__":
    unittest.main()
