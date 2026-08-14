"""Routing Client backend tests. The server is a WINDOW, not a wizard: everything
asserted here is about what it renders, in what order, and how it degrades -- never
about a routing decision, because the server makes none. Routing belongs to
routing_lab.py (tests/test_lab_logic.py).

Two gateway-receipt tests ride along at the bottom. They exercise the LAB's
gateway_call with the socket stubbed out; the client reads that receipt, so its
shape is pinned here next to the reader.
"""
import importlib.util, io, json, pathlib
import pytest
from fastapi.testclient import TestClient

import routing_client.server as srv
from routing_lab_answers_import_helper import answers
from constants import EFFICIENT_MODEL, GATEWAY_BASE_URL, STRATEGIES, STRONG_MODEL

# The eight keys bill_call/gateway_call promise; the client indexes them by name.
RECEIPT_KEYS = {"model", "input_tokens", "output_tokens", "cost", "latency",
                "counterfactual_cost", "why", "router_tax"}


def _client(monkeypatch, fake_chat):
    """The seam: the server renders the ANSWERS module with both model constructors
    faked, so no test here opens a socket or spends a token."""
    monkeypatch.setattr(srv, "_load_lab", lambda: answers)
    monkeypatch.setattr(answers, "build_model_pool",
                        lambda: {"strong": fake_chat("big"), "efficient": fake_chat("small")})
    monkeypatch.setattr(answers, "build_classifier", lambda: fake_chat("COMMODITY"))
    return TestClient(srv.app)


def _blank_lab():
    """The learner's own file, every TODO still unfilled."""
    path = pathlib.Path(srv.__file__).resolve().parents[1] / "routing_lab.py"
    spec = importlib.util.spec_from_file_location("blank_lab", path)
    blank = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(blank)
    return blank


def _events(body):
    """Parse an SSE body into [(event, data), ...] in arrival order."""
    parsed = []
    for block in body.split("\n\n"):
        name = data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                name = line[len("event: "):]
            elif line.startswith("data: "):
                data = line[len("data: "):]
        if name:
            parsed.append((name, json.loads(data) if data else None))
    return parsed


# --------------------------------------------------------------- /api/status ---

