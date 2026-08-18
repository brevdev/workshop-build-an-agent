"""Routing Client backend tests. The server is a WINDOW, not a wizard: everything
asserted here is about what it renders, in what order, and how it degrades -- never
about a routing decision, because the server makes none. Routing belongs to
routing_lab.py (tests/test_lab_logic.py).

Two gateway-receipt tests ride along at the bottom. They exercise the LAB's
gateway_call with the socket stubbed out; the client reads that receipt, so its
shape is pinned here next to the reader.
"""
import importlib.util, io, json, os, pathlib, subprocess, types
import pytest
from fastapi.testclient import TestClient

import routing_client.server as srv
from routing_lab_answers_import_helper import answers
from constants import EFFICIENT_MODEL, GATEWAY_BASE_URL, STRATEGIES, STRONG_MODEL

# The eight keys bill_call/gateway_call promise; the client indexes them by name.
RECEIPT_KEYS = {"model", "input_tokens", "output_tokens", "cost", "latency",
                "counterfactual_cost", "why", "router_tax"}


@pytest.fixture(autouse=True)
def hermetic_key(monkeypatch, tmp_path):
    """Every test runs with NO ambient key and _SECRETS_FILE pointed away from the
    real repo file: the key path is explicit in the tests that exercise it, and the
    rest must not depend on the machine they run on."""
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr(srv, "_SECRETS_FILE", tmp_path / "no-secrets.env")
    monkeypatch.setattr(srv, "_injected_key", None)


def _client(monkeypatch, fake_chat):
    """The seam: the server renders the ANSWERS module with both model constructors
    faked, so no test here opens a socket or spends a token."""
    monkeypatch.setattr(srv, "_load_lab", lambda: answers)
    monkeypatch.setattr(answers, "build_model_pool",
                        lambda: {"strong": fake_chat("big"), "efficient": fake_chat("small")})
    monkeypatch.setattr(answers, "build_classifier", lambda: fake_chat("COMMODITY"))
    return TestClient(srv.app)


def _blank_lab():
    """The learner's own file, every TODO still unfilled. On a working checkout that
    IS its state; in a learner's workspace it may be filled in (or half-typed), and
    a maintainer suite must not go red because somebody did the module -- so the
    tests that need blanks skip, with the reason, when none are left."""
    path = pathlib.Path(srv.__file__).resolve().parents[1] / "routing_lab.py"
    spec = importlib.util.spec_from_file_location("blank_lab", path)
    blank = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(blank)
    except Exception as exc:
        pytest.skip(f"routing_lab.py does not execute in this workspace ({exc!r}) — "
                    "blank-file rendering is pinned on a clean checkout")
    if any(blank.probe_unlocks(blank).values()):
        pytest.skip("routing_lab.py has been filled in — blank-file rendering is "
                    "pinned on a clean checkout")
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


# ------------------------------------------------------------- the key path ---
# A tile inherits the JupyterLab server's environment, and no learner terminal can
# export anything into THAT -- so the server reconciles NVIDIA_API_KEY with
# <repo_root>/secrets.env on every status poll and before every live query. These
# pin the reconciliation rules; srv._SECRETS_FILE is the seam (the autouse fixture
# points it at an absent tmp file, so each test writes exactly the file it means).

def test_key_falls_back_to_secrets_env(monkeypatch, fake_chat, tmp_path):
    secrets = tmp_path / "secrets.env"
    secrets.write_text("# workshop keys\nNVIDIA_API_KEY=nvapi-from-file\n")
    monkeypatch.setattr(srv, "_SECRETS_FILE", secrets)
    body = _client(monkeypatch, fake_chat).get("/api/status").json()
    assert (body["key_present"], body["key_source"]) == (True, "secrets.env")
    assert os.environ["NVIDIA_API_KEY"] == "nvapi-from-file"   # ambient for ChatNVIDIA


def test_key_from_the_launch_environment_wins(monkeypatch, fake_chat, tmp_path):
    """A key exported by whoever launched the server was set deliberately; a server
    that silently swapped it for the file's would be undebuggable."""
    secrets = tmp_path / "secrets.env"
    secrets.write_text("NVIDIA_API_KEY=nvapi-from-file\n")
    monkeypatch.setattr(srv, "_SECRETS_FILE", secrets)
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-explicit")
    body = _client(monkeypatch, fake_chat).get("/api/status").json()
    assert body["key_source"] == "env"
    assert os.environ["NVIDIA_API_KEY"] == "nvapi-explicit"


