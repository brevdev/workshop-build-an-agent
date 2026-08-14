"""Routing Client backend.

WINDOW, NOT WIZARD: this file contains zero routing logic. It re-reads the
learner's routing_lab.py from disk on every request and renders whatever that
file returns -- every lane, price, receipt and verdict below was decided by the
lab. The server's only jobs are to name the SSE event a result arrives on, to
say which exercise is still blank when one raises, and to keep the unlock probe
away from the module answering live queries.

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

@app.get("/api/status")
def status():
    """The `systems online: N/5` strip plus the health panel. Ex4's blank is a config
    file rather than Python, so it is not probed -- gateway_alive stands in for it."""
    body = {"gateway_alive": _gateway_alive(),
            "key_present": bool(os.environ.get("NVIDIA_API_KEY")),
            "repo_root": str(REPO_ROOT),   # the banner's `source <root>/secrets.env`
            # Read once at startup: reloading the shim mid-session would swap the
            # MockRouter class out from under an in-flight query. Install the SDK,
            # then restart the tile.
            "sdk_available": shim.SDK_AVAILABLE,
            "lab_error": None}
    try:
        probe = _probe_copy(_load_lab())
        with _PROBE_LOCK:                      # belt and braces: one probe at a time
            unlocks = probe.probe_unlocks(probe)
    except Exception as exc:                   # a half-typed lab must not 500 the UI
        unlocks = {"ex1": False, "ex2": False, "ex3": False, "ex5": False}
        body["lab_error"] = f"{type(exc).__name__}: {exc}"
    return {"unlocks": unlocks, **body}


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


def _canonical_rank(strategy):
    order = constants.STRATEGIES
    return order.index(strategy) if strategy in order else len(order)


# THE /api/race CONTRACT: run_suite answers the 12-task workload under these four
# and raises ValueError on anything else, so these four are all the race accepts.
# `gateway` and `mock_demo` are /api/query strategies only -- they are in
# constants.STRATEGIES, so the UI must not offer them as race chips.
RACE_STRATEGIES = ["strong_only", "efficient_only", "manual_classifier", "switchyard_stage"]


@app.post("/api/race")
def race(body: dict):
    """Ex5's leaderboard: the 12-task suite under each strategy, one row at a time.
    Accepts RACE_STRATEGIES only (see above)."""
    requested = body.get("strategies") or []

    def gen():
        # Validate BEFORE the first suite runs. A race is ~12 live calls per strategy,
        # so a bad entry discovered at strategy three has already spent real money on
        # a run that ends in an error instead of a verdict. Rejection is all-or-
        # nothing rather than "run the valid subset": silently dropping a chip the
        # learner selected would hand back a verdict comparing less than they asked
        # for, and the receipt would not say so.
        unsupported = list(dict.fromkeys(s for s in requested if s not in RACE_STRATEGIES))
        if unsupported or not requested:
            problem = (f"unsupported {', '.join(unsupported)}" if unsupported
                       else "no strategies selected")
            yield _sse("error", {"message": f"Race: {problem}. "
                                            f"Supported: {', '.join(RACE_STRATEGIES)}."})
            return
        results = {}
        try:
            lab = _load_lab()
            # routing_verdict picks the routed row by dict INSERTION order, so results
            # go in in constants.STRATEGIES order however the UI listed them --
            # otherwise the receipt would compare against whichever chip came first.
            # dict.fromkeys also collapses a chip sent twice into one suite run.
            for strategy in dict.fromkeys(sorted(requested, key=_canonical_rank)):
                results[strategy] = lab.run_suite(strategy, lab.RunningBill())
                rows = lab.routing_verdict(results)["rows"]
                yield _sse("race_row", next(r for r in rows if r["strategy"] == strategy))
            yield _sse("race_receipt", {"receipt": lab.routing_verdict(results)["receipt"]})
        except Exception as exc:
            # Whatever finished has already been paid for: render its verdict before
            # saying what broke. (If the verdict itself is the blank that broke, there
            # is nothing to render -- say so once, in the error.)
            receipt = None
            if results:
                try:
                    receipt = lab.routing_verdict(results)["receipt"]
                except Exception:
                    receipt = None
            if receipt is not None:
                yield _sse("race_receipt", {"receipt": receipt})
            yield _sse("error", {"message": _locked(exc)
                                 if isinstance(exc, NotImplementedError)
                                 else f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(gen(), media_type="text/event-stream")


# The UI, mounted last: it is a catch-all, and /api/* is matched before it.
if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
