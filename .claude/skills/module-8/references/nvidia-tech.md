# Module 8 NVIDIA technologies — tutor reference

What each technology is, its role in *this* module, and where to learn more. Module 8's
NVIDIA surface is small and deep: one router (**NeMo Switchyard**), the **Nemotron** models it
routes between, and **NIM** serving them. Most of the confusion is about what Switchyard *is*
(three surfaces, one core) and what is **not installable today** — be precise about both.

## NeMo Switchyard — the router

- **What:** NVIDIA's open-source model router. **Apache-2.0**, source of truth at
  [github.com/NVIDIA-NeMo/Switchyard](https://github.com/NVIDIA-NeMo/Switchyard). It shipped
  alongside **Nemotron 3.5 Lightning** (launch: 2026-08-11) and is what the whole module runs on.
- **Status: pre-alpha.** Upstream self-describes as *"Experimental software. Not for production
  use."*, "evolving rapidly", with the API and algorithms "expected to change significantly
  before we reach v1.0". It shipped `v0.1.0 → v0.2.0-rc.1 → v0.2.0-rc2 → v0.2.0` inside days,
  and `main` has already diverged from the 0.2.0 release. **Read shipped-package behaviour,
  never `main`'s docs.** The module handles this by pinning; the page says so out loud (a layer
  moving this fast is evidence of the thesis, not a caveat to hide).
- **The pin:** `nemo-switchyard[cli]==0.2.0`, installed by
  `code/8-agent-routing/scripts/install_switchyard.sh` — **THE pin record**: package version,
  per-wheel sha256s, and the three model ids all live there (mirrored into `constants.py` for
  what the lab code reads). Every wheel is `cp312-abi3`, so **Python ≥ 3.12 is required**;
  upstream's README still prints a 3.10 install line that cannot resolve. Linux aarch64 and
  x86_64 wheels both exist (manylinux2014) — no arch problem on the workshop image or a
  GB10/Spark box. Two top-level packages install: `switchyard` (Python) and `switchyard_rust`
  (loaders over a ~25 MB compiled Rust extension — the algorithms *and* the whole gateway live
  in that `.so`; there is no pure-Python fallback).

### Three surfaces, one routing core
| Surface | What it is | Where in the module |
|---|---|---|
| **The library** — `switchyard.libsy` | Build targets + an algorithm **in your own process**. The router decides; your code still owns the call and the transport. | **Exercise 3**, via `switchyard_shim.py` |
| **The gateway** — `switchyard_rust.server.Server` | An OpenAI-compatible server in front of your app: the app asks for the model `switchyard` and the yard picks. **Embedded in the pip wheel** — there is **no separate binary to install** and **no `--dry-run` flag**. | **Exercise 4**, via `scripts/serve_gateway.sh` |
| **The launcher** — `switchyard launch claude \| codex \| openclaw` | Starts one of Module 7's harnesses already pointed at a router. | Named on the page; not exercised |

- **The module's only SDK import is `code/8-agent-routing/switchyard_shim.py`** — deliberate
  churn armor for a pre-alpha dependency. If the upstream surface moves, that one file changes
  and nothing else does; its fallback degrades to a loud `MockRouter` so the exercise still
  teaches while a maintainer catches up.
- **Validating a config** (the `--dry-run` replacement): construct the embedded server on an
  ephemeral port — `Server('routes.toml', port=0).close()`. Loading it *is* validating it.
- **CLI:** `switchyard --version`, `switchyard launch {claude,codex,openclaw}`, and
  `switchyard serve --routing-profiles PATH`. ⚠️ `switchyard serve` takes a **YAML routing-profile
  bundle**, *not* a `routes.toml` — two config dialects ship in one package. **The module teaches
  the TOML one** (what upstream documents and what the Rust gateway consumes); don't send a
  learner to `switchyard serve`.
- **Verified surface, pins, and every deviation from what the docs imply:**
  `docs/specs/switchyard-api-notes.md` (executed, not read off a docs page — dated 2026-08-13,
  nemo-switchyard 0.2.0).

