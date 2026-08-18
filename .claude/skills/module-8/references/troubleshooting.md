# Module 8 Troubleshooting — tutor reference

Environment problems, not exercises — **give concrete, direct fixes** (tutor-policy rule 7).
An unfilled blank is an *exercise* (guide it); a filled blank that errors, a dark tile, a dead
gateway or a failed install is *environment* (fix it). All commands run from
`code/8-agent-routing/` unless noted. ⚠️ **Never run a billed suite to "check" something** — each
`--exercise N` is 18–51 live calls.

## The NVIDIA key (this module's most predictable failure)
- **Symptom:** live queries fail; `serve_gateway.sh` refuses to start and prints the exact
  `source` line with the absolute path filled in; the Routing Client shows a **persistent
  banner** (not a toast) — but only when the key is missing from `secrets.env` too (see below).
- **Fix for terminals:** `set -a; source /project/secrets.env; set +a`
- ⚠️ **Keep the path absolute.** `secrets.env` lives at the **project root**, so sourcing it by
  bare filename fails from the lab directory. Both the script and the client banner resolve the
  absolute path for you.
- ⚠️ **Which process matters.**
  - **The gateway** reads the key from **its own process environment** via `api_key_env` — so it
    must be exported in the terminal you run `serve_gateway.sh` from. Exporting it in the lab's
    terminal does nothing for it. This is the case that still genuinely depends on the terminal.
  - **The Routing Client's server** needs no terminal: it reconciles `NVIDIA_API_KEY` with
    **`/project/secrets.env` on every status poll and before every live query**. Saving the key
    with the **Secrets Manager tile** (or editing the file directly) reaches a tile that is
    already open within a few seconds — **no relaunch**. A key exported in the launch
    environment wins over the file; the banner appears only when the key is in **neither**
    place, and it takes itself down once the file has one.
- **Verify from anywhere:** `curl -s localhost:4000/v1/models`.

## The Routing Client
- **Chips greyed out / `systems online: 0/5`** — the design, not a fault: each chip is titled with
  the exercise that unlocks it. `probe_unlocks(module)` in `routing_lab.py` is the check — it
  calls each exercise's entry point with **fake inputs** (never a token, never a socket) and
  returns `False` for any blank still raising `NotImplementedError`.
- ⚠️ **Notebook-track learners:** the client reads **`routing_lab.py`**, not the notebook. Paste
  each finished function back into the `.py` or the tile stays dark no matter how green the
  notebook is.
- **The gateway chip** isn't probed (Ex4's blank is a config file) — **gateway liveness stands in
  for it**, so it lights the moment the client can reach `:4000`.
- **A "`routing_lab.py` didn't execute" banner** is a *different* failure: the file itself is
  broken (syntax/import), which is not the same as a blank exercise. Unfilled blanks never
  produce this banner, and the banner now carries its own hint line. Two cases:
  - **A missing import** (`ModuleNotFoundError`) is the **tile's interpreter**, never their code
    — the hint says so and names the interpreter. `start_client.sh` probes its candidates
    (`ROUTING_CLIENT_PYTHON` → the Switchyard venv → `python3.12` → `python3`) and runs the
    first that can import the lab's deps, so this banner means **no** candidate could. Fix:
    `bash scripts/install_switchyard.sh` (it prepares an interpreter with the SDK *and* the
    lab's runtime deps), then **relaunch the tile** — it prefers that interpreter.
  - **Anything else** is their file: run `python3 routing_lab.py --exercise 1` and read the
    traceback.
- **Chips didn't light after solving an exercise** — they should, **live**: the client re-reads
  `routing_lab.py` every ~5 s, so no relaunch is ever needed for unlocks. If a solved exercise
  stays locked, either the work isn't in the `.py` (notebook track — paste it back) or a banner
  above the yard is reporting why the file can't execute.
- **"Where do I run the exercises in the client?"** — nowhere, by design: the client is the
  **end-of-lab recap and playground** (single queries only, one live call per Send). Every
  suite, demo, and scoreboard runs from the lab files (`python3 routing_lab.py --exercise N`
  or the notebook). A greyed strategy chip names the exercise that unlocks it; a finished lab
  reads `systems online: 5/5` at first open.
- **The tile won't open / you're headless** — the client is a window, never a requirement. Every
  exercise has a **Run it** command that prints the same numbers in a terminal, and the module is
  complete without ever opening the tile. In a sandbox with no forwarded port, that's the path.
- **A stray `[route → efficient]` line in the server's stdout** is the Ex3 unlock probe's trace —
  expected noise, not an error.

## The Switchyard SDK
- **Symptom:** `⚠️ switchyard SDK unavailable — using MockRouter` on every Exercise 3 run, or the
  client's SDK banner. **This is expected and deliberately loud** — the degraded path still
  teaches (deterministic, the trace still prints), but it decides with a heuristic rather than the
  stage scorer, and it says so every time.
- **Fix:** `bash scripts/install_switchyard.sh`. It prefers your ambient environment and falls
  back to a dedicated venv when ambient is **PEP 668 / externally managed**, verifies the wheel's
  sha256, and prints the interpreter it used. `bash scripts/install_switchyard.sh --print-python`
  prints only that path. ⚠️ **`--print-python` is not a read-only probe** — on a cold box that
  call performs the whole install.
- ⚠️ **Relaunch the client tile after installing** — `sdk_available` is read **once at server
  startup** (reloading the shim mid-session would swap the `MockRouter` class out from under an
  in-flight query).
- ⚠️ **Needs Python ≥ 3.12** — only `cp312-abi3` wheels are published; upstream's README still
  prints a 3.10 install line that cannot resolve.
- ⚠️ **Never `pip install switchyard`** — that's an unrelated networking-course package (and
  `switchyard-dev` is unrelated too). The right one is **`nemo-switchyard[cli]==0.2.0`**.
