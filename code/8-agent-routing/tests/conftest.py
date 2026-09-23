import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest

class FakeResponse:
    def __init__(self, content, in_tok=100, out_tok=20):
        self.content = content
        self.usage_metadata = {"input_tokens": in_tok, "output_tokens": out_tok}
        self.tool_calls = []

class FakeChat:
    """Stands in for ChatNVIDIA: returns queued responses, records prompts."""
    def __init__(self, responses):
        self.responses = list(responses); self.calls = []
    def invoke(self, messages):
        self.calls.append(messages)
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]

@pytest.fixture
def fake_chat():
    return lambda *responses: FakeChat([FakeResponse(r) if isinstance(r, str) else r for r in responses])
