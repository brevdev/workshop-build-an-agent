"""Routing Client backend.

WINDOW, NOT WIZARD: this file contains zero routing logic. It re-reads the
learner's routing_lab.py from disk on every request and renders whatever that
file returns -- every lane, price, receipt and verdict below was decided by the
lab. The server's only jobs are to name the SSE event a result arrives on, to
say which exercise is still blank when one raises, to keep the unlock probe
away from the module answering live queries, and to keep NVIDIA_API_KEY current
from <repo_root>/secrets.env (a tile has no terminal to export it in).

Launched by routing_client/start_client.sh (the JupyterLab tile's entry point).
"""
import importlib.util, json, os, pathlib, socket, subprocess, sys, threading, urllib.parse

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

HERE = pathlib.Path(__file__).resolve().parent
LAB_DIR = HERE.parent
# code/8-agent-routing/routing_client -> the repo root. The UI prints this in the
# missing-key banner: the server shares a filesystem with the learner's terminal,
# so a path derived here is right both inside JupyterLab (/project) and outside it.
REPO_ROOT = LAB_DIR.parent.parent
sys.path.insert(0, str(LAB_DIR))          # constants / switchyard_shim / routing_lab

import constants                          # noqa: E402  -- needs LAB_DIR on sys.path
import switchyard_shim as shim            # noqa: E402  -- the ONLY route to the SDK

app = FastAPI(title="Routing Client")
STATIC = HERE / "static"
_PROBE_LOCK = threading.Lock()
_LOCKED_HINT = "fill that TODO in routing_lab.py and retry."


# --------------------------------------------------------------------------
# The key. The tile inherits the JupyterLab server's environment, and no learner
# terminal ever exported anything into THAT — so "set it in a terminal" cannot
# reach a tile. The workshop's canonical key store is <repo_root>/secrets.env
# (the Secrets Manager tile writes it), and the lab reads the key from the
# environment (ChatNVIDIA), so the bridge is: re-read the file on every status
# poll and every query, and keep os.environ current.
# --------------------------------------------------------------------------

_KEY_ENV = "NVIDIA_API_KEY"
_SECRETS_FILE = REPO_ROOT / "secrets.env"    # a seam: tests point it at a tmp file
_injected_key = None                         # the value THIS server put in os.environ


def _quiet_unauthenticated_tracing():
    """The Workbench container ships LANGSMITH_TRACING=true (variables.env) but the
    tile never sees a LangSmith key, so every lab call the client makes — in-process
    or in an exercise subprocess — retries a 401 trace upload and prints the failure.
    Terminals don't hit this (sourcing secrets.env loads that key too), so: tracing
    stays exactly as configured when it is authenticated, and goes quiet when it
    could only ever fail."""
    if os.environ.get("LANGSMITH_TRACING", "").lower() == "true" \
            and not os.environ.get("LANGSMITH_API_KEY"):
        os.environ["LANGSMITH_TRACING"] = "false"


_quiet_unauthenticated_tracing()             # once, at startup: subprocesses inherit it


def _read_secrets_key():
    """NVIDIA_API_KEY as secrets.env spells it right now, else None. Tolerates
    `export K=V`, quotes, comments and CRLF; last assignment wins (source
    semantics). An absent or unreadable file is an ordinary no, never an error —
    this runs on every poll."""
    try:
        text = _SECRETS_FILE.read_text()
    except OSError:
        return None
    value = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        name, sep, raw = line.partition("=")
        if not sep or name.strip() != _KEY_ENV or name.startswith("#"):
            continue
        raw = raw.strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            raw = raw[1:-1]
        value = raw or None
    return value


def _refresh_key():
    """Reconcile os.environ with secrets.env; return where the key in effect came
    from ("env", "secrets.env") or None. A key exported by whoever launched the
    server always wins — it was set deliberately, and a server that silently
    swapped it out would be undebuggable. Otherwise the environment tracks the
    file both ways: an edit reaches a tile that is already open, and a key removed
    from the file stops being reported as present."""
    global _injected_key
    current = os.environ.get(_KEY_ENV)
    if current and current != _injected_key:
        return "env"
    fresh = _read_secrets_key()
    if fresh:
        if fresh != current:
            os.environ[_KEY_ENV] = fresh
        _injected_key = fresh
        return "secrets.env"
    if current:                              # our own stale injection — retract it
        del os.environ[_KEY_ENV]
    _injected_key = None
    return None


# --------------------------------------------------------------------------
# Loading the learner's lab. Re-read from disk per request: fill a TODO, hit
# the UI again, watch the panel come alive -- no client restart.
# --------------------------------------------------------------------------