### The algorithms (config `type` names, as the learner writes them)
| Config name | Evidence it reads | Cost of deciding | One-line semantics |
|---|---|---|---|
| `passthrough` | none | free | Sends everything to one target — "no router", as a nameable configuration. The control row. |
| `noop` | none | free | No upstream at all; the offline, config-only case. |
| `random` | none | free | Weighted coin over targets (`weights`, `seed`). Indefensible as policy, excellent as an **A/B instrument**. |
| `llm_classifier` (**capability** mode) | the request text (+ recent turns) | **one small LLM call per turn** | A judge scores **how likely the *efficient* model is to succeed**. **Above `base_threshold` → efficient; below → strong.** Raising the dial demands more confidence, so **more traffic escalates**. |
| `llm_classifier` (**escalation** mode) | the trajectory, per session | one judge call per turn *until it latches* | Every session **starts on `weak`** and moves to `strong` after `escalation.confirmations` consecutive escalate verdicts. **One-way — it never de-escalates.** Sessions are grouped by the `x-switchyard-session-id` header. |
| `stage_router` | tool calls/results the agent already emits — the **text**, not the count | **free** (no second call, no extra round trip) | Scores the recent trajectory and picks a tier. `picker` = `efficient_first` \| `capable_first` (the default tier), `confidence_threshold` = how sure the scorer must be to leave it. |
| learned / **prefill** routers | the model's own **residual stream** from the prefill pass | a **training run** up front, then ~free per call | A small trained head predicts per-target success. Taught on the taxonomy page; **not exercised** — a training run doesn't fit in a 95-minute lab. |

Other `llm_classifier` knobs worth naming: `session_affinity` (pin a session to the tier it
started on), `message_hash_fallback` (backstop for clients that send no session id — **requires
`session_affinity`**; the SDK rejects it otherwise), and abstention (an unusable judge verdict
falls through to the default tier — served, not errored).

**libsy signatures the shim was written against** (0.2.0, verbatim from the installed package):
`LlmTarget(name, client)` · `algorithms.stage_router(capable_target, efficient_target, *, picker,
confidence_threshold, …)` · `algorithms.llm_task_classifier(judge_target, efficient_target,
capable_target, *, config)` · `TaskClassifierConfig(base_threshold, *, session_affinity=False,
message_hash_fallback=False, …)` · `Algorithm.run(request, headers=None)` (async → `(decisions,
response)`). The Python binding **does** call your `LlmClient.call` — libsy owns the decision and
the control flow; you own the transport.

