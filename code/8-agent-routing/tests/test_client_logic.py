"""Routing Client backend tests. The server is a WINDOW, not a wizard: everything
asserted here is about what it renders, in what order, and how it degrades -- never
about a routing decision, because the server makes none. Routing belongs to
routing_lab.py (tests/test_lab_logic.py).

Two gateway-receipt tests ride along at the bottom. They exercise the LAB's
gateway_call with the socket stubbed out; the client reads that receipt, so its
shape is pinned here next to the reader.
"""
import importlib.util, io, json, pathlib, subprocess, types
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


class _FakeOpener:
    """Stands in for the lab's urllib opener: no gateway, no network. Serves both
    surfaces the client reads -- POST /chat/completions and GET /stats."""

    def __init__(self, body):
        self.body, self.requests = body, []

    def open(self, req, timeout=None):
        self.requests.append(req)
        return io.BytesIO(json.dumps(self.body).encode())


def _gateway_body(served_by, prompt=100, completion=20):
    return {"model": served_by, "usage": {"prompt_tokens": prompt, "completion_tokens": completion},
            "choices": [{"message": {"content": "42"}}]}


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


def test_status_carries_the_repo_root_the_key_banner_prints(monkeypatch, fake_chat):
    """The missing-key banner tells the learner which secrets.env to source. It used
    to hardcode /project (true only inside the Workbench container), so the path now
    comes from the server, which is on the same filesystem as their terminal."""
    c = _client(monkeypatch, fake_chat)
    root = pathlib.Path(c.get("/api/status").json()["repo_root"])
    assert root.is_absolute()
    assert (root / "code" / "8-agent-routing" / "routing_client").is_dir()


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


# The lane is the ONE thing the server derives rather than forwards, so all three of
# its arms are pinned. It is a mapping of the receipt's model id, never a second
# opinion about routing: capable == the strong constant, efficient == the efficient
# one, local == anything else the gateway named.