def _lab_path(name=None):
    """Which file to render. ROUTING_LAB_MODULE points the client at another lab
    file -- how a demo runs the finished implementation without touching the
    learner's copy:  ROUTING_LAB_MODULE=routing_lab.answers bash start_client.sh 8899
    """
    name = name or os.environ.get("ROUTING_LAB_MODULE") or "routing_lab"
    return LAB_DIR / f"{name}.py"


def _exec_module(name, path):
    """Execute a lab file into a private module object -- not `import routing_lab`,
    so a dotted ROUTING_LAB_MODULE (routing_lab.answers) works too, and so each
    caller gets its own copy instead of sharing one reloaded global."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_lab():
    return _exec_module("routing_lab_live", _lab_path())


def _probe_copy(lab):
    """probe_unlocks briefly swaps a module global (ChatNVIDIA) and prints a trace,
    so it must never run against the module object serving live queries. Hand it a
    private, freshly executed copy of the same file. The path comes from the module
    _load_lab returned, so the env var and any test that substitutes _load_lab both
    keep working through one seam. Its Ex3 probe prints a stray `[route -> efficient]`
    line to the server's stdout -- expected trace noise, not an error."""
    path = getattr(lab, "__file__", None)
    return _exec_module("routing_lab_probe", path) if path else lab


# --------------------------------------------------------------------------
# Rendering helpers
# --------------------------------------------------------------------------

def _sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _locked(blank):
    """An unfilled blank raises NotImplementedError naming its exercise ("Exercise
    2b") -- put that label in the banner so the learner knows where to go. A bare
    NotImplementedError() carries no label, and "Locked:  -- fill that TODO"
    pointing at nothing is worse than plain error text, so it gets generic text."""
    label = str(blank).strip()
    if not label:
        return ("NotImplementedError: an unfilled TODO in routing_lab.py is on this "
                "path — fill it and retry.")
    return f"Locked: {label} — {_LOCKED_HINT}"


def _gateway_alive():
    """Ex4's health light. A connect probe, never a request: status is polled, so it
    must stay free and quiet whether or not a gateway is up."""
    url = urllib.parse.urlsplit(constants.GATEWAY_BASE_URL)
    try:
        with socket.create_connection((url.hostname or "127.0.0.1", url.port or 80),
                                      timeout=0.3):
            return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------

def _lab_hint(exc):
    """One actionable line under the lab-didn't-execute banner. A missing module is
    an INTERPRETER problem, not a lab problem — the learner's file may be perfect
    and still not execute here — so that case names the interpreter and the fix.
    Everything else points at the terminal, where the full traceback lives."""
    if isinstance(exc, ModuleNotFoundError):
        return (f"That import is missing from the client's interpreter "
                f"({sys.executable}), not from your code. Run "
                f"`bash scripts/install_switchyard.sh` — it prepares an environment "
                f"with the lab's dependencies — then relaunch this tile: it prefers "
                f"that environment when it exists.")
    return ("Run `python3 routing_lab.py --exercise 1` in a terminal to see the "
            "full traceback.")


def _current_unlocks():
    """The unlock probe as one seam: (unlocks dict, exception-or-None). Shared by
    /api/status (which renders the failure) and /api/exercise (which refuses to
    spawn on it) so the two can never disagree about what counts as solved."""
    try:
        probe = _probe_copy(_load_lab())
        with _PROBE_LOCK:                      # belt and braces: one probe at a time
            return probe.probe_unlocks(probe), None
    except Exception as exc:                   # a half-typed lab must not 500 the UI
        return {"ex1": False, "ex2": False, "ex3": False, "ex5": False}, exc


@app.get("/api/status")
def status():
    """The `systems online: N/5` strip plus the health panel. Ex4's blank is a config
    file rather than Python, so it is not probed -- gateway_alive stands in for it."""
    key_source = _refresh_key()                # secrets.env edits land without a relaunch
    unlocks, lab_exc = _current_unlocks()
    return {"unlocks": unlocks,
            "gateway_alive": _gateway_alive(),
            "key_present": bool(os.environ.get(_KEY_ENV)),
            "key_source": key_source,          # "env" | "secrets.env" | None
            "repo_root": str(REPO_ROOT),   # the banner's `<root>/secrets.env` path
            "python": sys.executable,      # which interpreter the lab executes under
            # Read once at startup: reloading the shim mid-session would swap the
            # MockRouter class out from under an in-flight query. Install the SDK,
            # then restart the tile.
            "sdk_available": shim.SDK_AVAILABLE,
            "lab_error": f"{type(lab_exc).__name__}: {lab_exc}" if lab_exc else None,
            "lab_hint": _lab_hint(lab_exc) if lab_exc else None}


def _memory_mb(field):
    """`1234 MiB` -> 1234. `[N/A]` -> None: unified-memory parts (GB10) report no
    per-process figure, and that is not a reason to hide a live GPU."""
    head = field.strip().split()
    return int(head[0]) if head and head[0].isdigit() else None