### The `routes.toml` vocabulary (Exercise 4)
`schema_version = 1` (what 0.2.0 speaks) → `[llm_clients.<name>]` (`format` — `openai_chat`,
`anthropic_messages`, or OpenAI Responses; `base_url`; `api_key_env` = the **name** of the env
var, never the key) → `[targets.<name>]` (`id` = upstream model id, `llm_client`, optional
`extra_body`) → `[routes.<name>]` (`id` = the public model id your app puts in `model`, `type`,
plus the algorithm's keys). The gateway is also an **adapter**: it accepts OpenAI Chat,
Anthropic Messages and OpenAI Responses inbound, normalizes them, and speaks whatever dialect
each client declares outbound — inbound and outbound are independent.

## Nemotron — the models being routed between
- **Nemotron 3.5 Lightning 30B** (`nvidia/nemotron-3.5-lightning-30b-a3b`) — the **efficient /
  open / weak** tier. Shipped alongside Switchyard; headline is **4× output speed**. Also the
  lab's `CLASSIFIER_MODEL` (no third model by design). Model card + deploy tab:
  https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b
- **Nemotron 3 Super 120B** (`nvidia/nemotron-3-super-120b-a12b`) — the **strong / capable**
  tier. ⚠️ It **plays the frontier role**; it is not literally a frontier model. The stand-in
  exists so the whole module runs on one free key. In production the strong slot is often a
  closed frontier model at a steeper price — which widens the gap and makes routing pay off *more*.
- **Nemotron 3 Nano 30B** (`nvidia/nemotron-3-nano-30b-a3b`) — the gateway's **judge** target in
  Exercise 4. It gets its own model id **because two targets sharing an id on one client are
  deduplicated** (trap 1), and `extra_body = { chat_template_kwargs = { thinking = false } }`
  because a thinking judge never emits its verdict (trap 2).
- **NIM / API Catalog** — hosted inference at `https://integrate.api.nvidia.com/v1`
  (OpenAI-compatible); one `NVIDIA_API_KEY` covers both tiers and the judge. Exercise 4b swaps
  the weak tier for a **local NIM** on your own GPU — Module 2's runbook, parameterized. The
  router doesn't serve models and the serving stack doesn't pick them.
- **ChatNVIDIA** (`langchain_nvidia_ai_endpoints`) — NVIDIA's LangChain integration; the client
  every direct call in the lab goes through. (LangChain is third-party; this package is NVIDIA's.)

## Ecosystem — direction, not a shopping list
NVIDIA's launch coverage named who was already building on Switchyard:
- **LiteLLM** — adding it as a plug-in to its proxy layer.
- **Kong** — delivering it natively through Kong AI Gateway.
- **Cognition** — running a Switchyard router inside **Devin Desktop** (FrontierCode Main:
  50.6% accuracy at $3.11 mean cost/run, ~28% below the frontier-only baseline, routing between
  Opus 5 and Kimi K2.7 — neither of them NVIDIA's).
- **LangChain** — published the **145-task deep-agent routing benchmark** this module quotes
  throughout (93/7 call share, 21% router tax, ~700 ms/turn, 86.0% → 80.0%).
- **Nous Research** — wiring it into **Hermes**, the harness from Module 7.

> ⚠️ **Not installable today.** There is **no** `langchain-nvidia-switchyard` (404 on PyPI), and
> no LangChain/LiteLLM Switchyard middleware package of any name. Treat the list above as
> ecosystem direction — the honest version in a learner's own code is the shim they wrote in
> Exercise 3. And two **decoy** PyPI packages will install happily and teach nothing:
> `switchyard` (a networking-course framework, unrelated) and `switchyard-dev` (local HTTP
> runtimes for agent worktrees, unrelated). The package is **`nemo-switchyard`**.

## Where Switchyard sits in the workshop's NVIDIA stack
**Nemotron** (models to route to) · **NIM** (serves them wherever you want) · **NemoClaw**
(makes open agents safe to run at all, M6) · **Verified Skills** (portable capability, M7) ·
**NeMo Switchyard** (makes the mix rational — per call, per session, per config file).
Capability that travels, now with a dispatcher.

## Links
- [NeMo Switchyard on GitHub](https://github.com/NVIDIA-NeMo/Switchyard) — Apache-2.0, source of truth
- [Getting started](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/getting_started.md) · [Core concepts](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/core_concepts.md) · [Routing algorithms overview](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/routing_algorithms/overview.md) · [TOML schema reference](https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/reference/toml_schema.md)
- [Route AI agent workloads across models with NVIDIA NeMo Switchyard](https://developer.nvidia.com/blog/route-ai-agent-workloads-across-models-with-nvidia-nemo-switchyard/) — the technical launch post
- [Nemotron 3.5 Lightning and NeMo Switchyard](https://blogs.nvidia.com/blog/nemotron-lightning-switchyard-rtx-dgx/) — the launch story, RTX through DGX
- [LangChain's agent-routing benchmark](https://www.langchain.com/blog/switchyard-agent-routing-benchmark) — the 145-task run behind the headline numbers
- [Boomi: Why Open Model Routing Matters](https://boomi.com/blog/why-open-model-routing-matters/) — routing to a fine-tuned specialist in production
- [Nemotron 3.5 Lightning on build.nvidia.com](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b) — the efficient tier's model card

> **Frequent confusions:**
> - *"Is Switchyard a model?"* No — it's a **router**. It picks which model answers; it never
>   generates a token itself (the judge in `llm_classifier` is a *target*, a model you configure).
> - *"Is Super 120B a frontier model?"* In this lab it **plays** that role. Say "stand-in."
> - *"Do I need a Switchyard server binary?"* No. The gateway is inside the pip wheel.
> - *"Can I put Claude/GPT in the pool?"* Yes — `anthropic_messages` is a first-class client
>   format, so it's a config edit with your own key. Nothing in the module requires it, and the
>   workshop's smoke test doesn't cover it.