def test_status_reports_unlocks(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    body = c.get("/api/status").json()
    assert body["unlocks"] == {"ex1": True, "ex2": True, "ex3": True, "ex5": True}
    assert set(body) >= {"unlocks", "gateway_alive", "key_present", "sdk_available"}


def test_status_probes_a_copy_never_the_module_serving_queries(monkeypatch, fake_chat):
    """probe_unlocks swaps a module global while it runs, so it must never be pointed
    at the object answering live queries. Proof: a stand-in installed on the live
    module is not the one the probe calls, and the live module comes back untouched."""
    c = _client(monkeypatch, fake_chat)
    touched = []
    monkeypatch.setattr(answers, "route_call", lambda *a, **kw: touched.append(1))
    monkeypatch.setattr(answers, "SENTINEL", "live", raising=False)

    body = c.get("/api/status").json()

    assert body["unlocks"]["ex2"] is True     # the probe did run Ex2's blank...
    assert touched == []                      # ...on its own copy, not this module's
    assert answers.SENTINEL == "live"


def test_status_survives_a_lab_that_will_not_import(monkeypatch):
    """A half-typed routing_lab.py is the most likely state of the file this thing
    re-reads every request. Locked is fine; a 500 with no body is not."""
    def half_typed():
        raise SyntaxError("invalid syntax (routing_lab.py, line 47)")
    monkeypatch.setattr(srv, "_load_lab", half_typed)
    body = TestClient(srv.app).get("/api/status").json()
    assert body["unlocks"] == {"ex1": False, "ex2": False, "ex3": False, "ex5": False}
    assert "SyntaxError" in body["lab_error"]


def test_routing_lab_module_env_selects_another_lab_file(monkeypatch):
    """How a demo (and the answer-key smoke test) points the client at the completed
    implementation without editing the learner's copy."""
    monkeypatch.setenv("ROUTING_LAB_MODULE", "routing_lab.answers")
    lab = srv._load_lab()
    assert pathlib.Path(lab.__file__).name == "routing_lab.answers.py"
    assert lab.probe_unlocks(lab) == {"ex1": True, "ex2": True, "ex3": True, "ex5": True}


# ---------------------------------------------------------------- /api/query ---

def test_query_streams_decision_then_receipt(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    r = c.post("/api/query", json={"text": "reformat this", "strategy": "manual_classifier"})
    events = [l for l in r.text.splitlines() if l.startswith("event:")]
    assert events[0] == "event: route_decision"
    assert "event: receipt" in events and "event: answer" in events

    named = dict(_events(r.text))
    assert set(named["route_decision"]) == {"lane", "model", "why"}
    assert named["route_decision"]["lane"] == "efficient"        # the lab classified it
    assert RECEIPT_KEYS <= set(named["receipt"])
    assert named["receipt"]["counterfactual_saved"] == pytest.approx(
        named["receipt"]["counterfactual_cost"] - named["receipt"]["cost"])
    assert named["answer"]["text"] == "small"


def test_locked_strategy_yields_error(monkeypatch):
    """Every TODO unfilled: the first blank the strategy reaches is Exercise 1a's
    model pool, and that is the one the banner must name."""
    monkeypatch.setattr(srv, "_load_lab", _blank_lab)
    r = TestClient(srv.app).post("/api/query",
                                 json={"text": "x", "strategy": "manual_classifier"})
    assert "event: error" in r.text
    message = dict(_events(r.text))["error"]["message"]
    assert message == "Locked: Exercise 1a — fill that TODO in routing_lab.py and retry."


def test_locked_error_names_the_blank_actually_hit(monkeypatch, fake_chat):
    """Exercise 1 filled, Exercise 2 not: the banner moves on with the learner."""
    c = _client(monkeypatch, fake_chat)

    def unfilled(*a, **kw):
        raise NotImplementedError("Exercise 2b")
    monkeypatch.setattr(answers, "route_call", unfilled)

    r = c.post("/api/query", json={"text": "x", "strategy": "manual_classifier"})
    assert dict(_events(r.text))["error"]["message"] == (
        "Locked: Exercise 2b — fill that TODO in routing_lab.py and retry.")


def test_unlabelled_blank_does_not_render_an_empty_lock(monkeypatch, fake_chat):
    """A bare NotImplementedError() has no exercise to name. "Locked:  — fill that
    TODO" pointing at nothing is worse than plain error text, so it must not happen."""
    c = _client(monkeypatch, fake_chat)

    def unlabelled(*a, **kw):
        raise NotImplementedError
    monkeypatch.setattr(answers, "route_call", unlabelled)

    message = dict(_events(c.post("/api/query", json={
        "text": "x", "strategy": "manual_classifier"}).text))["error"]["message"]
    assert not message.startswith("Locked:")
    assert "routing_lab.py" in message


def test_unknown_strategy_is_an_error_event_not_a_broken_stream(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    r = c.post("/api/query", json={"text": "x", "strategy": "teleport"})
    assert dict(_events(r.text))["error"]["message"].startswith("ValueError:")


# ----------------------------------------------------------------- /api/race ---

def _canned(cost, model, tax=0.0, passed=True, n=12):
    return [{"id": f"t{i}", "kind": "commodity", "passed": passed, "cost": cost / n,
             "latency": 0.1, "models": {model: 1}, "router_tax": tax / n} for i in range(n)]


def test_race_rows_stream_in_canonical_strategy_order(monkeypatch, fake_chat):
    """routing_verdict reads the routed row out of dict insertion order, so the race
    must feed it constants.STRATEGIES order whatever order the chips were clicked in
    -- otherwise the receipt compares against whichever strategy the UI listed first."""
    c = _client(monkeypatch, fake_chat)
    canned = {"strong_only": _canned(10.0, STRONG_MODEL),
              "manual_classifier": _canned(1.0, EFFICIENT_MODEL, tax=0.1),
              "switchyard_stage": _canned(2.0, EFFICIENT_MODEL)}
    monkeypatch.setattr(answers, "run_suite", lambda strategy, bill=None: canned[strategy])

    r = c.post("/api/race", json={"strategies": ["switchyard_stage", "manual_classifier",
                                                 "strong_only"]})
    events = _events(r.text)
    assert [d["strategy"] for name, d in events if name == "race_row"] == [
        "strong_only", "manual_classifier", "switchyard_stage"]

    receipt = next(d["receipt"] for name, d in events if name == "race_receipt")
    # manual_classifier outranks switchyard_stage in STRATEGIES, so it is the routed row.
    assert "$1.00 vs $10.00" in receipt


def test_race_rejects_an_unsupported_strategy_before_spending_a_token(monkeypatch, fake_chat):
    """`gateway` is a headline strategy and a member of STRATEGIES, but run_suite
    raises on it -- and canonical order puts it last, so discovering that by running
    it would mean two suites (~24 live calls) already paid for, then an error and no
    verdict. The race must refuse before the first call."""
    c = _client(monkeypatch, fake_chat)
    calls = []
    monkeypatch.setattr(answers, "run_suite", lambda *a, **kw: calls.append(a))

    r = c.post("/api/race", json={"strategies": ["strong_only", "manual_classifier", "gateway"]})

    message = dict(_events(r.text))["error"]["message"]
    assert "gateway" in message                                  # names the offender
    assert "strong_only, efficient_only, manual_classifier, switchyard_stage" in message
    assert calls == []                                           # nothing was spent
    assert "race_row" not in r.text


def test_race_rejects_an_empty_selection(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    calls = []
    monkeypatch.setattr(answers, "run_suite", lambda *a, **kw: calls.append(a))
    r = c.post("/api/race", json={"strategies": []})
    assert "no strategies selected" in dict(_events(r.text))["error"]["message"]
    assert calls == []


def test_race_collapses_a_duplicated_strategy_to_one_row(monkeypatch, fake_chat):
    """A double-clicked chip must not buy the same suite twice."""
    c = _client(monkeypatch, fake_chat)
    calls = []
    monkeypatch.setattr(answers, "run_suite",
                        lambda strategy, bill=None: calls.append(strategy) or _canned(10.0, STRONG_MODEL))

    r = c.post("/api/race", json={"strategies": ["strong_only", "strong_only"]})

    assert calls == ["strong_only"]
    assert [name for name, _ in _events(r.text)] == ["race_row", "race_receipt"]


def test_race_renders_the_receipt_it_already_paid_for_before_reporting_the_break(monkeypatch, fake_chat):
    """Defense in depth: if a suite blows up mid-race, the strategies that finished
    were still charged for, so their verdict ships before the error does."""
    c = _client(monkeypatch, fake_chat)
    canned = {"strong_only": _canned(10.0, STRONG_MODEL),
              "manual_classifier": _canned(1.0, EFFICIENT_MODEL, tax=0.1)}

    def flaky(strategy, bill=None):
        if strategy not in canned:
            raise RuntimeError("upstream 503")
        return canned[strategy]
    monkeypatch.setattr(answers, "run_suite", flaky)

    r = c.post("/api/race", json={"strategies": ["strong_only", "manual_classifier",
                                                 "switchyard_stage"]})
    events = _events(r.text)

    assert [name for name, _ in events] == ["race_row", "race_row", "race_receipt", "error"]
    assert "$1.00 vs $10.00" in events[2][1]["receipt"]      # the two that finished
    assert events[3][1]["message"] == "RuntimeError: upstream 503"


def test_race_reports_a_locked_suite_instead_of_dying_mid_stream(monkeypatch):
    monkeypatch.setattr(srv, "_load_lab", _blank_lab)
    r = TestClient(srv.app).post("/api/race", json={"strategies": ["strong_only"]})
    assert "Exercise" in dict(_events(r.text))["error"]["message"]


# ------------------------------------------------- the lab's gateway receipt ---
# Exercise 4 answers out of process, so its receipt is assembled from the gateway's
# JSON rather than from a chat client. Same eight keys, or the client's receipt log
# and race rows quietly lose a column. Stub the opener: no gateway, no network.

class _FakeOpener:
    def __init__(self, body):
        self.body, self.requests = body, []

    def open(self, req, timeout=None):
        self.requests.append(req)
        return io.BytesIO(json.dumps(self.body).encode())


def _gateway_body(served_by, prompt=100, completion=20):
    return {"model": served_by, "usage": {"prompt_tokens": prompt, "completion_tokens": completion},
            "choices": [{"message": {"content": "42"}}]}


def test_gateway_receipt_carries_every_key_the_client_reads(monkeypatch):
    opener = _FakeOpener(_gateway_body(EFFICIENT_MODEL))
    monkeypatch.setattr(answers, "_local_opener", lambda: opener)
    bill = answers.RunningBill()

    text, receipt = answers.gateway_call("2 hours in minutes?", bill)

    assert text == "42"
    assert set(receipt) == RECEIPT_KEYS
    assert receipt["model"] == EFFICIENT_MODEL           # attribution: the UPSTREAM id
    assert (receipt["input_tokens"], receipt["output_tokens"]) == (100, 20)
    assert receipt["cost"] == pytest.approx(answers._price(EFFICIENT_MODEL,
                                                           {"input_tokens": 100, "output_tokens": 20}))
    assert receipt["counterfactual_cost"] == pytest.approx(answers._price(
        STRONG_MODEL, {"input_tokens": 100, "output_tokens": 20}))
    assert receipt["router_tax"] == 0.0                  # the judge spends server-side
    assert bill.total_cost == pytest.approx(receipt["cost"])
    assert opener.requests[0].full_url == f"{GATEWAY_BASE_URL}/chat/completions"


def test_gateway_prices_an_unpriced_upstream_model_at_the_efficient_tier(monkeypatch):
    """The gateway can name a model PRICING has never heard of (a local NIM, Ex4b, or
    an upstream rename). Bill it at the open tier rather than crashing the receipt --
    and keep reporting the id it actually reported."""
    opener = _FakeOpener(_gateway_body("meta/some-local-nim-8b"))
    monkeypatch.setattr(answers, "_local_opener", lambda: opener)
    bill = answers.RunningBill()

    _, receipt = answers.gateway_call("hello", bill)

    assert receipt["model"] == "meta/some-local-nim-8b"
    assert receipt["cost"] == pytest.approx(answers._price(EFFICIENT_MODEL,
                                                           {"input_tokens": 100, "output_tokens": 20}))
    assert list(bill.by_model) == [EFFICIENT_MODEL]