@app.get("/api/gpu")
def gpu():
    """Ex4b's badge: is there a GPU under this box, and how busy is it right now?
    Polled every 2s while gateway mode is on, so every way this can fail -- no
    nvidia-smi, no driver, a wedged one, a line this parser does not recognise --
    has to be the same quiet answer instead of a 500 twice a second. nvidia-smi
    prints one line per GPU; the badge is a liveness cue for the local lane, not a
    monitoring product, so it reports GPU 0 rather than inventing an aggregate."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=2, check=True).stdout
        utilization, memory = out.strip().splitlines()[0].split(",")
        return {"available": True,
                "utilization_pct": int(utilization.strip().split()[0]),
                "memory_used_mb": _memory_mb(memory)}
    except Exception:
        return {"available": False}


@app.get("/api/gateway_stats")
def gateway_stats():
    """Ex4's REAL router tax. A gateway receipt's `router_tax` is structurally 0.0 --
    the judge's tokens are spent server-side and never reach a completion's usage
    block -- so the tier split and the tax have to come from the gateway's own books.
    The numbers are still the lab's (gateway_stats() is its function, pointed at the
    gateway's /v1/stats); this only forwards them, so the page never has to reach a
    second origin. Two guards, because this is polled: the same connect probe
    /api/status uses, and a JSON answer rather than a stack trace if the gateway goes
    away between the probe and the read.

    One quirk the renderer must respect (docs/specs/switchyard-api-notes.md): read
    `tiers.*.token_pct`, never `tiers.*.calls` -- the default tier's call counter
    reads 0 no matter how much traffic it served."""
    if not _gateway_alive():
        return JSONResponse(status_code=503, content={
            "available": False,
            "error": f"no gateway listening on {constants.GATEWAY_BASE_URL}"})
    try:
        return {"available": True, "stats": _load_lab().gateway_stats()}
    except Exception as exc:
        return JSONResponse(status_code=503, content={
            "available": False, "error": f"{type(exc).__name__}: {exc}"})


@app.post("/api/query")
def query(body: dict):
    """One query down one strategy's track. Every branch hands off to the lab and
    streams back exactly what came out of it."""
    text, strategy = body.get("text", ""), body.get("strategy", "")

    def gen():
        try:
            _refresh_key()          # the call below buys real tokens with this key
            lab = _load_lab()
            if strategy not in constants.STRATEGIES:
                raise ValueError(f"unknown strategy {strategy!r}")
            bill = lab.RunningBill()
            if strategy == "gateway":          # Ex4 answers out of process: no pool here
                answer, receipt = lab.gateway_call(text, bill)
            else:
                pool = lab.build_model_pool()
                if strategy == "strong_only":
                    response, receipt = lab.bill_call(lab.STRONG_MODEL, pool["strong"], text, bill)
                elif strategy == "efficient_only":
                    response, receipt = lab.bill_call(lab.EFFICIENT_MODEL, pool["efficient"], text, bill)
                elif strategy == "manual_classifier":
                    response, receipt = lab.route_call(text, pool, bill)
                elif strategy == "switchyard_stage":
                    response, receipt = lab.switchyard_call(text, pool, bill)
                else:                          # mock_demo: routed with no SDK -- but the
                    # MockRouter replaces the routing DECISION only. The call that
                    # answers is a live one, so this path needs the key like every other.
                    response, receipt = lab.switchyard_call(text, pool, bill,
                                                            router=shim.MockRouter())
                answer = response.content
            # The lane is the one thing this file derives rather than forwards, and it
            # is a mapping of the id the receipt already carries -- never a second
            # opinion about routing. Three arms, because the gateway can name a model
            # neither constant covers: a local NIM (Ex4b) or an upstream rename. The
            # lab prices those at the efficient tier as a FALLBACK, so calling them
            # "efficient" here would have the yard claim a lane the receipt cannot
            # back up. `local` gets its own rail (or the efficient one with the raw id
            # showing, when there is no GPU lane to park on).
            if receipt["model"] == lab.STRONG_MODEL:
                lane = "capable"
            elif receipt["model"] == lab.EFFICIENT_MODEL:
                lane = "efficient"
            else:
                lane = "local"
            yield _sse("route_decision", {"lane": lane, "model": receipt["model"],
                                          "why": receipt["why"]})
            # The one number the receipt does not carry: what this query would have
            # cost at the frontier tier, minus what it did cost.
            receipt["counterfactual_saved"] = receipt["counterfactual_cost"] - receipt["cost"]
            yield _sse("receipt", receipt)
            yield _sse("answer", {"text": answer})
        except NotImplementedError as blank:
            yield _sse("error", {"message": _locked(blank)})
        except Exception as exc:
            yield _sse("error", {"message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(gen(), media_type="text/event-stream")


# The UI, mounted last: it is a catch-all, and /api/* is matched before it.
if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