def test_key_tracks_a_secrets_edit_without_a_relaunch(monkeypatch, fake_chat, tmp_path):
    """The whole point: Secrets Manager writes the file while the tile is open, and
    the next poll must pick it up -- no relaunch, no stale copy."""
    secrets = tmp_path / "secrets.env"
    secrets.write_text("NVIDIA_API_KEY=nvapi-first\n")
    monkeypatch.setattr(srv, "_SECRETS_FILE", secrets)
    c = _client(monkeypatch, fake_chat)
    c.get("/api/status")
    secrets.write_text("NVIDIA_API_KEY=nvapi-rotated\n")
    body = c.get("/api/status").json()
    assert body["key_source"] == "secrets.env"
    assert os.environ["NVIDIA_API_KEY"] == "nvapi-rotated"


def test_key_injection_is_retracted_when_the_file_loses_it(monkeypatch, fake_chat, tmp_path):
    """key_present must never report a key the learner has since removed."""
    secrets = tmp_path / "secrets.env"
    secrets.write_text("NVIDIA_API_KEY=nvapi-first\n")
    monkeypatch.setattr(srv, "_SECRETS_FILE", secrets)
    c = _client(monkeypatch, fake_chat)
    assert c.get("/api/status").json()["key_present"] is True
    secrets.write_text("NVIDIA_API_KEY=\n")
    body = c.get("/api/status").json()
    assert (body["key_present"], body["key_source"]) == (False, None)
    assert "NVIDIA_API_KEY" not in os.environ


def test_key_reads_missing_when_it_is_nowhere(monkeypatch, fake_chat):
    body = _client(monkeypatch, fake_chat).get("/api/status").json()
    assert (body["key_present"], body["key_source"]) == (False, None)


def test_secrets_parser_tolerates_export_quotes_comments_and_crlf(monkeypatch, tmp_path):
    secrets = tmp_path / "secrets.env"
    secrets.write_text("# comment\n"
                       "#NVIDIA_API_KEY=commented-out\n"
                       "OTHER_KEY=zzz\r\n"
                       'export NVIDIA_API_KEY="nvapi-quoted"\r\n')
    monkeypatch.setattr(srv, "_SECRETS_FILE", secrets)
    assert srv._read_secrets_key() == "nvapi-quoted"


def test_query_makes_the_key_ambient_before_the_lab_runs(monkeypatch, fake_chat, tmp_path):
    """Live queries buy tokens with this key, so the file has to be reconciled on the
    query path itself -- a learner who never opens the status poll (curl, tests)
    still gets the key."""
    secrets = tmp_path / "secrets.env"
    secrets.write_text("NVIDIA_API_KEY=nvapi-late\n")
    monkeypatch.setattr(srv, "_SECRETS_FILE", secrets)
    c = _client(monkeypatch, fake_chat)
    seen = {}
    pool = {"strong": fake_chat("big"), "efficient": fake_chat("small")}

    def spying_pool():
        seen["key"] = os.environ.get("NVIDIA_API_KEY")
        return pool
    monkeypatch.setattr(answers, "build_model_pool", spying_pool)

    r = c.post("/api/query", json={"text": "x", "strategy": "efficient_only"})

    assert "event: answer" in r.text
    assert seen["key"] == "nvapi-late"


def test_unauthenticated_tracing_goes_quiet(monkeypatch):
    """LANGSMITH_TRACING=true with no key means a 401 trace-upload failure printed on
    every lab call the client makes (verified live in the Workbench container)."""
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    srv._quiet_unauthenticated_tracing()
    assert os.environ["LANGSMITH_TRACING"] == "false"


def test_authenticated_tracing_is_left_alone(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "lsv2-test")
    srv._quiet_unauthenticated_tracing()
    assert os.environ["LANGSMITH_TRACING"] == "true"


# ------------------------------------------------------------- the lab hint ---

def test_lab_hint_points_at_the_interpreter_on_a_missing_module(monkeypatch):
    """A ModuleNotFoundError from the lab is an INTERPRETER problem -- the learner's
    file may be perfect and still not execute here -- so the hint must say that and
    name the fix, not just echo the traceback line."""
    def missing():
        raise ModuleNotFoundError("No module named 'langchain_nvidia_ai_endpoints'",
                                  name="langchain_nvidia_ai_endpoints")
    monkeypatch.setattr(srv, "_load_lab", missing)
    body = TestClient(srv.app).get("/api/status").json()
    assert body["lab_error"].startswith("ModuleNotFoundError")
    assert "install_switchyard.sh" in body["lab_hint"]
    assert "not from your code" in body["lab_hint"]


def test_lab_hint_points_at_the_terminal_on_learner_errors(monkeypatch):
    def half_typed():
        raise SyntaxError("invalid syntax (routing_lab.py, line 47)")
    monkeypatch.setattr(srv, "_load_lab", half_typed)
    body = TestClient(srv.app).get("/api/status").json()
    assert "--exercise 1" in body["lab_hint"]


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
