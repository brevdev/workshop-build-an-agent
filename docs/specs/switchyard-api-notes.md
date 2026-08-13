# NeMo Switchyard — verification spike & pin record

**Task 1 of the Module 8 build (spec §8/§8b "verify-at-implementation" checklist).**
Everything below was **executed**, not read off a docs page. Where the upstream docs, the
Module 8 design spec (`docs/specs/2026-08-13-module-8-agent-routing-design.md`) and the
shipped package disagree, **the shipped package wins** and the disagreement is recorded
under [Deviations](#deviations-from-spec-assumptions).

| | |
|---|---|
| **Verified on** | 2026-08-13 |
| **Box** | GB10 / DGX Spark, `aarch64`, Linux 6.17, Python 3.12.3 |
| **Upstream** | [github.com/NVIDIA-NeMo/Switchyard](https://github.com/NVIDIA-NeMo/Switchyard) — Apache-2.0, self-described **pre-alpha** ("Experimental software. Not for production use.") |
| **Live endpoint** | `https://integrate.api.nvidia.com/v1` with `NVIDIA_API_KEY` |
| **Scratch** | `/tmp/claude-syd*` (venv, probe configs, probe scripts) — nothing committed |

---

## Pins

### The pip package

```
nemo-switchyard[cli]==0.2.0          # PyPI name; top-level imports are `switchyard` + `switchyard_rust`
```

`0.2.0` is the newest release (`pip index versions nemo-switchyard` → `0.2.0, 0.1.0, 0.0.1`;
`0.0.1.dev1` also exists on PyPI but is not listed). Uploaded **2026-08-10**.

Built with **maturin** — every wheel carries a ~25 MB compiled Rust extension
(`switchyard_rust/_switchyard_rust.abi3.so`). There is no pure-Python fallback: the routing
algorithms **and the whole gateway** live in that `.so`.

### Wheel sha256s (the audit record; `install_switchyard.sh` verifies the matching one)

| Platform | Wheel | sha256 |
|---|---|---|
| **Linux aarch64** (GB10/Spark, Jetson) | `nemo_switchyard-0.2.0-cp312-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl` | `18ec104d044161a15979f562cfdc4a132543e882d051ed80d052219d78333378` |
| **Linux x86_64** (Brev A100, most learners) | `nemo_switchyard-0.2.0-cp312-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `5691b5df6573ac21a2f2fb76050d957e99340536b0536a1c85278892a5808e76` |
| macOS arm64 | `nemo_switchyard-0.2.0-cp312-abi3-macosx_11_0_arm64.whl` | `46afd9b3df91cdc91b8544572cf3ec7106a0d5c75a785ee0677f0e45ac2461f1` |
| macOS x86_64 | `nemo_switchyard-0.2.0-cp312-abi3-macosx_10_12_x86_64.whl` | `746d4307011a29e1b0a8126b3e615cea2d1c1493dbd0c5fcf36db4538c737203` |
| Windows amd64 | `nemo_switchyard-0.2.0-cp312-abi3-win_amd64.whl` | `4641d19c6e7fd6d64d05bd8354f409e9f6a80a1472f7f0518a5ecc9c4347dbb1` |
| Windows arm64 | `nemo_switchyard-0.2.0-cp312-abi3-win_arm64.whl` | `5ea9e65a751da540e7231d39f28ecf66af06e90ffccec36a05ca755875430c05` |
| sdist | `nemo_switchyard-0.2.0.tar.gz` | `da76a59ea88563d12828a439ae51475b4ffef2f231a6f44bde47eb2eda5e3648` |

**aarch64 and x86_64 Linux wheels both exist and both are `manylinux2014`** — the module has
no arch problem on either the workshop image or this GB10. Verified by installing the aarch64
wheel here and running the gateway live (below).

### Python version

**`>=3.12`.** The published `0.2.0` METADATA says `Requires-Python: >=3.12` and every wheel is
`cp312-abi3`. The workshop image already ships Python 3.12 (`postBuild.bash` uses `python3.12`
throughout), so this is a non-issue — but see [Deviation 7](#7-python-version-the-readme-is-wrong):
the README and the repo's `main` branch both advertise 3.10, which does not work.

### Transitive runtime deps (unpinned by us; resolved versions observed 2026-08-13)

| Declared | Resolved here |
|---|---|
| `openai>=2.7,<3.0` | 2.54.0 |
| `anthropic>=0.99.0,<1.0` | 0.122.0 |
| `httpx>=0.28.1,<1.0` | 0.28.1 |
| `pydantic>=2.13.3,<3.0` | 2.13.4 |
| `prompt-toolkit>=3.0.52,<4.0` (extra `cli`) | 3.0.53 |

Other extras that exist but the module does **not** use: `server` (fastapi/uvicorn/sse-starlette —
that is the *YAML* server, see Deviation 4), `tracing` (ddtrace), `affinity-redis` (redis), `all`.

Full install (wheel + all deps) took **~4 s** on this box and needs no compiler.

### The Rust crate (NOT used by this module)

`switchyard-server` on crates.io is at **0.2.0** (its only published version, 2026-08-10).
Installing it means `cargo install --locked switchyard-server` — a full Rust release build.
**We do not do this, and Module 8 does not need it.** See [Server install](#server-install).

### `langchain-nvidia-switchyard`

**Does not exist.** `pip index versions langchain-nvidia-switchyard` → *No matching distribution*;
`https://pypi.org/simple/langchain-nvidia-switchyard/` → **404**. A grep of the full PyPI simple
index for `switchyard` returns exactly three projects:

- `nemo-switchyard` — ours
- `switchyard` (1.0.0, Joel Sommers) — **unrelated**, a networking-course framework. Do not let a
  learner `pip install switchyard`.
- `switchyard-dev` (0.1.1) — **unrelated**, "local HTTP runtimes for parallel AI agent worktrees".

Also 404: `langchain-switchyard`, `switchyard-langchain`, `nemo-switchyard-langchain`,
`litellm-switchyard`, `nvidia-switchyard`. The LangChain middleware and LiteLLM plugin named in the
design spec's §0 are **not installable today** — treat them as ecosystem prose in
`evaluating_routing.md`, never as a lab dependency.

---

## Python surface

**There is a real, rich Python routing surface.** The spec's §8 fear ("CLI-only, wrap the server over
HTTP") did not materialise. Task 5's shim can call `switchyard.libsy` directly.

```python
import switchyard
switchyard.__version__        # '0.2.0'
```

Two top-level packages install: **`switchyard`** (Python: libsy bindings, config/profile machinery,
CLI) and **`switchyard_rust`** (thin loaders over the compiled `.so`).

### `switchyard.libsy` — the in-process router (Exercise 3 / Task 5's shim)

```python
from switchyard.libsy import (
    Algorithm, LibsyError, LlmClient, LlmFallback, LlmTarget, TaskClassifierConfig, algorithms,
)
```

Verbatim signatures, from `inspect.signature` on the installed package:

```python
LlmTarget(name, client)
#   "A required-client routing target used by Python-created algorithms."
#   .name -> str   (read-only property; this string is what shows up as `selected_model`)

class LlmClient(Protocol):          # you implement this; structural, no base class to inherit
    async def call(self, request: Mapping[str, object]) -> Mapping[str, object]: ...

TaskClassifierConfig(base_threshold, *, threshold_step=0.0, session_affinity=False,
                     message_hash_fallback=False, recent_turn_window=None,
                     max_output_tokens=4096, prompt=None)

LlmFallback(judge_target, *, config)          # config: TaskClassifierConfig

algorithms.llm_task_classifier(judge_target, efficient_target, capable_target, *, config)
algorithms.stage_router(capable_target, efficient_target, *, picker, confidence_threshold,
                        recent_window=None, escalation_note=None, deescalation_note=None,
                        only_on_wrong_signal_escalation=True, capable_system_prompt=None,
                        efficient_system_prompt=None, classifier=None)
algorithms.random(targets, *, weights=None, seed=None)
algorithms.noop()

Algorithm.run(request, headers=None)          # async; returns (decisions, response)
```

Notes that cost time to discover:

- **`picker` is a string with exactly two legal values**: `"capable_first"` or `"efficient_first"`.
  Anything else raises `picker must be 'capable_first' or 'efficient_first', got "..."`.
- `algorithms.random` accepts `weights` and `seed` at runtime even though the shipped `.pyi` stub
  declares only `random(targets)`. Trust the runtime signature.
- The Rust *crate* README says libsy "never calls a model itself". The **Python** binding is not like
  that: `Algorithm.run` is documented as *"Run to completion using the clients configured on the
  algorithm's targets"* — the algorithm orchestrates and calls **your** `LlmClient.call`. You own the
  transport; libsy owns the decision **and** the control flow.
- `LibsyError` subclasses `switchyard_rust.core.SwitchyardRuntimeError`. A raise inside your
  `LlmClient.call` surfaces as `LibsyError: client call to target "<name>" failed: ...`.

#### The neutral request your `LlmClient.call` receives

Passing an OpenAI-shaped dict straight through **fails** —
`ValueError: invalid type: string "h", expected internally tagged enum ContentBlock`. Message
content must be a list of tagged blocks. Minimal accepted input to `Algorithm.run`:

```python
{"model": "switchyard",
 "messages": [{"role": "user", "content": [{"type": "text", "text": "hi"}]}],
 "output": {"max_output_tokens": 256}}
```

…which libsy normalises and hands to your client as (observed verbatim):

```python
{"model": "switchyard", "instructions": [], "messages": [...], "tools": [], "tool_choice": None,
 "sampling": {"temperature": None, "top_p": None, "top_k": None},
 "output": {"max_output_tokens": None, "response_format": None},
 "reasoning": {"effort": None, "raw": None},
 "stream": False, "extensions": {"fields": {}},
 "preservation": {"requests": {}, "responses": {}}}
```

`instructions` is a list of system-role messages in the same block shape
(`{"role": "system", "content": [{"type": "text", "text": ...}]}`).

#### The neutral response your `LlmClient.call` must return

```python
{"id": "...", "model": "<upstream model id>",
 "outputs": [{"role": "assistant", "content": [{"type": "text", "text": "..."}]}],
 "usage": {"input_tokens": 12, "output_tokens": 34}}
```

`outputs` is **required** and each entry needs `role` — returning a bare content block fails with
`missing field 'role'`. `usage` keys are `input_tokens`/`output_tokens` (not `prompt_tokens`).

#### How a selection is reported back

`await Algorithm.run(req)` returns a **2-tuple `(decisions, response)`**:

```python
decisions == [{"reasoning": "random routing selected target 'weak'", "selected_model": "weak"}]
```

`selected_model` is the **`LlmTarget.name`** you chose — the authoritative attribution signal for the
in-process path (Exercise 3 / the Routing Client's yard animation). `reasoning` is a human string and
is *not* stable enough to parse: on a successful classifier decision it still reads
`"fall-through selected weak (confidence 1.000)"`. **Read `selected_model`; render `reasoning`.**

`response` is the neutral response as normalised by libsy (`id`, `model`, `outputs`, `usage`,
`extensions`, `preservation`); its `model` is whatever *your* client reported.

#### The judge's structured-output contract (`llm_task_classifier`)

libsy builds the judge request itself and attaches a **strict JSON-schema `response_format`** on
`request["output"]["response_format"]` that your client **must forward upstream**:

```json
{"type": "json_schema",
 "json_schema": {"name": "CapabilityClassifierDecision", "strict": true,
  "schema": {"type": "object", "additionalProperties": false,
   "required": ["crux", "primary_rule", "capability_boundary", "p_solve"],
   "properties": {
     "crux": {"type": "string", "minLength": 1},
     "primary_rule": {"enum": ["SUP-1","SUP-2","SUP-3","SUP-4","SUP-5","UNC-1","UNC-2","LIM-1","LIM-2","none"], "type": "string"},
     "capability_boundary": {"enum": ["supported","uncertain","unsupported","unmatched"], "type": "string"},
     "p_solve": {"type": "number", "minimum": 0.0, "maximum": 1.0}}}}}
```

It also sets `output.max_output_tokens = 4096` (from `TaskClassifierConfig.max_output_tokens`) and a
~2 kB system prompt ("You are a task-level probability forecaster for a model router…" plus a
SUP-/UNC-/LIM- capability card). **If the judge never emits parseable JSON, libsy does not raise — it
silently falls through to the capable target.** See [Deviation 5](#5-the-judge-must-not-think-load-bearing);
this is the single most important operational fact in this document.

#### Minimal end-to-end libsy example (verified live on this box)

Everything Task 5's shim needs, in one block. This ran against
`integrate.api.nvidia.com` and produced `2 + 2 → weak`, hard prompt `→ strong`.

```python
import asyncio, httpx, os
from switchyard.libsy import LlmTarget, TaskClassifierConfig, algorithms

BASE = "https://integrate.api.nvidia.com/v1"
KEY  = os.environ["NVIDIA_API_KEY"]

class NvidiaClient:                       # satisfies the LlmClient protocol structurally
    def __init__(self, model, *, no_think=False):
        self.model, self.no_think = model, no_think

    async def call(self, request):        # request is the NEUTRAL dict shown above
        messages = []
        for block in request.get("instructions") or []:
            messages.append({"role": block.get("role", "system"),
                             "content": "".join(c.get("text", "") for c in block.get("content", []))})
        for msg in request.get("messages", []):
            messages.append({"role": msg["role"],
                             "content": "".join(c.get("text", "") for c in msg.get("content", []))})

        output = request.get("output") or {}
        body = {"model": self.model, "messages": messages,
                "max_tokens": output.get("max_output_tokens") or 512}
        if output.get("response_format"):                 # the judge's JSON schema -- MUST forward
            body["response_format"] = output["response_format"]
        if self.no_think:                                 # judge only; see Deviation 5
            body["chat_template_kwargs"] = {"thinking": False}

        async with httpx.AsyncClient(timeout=240) as http:
            reply = await http.post(f"{BASE}/chat/completions", json=body,
                                    headers={"Authorization": f"Bearer {KEY}"})
            reply.raise_for_status()
            data = reply.json()

        text  = data["choices"][0]["message"].get("content") or ""
        usage = data.get("usage") or {}
        return {"id": data.get("id", ""), "model": data.get("model", self.model),
                "outputs": [{"role": "assistant", "content": [{"type": "text", "text": text}]}],
                "usage": {"input_tokens":  usage.get("prompt_tokens", 0),
                          "output_tokens": usage.get("completion_tokens", 0)}}

judge  = LlmTarget("judge",  NvidiaClient("nvidia/nemotron-3-nano-30b-a3b", no_think=True))
weak   = LlmTarget("weak",   NvidiaClient("nvidia/nemotron-3.5-lightning-30b-a3b"))
strong = LlmTarget("strong", NvidiaClient("nvidia/nemotron-3-super-120b-a12b"))

router = algorithms.llm_task_classifier(judge, weak, strong,
                                        config=TaskClassifierConfig(0.5))

async def main():
    # NOTE: router.run(...) must be *created* with a loop already running -- see below.
    return await router.run({
        "model": "switchyard",
        "messages": [{"role": "user", "content": [{"type": "text", "text": "What is 2 + 2?"}]}],
        "output": {"max_output_tokens": 128},
    })

decisions, response = asyncio.run(main())
print(decisions[0]["selected_model"])                     # -> 'weak'
print(response["outputs"][0]["content"][0]["text"])       # -> '4' (or similar)
```

Two traps worth calling out for Task 5:

- **Argument order** is easy to get backwards: `llm_task_classifier(judge, efficient, capable, *, config)`.
- **`asyncio.run(router.run(...))` raises `RuntimeError: no running event loop`.** The coroutine
  binds to the running loop when it is *constructed*, and `asyncio.run` has not started one yet at
  argument-evaluation time. Always build it inside an `async def` (as above), or from a notebook
  cell where a loop is already running just `await router.run(...)`.

### `switchyard_rust.server.Server` — the gateway, embedded in the wheel

```python
from switchyard_rust.server import Server
class Server:
    def __init__(self, config: str | os.PathLike[str], *, port: int = 0) -> None: ...
    port: int          # property; with port=0 an ephemeral port is bound
    base_url: str      # property, e.g. "http://127.0.0.1:4000"
    def close(self, *, timeout_secs: float = 2.0) -> None: ...
    def __enter__(self) -> "Server": ...
    def __exit__(self, et, e, tb) -> bool: ...
```

`config` is a **`routes.toml`** path. This is the same Rust proxy as the standalone binary, hosted in
process over PyO3 — `switchyard/cli/launchers/native_server.py` uses exactly this. It is the module's
gateway (Exercise 4) and needs **no cargo, no download, no separate binary**.

### CLI (`switchyard`, the only console script)

```
switchyard --version                  -> "switchyard 0.2.0"
switchyard serve   --routing-profiles PATH [--host] [--port 4000] [--inbound {openai,anthropic,both}]
                   [--workers N] [--reload] [--routing-log-file PATH] [--enable-rl-logging] [--rl-log-dir DIR]
switchyard launch  {claude,codex,openclaw}      # e.g. switchyard launch claude --model switchyard
```

`switchyard serve` is **not** the TOML gateway — see [Deviation 4](#4-switchyard-serve-is-yaml-not-routestoml).

### Other importable machinery (not needed by the lab, listed so nobody re-discovers it)

`switchyard` re-exports ~50 names including `LlmTarget`, `Switchyard`, `RouteTable`,
`ClassifierConfig`, `EscalationRouterConfig`, `StageRouterConfig`, `RandomRoutingConfig`,
`PassthroughProfileConfig`, `TranslationEngine`, `build_profile`. These are the *server-side* Python
profile/processor stack (`switchyard.lib.*`) used by the YAML `serve` path. **Task 5's shim should
use `switchyard.libsy`, not these** — `libsy` is the small, documented, Rust-owned surface.

---

## Server install

**Verdict: pip only. Nothing to download, nothing to compile, on either arch.**

| Path | How | Verdict for Module 8 |
|---|---|---|
| **Embedded PyO3 gateway** | `pip install nemo-switchyard[cli]==0.2.0`, then `switchyard_rust.server.Server("routes.toml", port=4000)` | ✅ **Use this.** aarch64 + x86_64 both verified/covered by manylinux2014 wheels. |
| Standalone Rust binary | `cargo install --locked switchyard-server` (crate 0.2.0) | ❌ Full Rust release build; needs a toolchain (not installed here) and is memory-hungry on a 128 GB unified-memory GB10. Not performed, not required. |
| Prebuilt release binary | — | ❌ **Does not exist.** GitHub releases `v0.0.1 / v0.1.0 / v0.2.0-rc.1 / v0.2.0-rc2 / v0.2.0` carry **only** auto-generated `Source code (tar.gz/zip)` assets. No `switchyard-server-<arch>` anywhere. |

So the design spec's `install_switchyard.sh` sketch (download `switchyard-server-${ARCH}` from a
release tag, `sha256sum -c`, `install` into `~/.local/bin`) **has no target to download** and that
whole stanza is gone from the real script, replaced by a comment saying so.

### Per-arch summary

- **aarch64 (this GB10, Jetson, Spark):** verified end-to-end here — wheel installs, `.so` loads,
  gateway serves, live routing works.
- **x86_64 (workshop image, Brev):** `manylinux_2_17_x86_64` wheel published with the identical
  version/ABI (`cp312-abi3`); sha256 recorded above. Not executed on x86_64 in this task — recorded
  from release metadata per the task's instruction. Risk is minimal (same wheel build, same ABI tag).

### Validating a config (the `--dry-run` replacement)

`--dry-run` is a flag on the **Rust CLI we do not install**. The equivalent with the embedded server:

```python
from switchyard_rust.server import Server
Server("routes.toml", port=0).close()      # binds an ephemeral port, then releases it
```

It performs the same load-time validation (unknown keys, missing `api_key_env` variable, bad weights,
missing targets all raise) and prints the same `WARN switchyard_server::config: …` diagnostics. This
is what `smoke_switchyard.sh` runs, and what Exercise 4's "validate before you serve" beat should
teach. It is a **real** bind, so it is not usable to validate a config while the same port is in use —
use `port=0`.

### Verified `routes.toml` schema (v0.2.0, `schema_version = 1`)

The design spec's §0 vocabulary is correct. Confirmed against
`docs/reference/toml_schema.md` **and** by loading configs through the server:

```toml
schema_version = 1

[llm_clients.<name>]                 # format (openai_chat|openai_responses|anthropic_messages), base_url,
                                     # api_key_env?, extra_headers?, max_retries? (0-10, default 2)
[targets.<name>]                     # id (upstream model id), llm_client, extra_body?
[routes.<name>]                      # id (public model id), type, context_window?, tool_calling?, reasoning?
```

`type = "llm_classifier"` keys: `mode` (`capability` default | `escalation` | `custom`),
`classifier_target`, `max_output_tokens` (default 4096), plus for capability mode `strong_target`,
`weak_target`, `base_threshold`, `threshold_step`, `session_affinity`, `message_hash_fallback`,
`recent_turn_window`, `prompt`. Escalation mode uses an inline table, exactly as the spec assumed:
`escalation = { confirmations = 2, recent_turn_window = 28, window_message_chars = 500 }`.
`type = "random"`: `targets`, `weights?`, `seed?`. `type = "passthrough"`: `target`.
`type = "noop"`: no upstream at all (handy for an offline/sandbox demo — it still needs an empty
`[targets]` table).

**`[targets.<name>].extra_body`** is the escape hatch that makes the whole module work
(Deviation 5): arbitrary keys merged into the upstream request.

---

## Gateway attribution

> **Question (spec §8.7 / Task 12): does the gateway response's `model` field report the upstream
> target model id?**
>
> ## ✅ **Yes.** Verified live against `integrate.api.nvidia.com`.

A single `POST /v1/chat/completions` with `{"model": "switchyard", ...}` came back with the
**upstream** id, and it changed with the routing decision:

| Prompt | `response["model"]` | wall time |
|---|---|---|
| `What is 2 + 2?` | `nvidia/nemotron-3.5-lightning-30b-a3b` | 0.9 s |
| `Design a fault-tolerant multi-region distributed transaction protocol with a formal linearizability proof…` | `nvidia/nemotron-3-super-120b-a12b` | 15.8 s |

The route id (`switchyard`) appears **only** in `GET /v1/models`; it never comes back in a completion.
So the Routing Client can drive its yard animation straight off the OpenAI-standard `model` field —
**no log tailing needed**, and the fallback plan in spec §8.7 can be dropped.

Response envelope is plain OpenAI Chat Completions: `id, object, created, model, choices[],
usage{prompt_tokens,completion_tokens,total_tokens}, service_tier, system_fingerprint`. There is **no**
extra `switchyard`/`routing` key on the response body, and the classifier's own token spend is **not**
in that `usage` block.

### Two better sources for the Routing Client's meters

**1. `GET /v1/stats`** — the gateway keeps the whole bill for you. Top-level keys:
`total_requests, total_errors, total_tokens, models, tiers, classifier, routing_overhead,
routing_fallbacks`. Observed after two routed requests:

```jsonc
"models": { "nvidia/nemotron-3-super-120b-a12b": {
    "calls": 1, "request_pct": 50.0, "prompt_tokens": 43, "completion_tokens": 16,
    "total_tokens": 59, "token_pct": 59.6, "cached_tokens": 0, "cache_hit_rate": 0.0,
    "max_observed_context_tokens": 77, "tiers": ["strong"],
    "model_call_latency": {"count":1,"avg_ms":15191.16,"p50_ms":…,"p99_ms":…},
    "total_latency":     {"count":1,"avg_ms":15840.31, …} }, … },
"tiers":   { "weak":   {"models":[…],"calls":1,"request_pct":50.0,"token_pct":40.4},
             "strong": {"models":[…],"calls":1,"request_pct":50.0,"token_pct":59.6} },
"classifier": { "total_requests": 2, "total_errors": 0,
                "total_tokens": {"prompt":1967,"completion":146,"total":2113},
                "models": {"nvidia/nemotron-3-nano-30b-a3b": {"calls":2, …}} },
"routing_overhead":  {"count":2,"avg_ms":1236.26,"min_ms":827.88,"max_ms":1644.63,"p50_ms":…,"p99_ms":…},
"routing_fallbacks": {"context_window": 0, "unavailable": 0}
```

This is a **gift** for the module's tokenomics thread: `tiers.*.request_pct` is the 93/7 split
measured on the learner's own traffic; `classifier.total_tokens` + `routing_overhead.avg_ms` are the
**router tax** (the M7 context-tax sequel) already itemised and *separated* from the routed spend.
`GET /health` → `{"status":"ok"}` for the client's health strip.

**`tiers` is also the health signal for the router itself.** A request the classifier could not decide
(no parseable verdict) is served **without a tier label**, so `tiers` stays `{}` while `models` and the
response `model` field still look perfectly normal. That makes an empty `tiers` map the one
deterministic tell for *both* silent-collapse modes below (Deviations 5 and 6) — `smoke_switchyard.sh`
asserts on it. The server also logs the cause: `WARN libsy: judge verdict unavailable; routing without
one … reason="parse_error"`. A Routing Client that renders tiers should treat "no tier" as a visible
degraded state, not as a missing datum.

**2. The server's own trace line** (stderr, one per request):

```
INFO switchyard_server::request: LLM request handled wire_format=openai_chat status=200
  requested_model="switchyard" selected_model="nvidia/nemotron-3.5-lightning-30b-a3b"
  streaming=false session_id="" correlation_id="" handling_duration_ms=948.59
```

### In-process (libsy) attribution

`decisions[0]["selected_model"]` — the **target name** (`"weak"`/`"strong"`), not the model id. Two
different attribution vocabularies for the two surfaces; Task 5/Task 12 should normalise.

---

## Deviations from spec assumptions

### 1. `langchain-nvidia-switchyard` does not exist
Nor does any other LangChain/LiteLLM Switchyard package (all 404 on PyPI). The design spec's §0 and
the wrap-up's "Ex3 libsy → LangChain `SwitchyardRoutingMiddleware` / LiteLLM plugin" mapping must be
worded as *ecosystem direction*, not something a learner can install. **Nothing in the lab may
depend on it.**

### 2. There is no `switchyard-server` binary to install
No pip console script, and no prebuilt asset on any GitHub release (checked v0.0.1 → v0.2.0: source
tarballs only). The standalone binary exists **only** via `cargo install --locked switchyard-server`,
a full Rust build. The module instead uses the identical Rust server **embedded in the pip wheel**
(`switchyard_rust.server.Server`). Every doc page, script and exercise that was going to say
`switchyard-server --config routes.toml --host … --port 4000` must be rewritten around that.
`install_switchyard.sh` records this in place of the brief's download-and-checksum stanza.

### 3. `--dry-run` is not available
It is a flag on the Rust CLI we do not install. Use `Server(cfg, port=0).close()` (see
[Server install](#validating-a-config-the---dry-run-replacement)). The *pedagogy* — validate before
you serve — survives intact; only the command changes.

### 4. `switchyard serve` is YAML, not `routes.toml`
The CLI's `serve` takes `--routing-profiles PATH`, a **YAML routing-profile bundle** parsed by
`switchyard/cli/route_bundle.py::parse_routing_profiles_file`, and needs the `[server]` extra
(fastapi + uvicorn + sse-starlette). Feeding it a `routes.toml` throws inside
`load_route_bundle_table`. Two different config dialects ship in one package — **the module teaches
the TOML one** (it is what upstream documents, what `switchyard launch --config` takes, and what the
Rust gateway consumes). Do not install `[server]`; do not mention `switchyard serve`.

### 5. The judge must not "think" (**load-bearing**)
`nvidia/nemotron-3.5-lightning-30b-a3b` on `integrate.api.nvidia.com` emits chain-of-thought into
`content` by default. As the classifier judge it burns the entire 4096-token verdict budget on
`Here's a thinking process: …`, never emits the `CapabilityClassifierDecision` JSON, and **libsy
silently falls through to the strong target** — so *every* request pays frontier prices while
appearing to work. Measured, same config except the judge's thinking flag:

| Judge config | EASY prompt | HARD prompt | classifier completion tokens | routing overhead |
|---|---|---|---|---|
| thinking **on** (default) | → **strong** | → strong | 8192 (2 × the 4096 cap) | **avg 32 211 ms** |
| thinking **off** | → **weak** ✅ | → strong ✅ | 119–146 | avg 757–1236 ms |

Fix, verified in both surfaces:

- **TOML:** `[targets.judge] extra_body = { chat_template_kwargs = { thinking = false } }`
- **libsy:** your `LlmClient` for the judge target adds `chat_template_kwargs={"thinking": False}`
  to the upstream body (a `/no_think` system message also works).

Structured output itself is fine on both hosted models — `nemotron-3-super-120b-a12b` returns clean
JSON immediately; `nemotron-3.5-lightning-30b-a3b` and `nemotron-3-nano-30b-a3b` do too **once
thinking is off** (or, for a short prompt, if given ≥4096 tokens to think first — not reliable with
the classifier's long capability-card prompt). Task 6's `routes.toml.answers` **must** carry the
`extra_body` line, and Task 5's shim must set it for the judge. Consider making it a taught beat: it
is a perfect "the router tax is real and you can measure it" moment.

### 6. The judge cannot reuse the efficient target's model id (**breaks the spec's model pool**)
The design spec's §2 model pool says *"Classifier: the efficient target itself (no third model, no
added cost surprise)."* With both `[targets.judge]` and `[targets.weak]` set to the same `id` on the
same `llm_client`, the server logs

```
WARN switchyard_server::config: target weak reuses model id nvidia/nemotron-3.5-lightning-30b-a3b
on llm client nvidia; only one target per id is kept and the other is dropped.
```

…and **routing dies silently**: `stats.tiers` comes back `{}` and every request — easy or hard —
goes to `strong`. Two workarounds, both verified live:

- **(a) A distinct judge model.** `[targets.judge] id = "nvidia/nemotron-3-nano-30b-a3b"` +
  `extra_body` thinking-off. Correct routing (easy→Lightning, hard→Super), ~1.2 s overhead. Costs a
  third model id but is unambiguous.
- **(b) A second `llm_client` pointing at the same base_url.** Dedup is keyed on
  *(llm_client, model id)*, so declaring `[llm_clients.nvidia_judge]` (identical fields) and hanging
  `[targets.judge]` off it keeps the spec's "the efficient model is also the judge" story. Verified:
  no warning, judge runs (119 completion tokens, 757 ms overhead), tiers populated.

**Task 6 must pick one and calibrate `base_threshold`.** Note the calibration wrinkle: with (b),
Lightning-as-judge scored *both* probe prompts above 0.5 and sent both to weak — a fine outcome, but
it means the demo prompts and threshold need tuning so learners actually *see* the split. Judge choice
is a real dial, not a detail. (Recommendation: (b) for fidelity to the module's thesis, with a
harder-calibrated HARD prompt; fall back to (a) if the split stays unstable.)

### 7. Python version: the README is wrong
The published `0.2.0` metadata requires **`>=3.12`** and ships only `cp312-abi3` wheels, but the
README (and the `main`-branch `pyproject.toml`, which is already ahead of the release) both say 3.10
— the README literally prints `uv tool install --python 3.10 "nemo-switchyard[cli]"`, which cannot
resolve. Use 3.12. Harmless for the workshop image; would burn a learner following upstream docs, so
it is worth one line in `meet_switchyard.md`.

### 8. Hosted model ids — all present, no substitution needed
`GET /v1/models` (102 models, 2026-08-13) contains **`nvidia/nemotron-3.5-lightning-30b-a3b`** and
**`nvidia/nemotron-3-super-120b-a12b`** exactly as the Global Constraints specify. Also live and
usable as the judge: `nvidia/nemotron-3-nano-30b-a3b`. (The §8.2 fallback plan is not needed today;
`smoke_switchyard.sh` is the canary that will catch it if that changes.)

### 9. Two attribution vocabularies
Gateway → upstream **model id** (`nvidia/nemotron-3.5-lightning-30b-a3b`); libsy →
**target name** (`weak`). Anything that renders both (the Routing Client) needs a mapping.

### 10. Upstream velocity, quantified
The repo self-describes as **pre-alpha**, "expected to change significantly before v1.0", and shipped
`v0.1.0 → v0.2.0-rc.1 → v0.2.0-rc2 → v0.2.0` inside days. `main` has already diverged from the 0.2.0
release (different `requires-python`, different extras). **Read shipped-package behaviour, never
`main`'s docs**, and re-run `smoke_switchyard.sh` before any event. The §8b churn playbook is
justified — if anything, understated.

---

## Reproducing this

```bash
set -a; source secrets.env; set +a                       # NVIDIA_API_KEY
python3.12 -m venv /tmp/claude-syd-venv
/tmp/claude-syd-venv/bin/pip install "nemo-switchyard[cli]==0.2.0"
bash code/8-agent-routing/scripts/install_switchyard.sh  # pinned + sha256-verified install
bash code/8-agent-routing/scripts/smoke_switchyard.sh    # config validation + live routed call
```