- **"It installed but the lab still can't import it"** — wrong interpreter. Ask which Python the
  lab is running under; the installer's `--print-python` names the one it used. When that path is
  the fallback **venv**, tell them to run the lab *with it* —
  `"$(bash scripts/install_switchyard.sh --print-python)" routing_lab.py --exercise 3`. The
  installer also puts the lab's own runtime deps (`langchain-nvidia-ai-endpoints`,
  `python-dotenv`) in that venv precisely so this works. `start_client.sh` probes rather than
  assumes: a venv that could import the SDK but not the lab is skipped for an interpreter that
  can run both, so that state no longer leaves the client dark at `0/5`.

## The gateway (Exercise 4)
- ⚠️ **There is no `switchyard-server` binary and no `--dry-run` flag.** The same Rust gateway is
  embedded in the pip wheel. Don't send anyone to `switchyard serve` either — that's a *YAML*
  routing-profile path, a different config dialect.
- **Validate before serving** (loading the config *is* validating it; port 0 binds and releases at
  once; silence means valid):
  ```bash
  "$(bash scripts/install_switchyard.sh --print-python)" -c \
    "from switchyard_rust.server import Server; Server('routes.toml', port=0).close()"
  ```
- **Serve:** `bash scripts/serve_gateway.sh routes.toml` (Ctrl-C to stop) — with the key exported
  in **that** terminal. Then `curl -s localhost:4000/v1/models` → one route id, `switchyard`; and
  `curl -s localhost:4000/v1/stats` → the gateway's own meter.
- **Port 4000 already in use** — usually an earlier gateway that wasn't Ctrl-C'd. Free it, or
  serve elsewhere with `PORT=… bash scripts/serve_gateway.sh routes.toml` — but
  `constants.GATEWAY_BASE_URL` points both the lab and the client at `localhost:4000`, so moving
  the port means the lab won't find it.
- **"It starts but routes nothing" / `⚠️ /v1/stats reports no tiers`** — the two traps, both of
  which *look healthy and bill like frontier-only*:
  - **TRAP 1 — the judge needs its own model id.** Two targets naming the same model on the same
    `llm_client` are deduplicated on (client, model id); one is dropped, the tier split collapses,
    every request lands on `strong`, and `/v1/stats` reports no tiers. Give the judge a distinct
    id (the lab uses Nano 30B) or a second client.
  - **TRAP 2 — the judge must not think.**
    `extra_body = { chat_template_kwargs = { thinking = false } }`. With thinking on it spends its
    whole verdict budget deliberating, never emits the JSON the classifier asked for, and the
    router **doesn't raise** — it falls through to `strong`.
  (Both are pre-commented above the provided judge target in `routes.toml.template`; both are
  recorded as Deviations 5 and 6 in `docs/specs/switchyard-api-notes.md`.)
- **Nothing ever escalates** — almost always the session. Single-shot traffic, and any request
  without an `x-switchyard-session-id` header, is its own session of length one. **Escalation
  judges runs, not prompts.**
- **The lab can't reach the gateway** — is it actually up (`curl /v1/models`), on 4000, and in a
  terminal that's still alive? The client probes with a bare TCP connect, so a *bound but broken*
  server can still light the chip.

## Exercise 4b (optional — Docker + an NVIDIA GPU)
`bash scripts/serve_local_nim.sh` — Module 2's NIM runbook parameterized (`docker login nvcr.io`,
a cached model volume, a container on the workbench network). When it's up: uncomment the two
`Exercise 4b` blocks at the bottom of **your** `routes.toml`, delete the hosted `[targets.weak]`,
restart the gateway, and watch `watch -n 0.5 nvidia-smi` in a third terminal — easy turns light
your GPU, hard turns escalate to the hosted 120B and leave it idle.
**No Docker or GPU? Skip 4b entirely — 4a is the full exercise**, and nothing later depends on it.

## Cost surprises (this lab spends real money — ~150 live calls end to end)
- **`--exercise 2` re-runs Exercise 1's two baselines first** (~24 of its ~51 calls), so it bills
  them again — deliberately: a routed row means nothing without its controls on the same screen.
  It happens even when 2a/2b are still blank, once Ex1 is filled.
- **`--exercise 5` is the longest run in the lab** (≈51 calls, 4–12 min).
- **A suite that looks hung is usually just a suite** — each exercise prints its own call count
  and expected duration.

## "It ran, but the numbers look wrong"
- **`insufficient data` from `routing_verdict`** — a **real state, not a bug**: the verdict
  needs a `strong_only` baseline plus one routed strategy in its results; hand it fewer and it
  says so instead of inventing a percentage.
- **`12 → strong / 0 → efficient`** (or the reverse) — a **collapsed router** that still prints a
  plausible bill. Check the classifier's thinking-off setting and the verdict parsing before
  anything else; the split line is the health check.
- **Costs/splits differ from the page** — expected. The page's figures are measured runs with
  published ranges (savings 40–60%, mix 83/17→92/8, tax 4–6%); the split wanders run to run, and
  the **latency** column is noise-dominated while the **cost ratio** is stable.
- **All strategies score 12/12** — the suite isn't hard enough to price accuracy. That's the
  module's own stated limit, not a broken run.

## Maintainer-side (not learner-facing)
`bash scripts/smoke_switchyard.sh` is the canary: fresh pinned install → validate the answers
TOML → one live routed call through the gateway → one direct hosted call → drift vs the latest
published version. It exits non-zero on exactly the two ways this stack fails *while still
returning a valid response* (the collapsed tier split, and the thinking judge). Run it before
every event and on every pin bump; the bump runbook is in `code/8-agent-routing/README.md`.