def test_lane_is_capable_when_the_strong_model_answered(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    r = c.post("/api/query", json={"text": "x", "strategy": "strong_only"})
    decision = dict(_events(r.text))["route_decision"]
    assert (decision["lane"], decision["model"]) == ("capable", STRONG_MODEL)


def test_gateway_lane_is_efficient_when_the_upstream_was_the_open_model(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    monkeypatch.setattr(answers, "_local_opener", lambda: _FakeOpener(_gateway_body(EFFICIENT_MODEL)))
    decision = dict(_events(c.post("/api/query", json={
        "text": "x", "strategy": "gateway"}).text))["route_decision"]
    assert (decision["lane"], decision["model"]) == ("efficient", EFFICIENT_MODEL)


def test_gateway_lane_is_local_when_the_upstream_is_a_model_no_constant_names(monkeypatch, fake_chat):
    """Ex4b's local NIM (and any upstream rename) comes back as an id PRICING has
    never heard of. The lab bills it at the open tier as a fallback -- that is a
    price, not an attribution, so it must not paint the commodity lane. It gets its
    own lane, and the receipt keeps showing the raw id the gateway reported."""
    c = _client(monkeypatch, fake_chat)
    monkeypatch.setattr(answers, "_local_opener",
                        lambda: _FakeOpener(_gateway_body("nvidia/nemotron-3-nano")))
    named = dict(_events(c.post("/api/query", json={"text": "x", "strategy": "gateway"}).text))
    assert named["route_decision"]["lane"] == "local"
    assert named["route_decision"]["model"] == "nvidia/nemotron-3-nano"
    assert named["receipt"]["model"] == "nvidia/nemotron-3-nano"


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


# ------------------------------------------------------------------ /api/gpu ---
# Ex4b's badge. The client polls this every 2s while gateway mode is on, so every
# way it can fail has to come back as a quiet {"available": false} -- a 500 here
# would toast the learner twice a second, and a hang would freeze the poll.

def _smi(monkeypatch, stdout=None, error=None):
    """Stand in for the nvidia-smi subprocess; record how it was invoked."""
    seen = []

    def run(argv, **kwargs):
        seen.append((argv, kwargs))
        if error is not None:
            raise error
        return types.SimpleNamespace(stdout=stdout, returncode=0)

    monkeypatch.setattr(srv.subprocess, "run", run)
    return seen


def test_gpu_reports_utilization_and_memory(monkeypatch):
    seen = _smi(monkeypatch, stdout="37 %, 1234 MiB\n")
    body = TestClient(srv.app).get("/api/gpu").json()
    assert body == {"available": True, "utilization_pct": 37, "memory_used_mb": 1234}
    argv, kwargs = seen[0]
    assert argv[:2] == ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used"]
    assert kwargs["timeout"] <= 5              # a wedged driver must not stall the poll


def test_gpu_still_reports_utilization_when_the_driver_has_no_memory_figure(monkeypatch):
    """Verbatim output from this workshop's GB10 box: unified memory, so memory.used
    reads [N/A] while utilization is a perfectly good number. The badge shows the
    utilization, so losing the whole panel over the other column is the wrong trade."""
    _smi(monkeypatch, stdout="0 %, [N/A]\n")
    assert TestClient(srv.app).get("/api/gpu").json() == {
        "available": True, "utilization_pct": 0, "memory_used_mb": None}


def test_gpu_reads_the_first_gpu_on_a_multi_gpu_box(monkeypatch):
    """One line per GPU. The badge is a liveness cue for the local-NIM lane, not a
    monitoring product: it reports GPU 0 rather than inventing an aggregate."""
    _smi(monkeypatch, stdout="12 %, 512 MiB\n88 %, 40960 MiB\n")
    body = TestClient(srv.app).get("/api/gpu").json()
    assert (body["utilization_pct"], body["memory_used_mb"]) == (12, 512)


@pytest.mark.parametrize("failure", [
    {"error": FileNotFoundError("nvidia-smi")},                 # no driver tools at all
    {"error": subprocess.TimeoutExpired("nvidia-smi", 2)},      # a wedged driver
    {"error": subprocess.CalledProcessError(9, "nvidia-smi")},  # ran, exited non-zero
    {"stdout": "No devices were found\n"},                      # ran, said nothing useful
    {"stdout": "[N/A], [N/A]\n"},                               # ran, no utilization figure
    {"stdout": ""},                                             # ran, said nothing at all
])
def test_gpu_reports_unavailable_on_every_failure(monkeypatch, failure):
    _smi(monkeypatch, **failure)
    assert TestClient(srv.app).get("/api/gpu").json() == {"available": False}


# ------------------------------------------------- the lab's gateway receipt ---
# Exercise 4 answers out of process, so its receipt is assembled from the gateway's
# JSON rather than from a chat client. Same eight keys, or the client's receipt log
# and race rows quietly lose a column.

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


# --------------------------------------------------------- /api/gateway_stats ---
# A gateway receipt's router_tax is structurally 0.0: the judge's tokens are spent
# server-side and never reach a completion's usage block. /v1/stats is where they
# are, so the client reads them THROUGH this server -- the browser must not have to
# reach a second origin to see the tax the module spends a whole exercise on.

def test_gateway_stats_serves_the_gateways_own_books(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    monkeypatch.setattr(srv, "_gateway_alive", lambda: True)
    stats = {"tiers": {"weak": {"total_tokens": 500, "token_pct": 58.0},
                       "strong": {"total_tokens": 362, "token_pct": 42.0}},
             "classifier": {"total_requests": 5, "total_tokens": {"total": 11940}},
             "routing_overhead": {"count": 5, "avg_ms": 1586.0}}
    opener = _FakeOpener(stats)
    monkeypatch.setattr(answers, "_local_opener", lambda: opener)

    body = c.get("/api/gateway_stats").json()

    assert body["available"] is True
    assert body["stats"] == stats                              # forwarded whole, nothing derived
    assert opener.requests[0] == f"{GATEWAY_BASE_URL}/stats"   # the gateway's meter, not ours


def test_gateway_stats_answers_json_when_nothing_is_listening(monkeypatch, fake_chat):
    """Polled while gateway mode is on, so a gateway that is not up is an ordinary
    state rather than an exception: JSON out, and the lab is never asked to open a
    socket that is going to time out."""
    c = _client(monkeypatch, fake_chat)
    monkeypatch.setattr(srv, "_gateway_alive", lambda: False)
    monkeypatch.setattr(answers, "gateway_stats",
                        lambda: pytest.fail("asked a gateway the probe said was down"))

    r = c.get("/api/gateway_stats")

    assert r.status_code == 503
    assert r.json()["available"] is False
    assert GATEWAY_BASE_URL in r.json()["error"]


def test_gateway_stats_reports_a_gateway_that_dies_between_probe_and_read(monkeypatch, fake_chat):
    c = _client(monkeypatch, fake_chat)
    monkeypatch.setattr(srv, "_gateway_alive", lambda: True)

    def gone():
        raise OSError("connection reset by peer")
    monkeypatch.setattr(answers, "gateway_stats", gone)

    r = c.get("/api/gateway_stats")

    assert r.status_code == 503
    assert r.json()["available"] is False
    assert "connection reset by peer" in r.json()["error"]
