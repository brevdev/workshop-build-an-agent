# Module 8 — Agent Routing 🛤️

**The big idea:** frontier-vs-open is a false binary. Every agent call is a purchase, and most of them do not need the expensive model. This module puts a meter on every call, then routes each one to the model that should answer it — three different ways, from a classifier you write by hand to a config file the application never reads.

---

## Run it in 3 steps

```bash
# 1. Set your NVIDIA key (get one free at build.nvidia.com)
export NVIDIA_API_KEY=nvapi-xxxxxxxx

# 2. Install what the lab needs
pip install -r ../../requirements.txt        # the model client
bash scripts/install_switchyard.sh           # the router — Exercises 3 and 4

# 3. Do the exercises
python3 routing_lab.py --exercise 1
```

Seven TODOs across five exercises, in order: `--exercise 1` → `5`. Every exercise prints a meter, and the numbers *are* the lesson.

> Prefer notebooks? Open **`routing_lab.ipynb`** instead. Stuck? Every answer is in `routing_lab.answers.py`, and behind the 🆘 peeks on the lab page.

---

## The 5 exercises

| # | You build | In one line | Run it |
|---|-----------|-------------|--------|
| 1 | The model pool and the bill meter | Two models, one meter: what the same 12 tasks cost on each | `python3 routing_lab.py --exercise 1` |
| 2 | A hand-rolled classifier router | A cheap model reads the request first and picks the lane — and that call is the **router tax** | `python3 routing_lab.py --exercise 2` |
| 3 | The same decision, from a library | Switchyard's stage router reads the trajectory the agent already produced, so the decision costs no extra call | `python3 routing_lab.py --exercise 3` |
| 4 | The same decision, out of the app | `routes.toml` owns the policy; the app asks for one route id and is never told which model answered | `python3 routing_lab.py --exercise 4` |
| 5 | The verdict | Accuracy, spend, the open/frontier mix, and what the router itself cost | `python3 routing_lab.py --exercise 5` |

Exercise 4's blank is a **config file, not Python**, and it needs the gateway running in a second terminal:

```bash
# terminal 2
cp routes.toml.template routes.toml          # then fill in its TODOs
export NVIDIA_API_KEY=nvapi-xxxxxxxx         # the gateway reads the key from THIS terminal
bash scripts/serve_gateway.sh routes.toml    # serves on :4000 — Ctrl-C to stop
```

```bash
# terminal 1
python3 routing_lab.py --exercise 4
curl -s localhost:4000/v1/models             # what the gateway serves
curl -s localhost:4000/v1/stats              # its own meter, including the router tax
```

Exercise 4b is optional and needs Docker plus an NVIDIA GPU: `bash scripts/serve_local_nim.sh` swaps the efficient tier for a local NIM, so easy turns run on your own silicon. No Docker or GPU? 4a is the full exercise.

---

## What's in this folder

```
routing_lab.py            ← do the exercises here (seven TODOs)
routing_lab.answers.py    ← the completed version
constants.py              ← model ids, PRICING, endpoints, strategy names — the single source
switchyard_shim.py        ← the ONLY file that imports the Switchyard SDK
routes.toml.template      ← Exercise 4's blank (commented skeleton)
routes.toml.answers       ← the completed gateway config
test_data/                ← the 12-task suite: 6 commodity, 6 frontier
scripts/
  install_switchyard.sh   ← THE pin record: versions, sha256s, model ids
  serve_gateway.sh        ← Exercise 4: serve a routes.toml on :4000
  serve_local_nim.sh      ← Exercise 4b: the local-NIM tier
  smoke_switchyard.sh     ← maintainer canary
tests/                    ← maintainer-side pytest, run against the .answers module
```

Shipping with the rest of the module: the notebook twins (`routing_lab.ipynb`, `routing_lab.answers.ipynb`), the Routing Client (`routing_client/`), and the web module (`.devx/8-agent-routing/`).

Your copied `routes.toml` is git-ignored — the `.template` and `.answers` files are the tracked ones.

## The Routing Client

`probe_unlocks(module)` in `routing_lab.py` is this module's unlock check. It calls each exercise's entry point with fake inputs — never a token, never a socket — and returns `{"ex1": …, "ex2": …, "ex3": …, "ex5": …}`, `False` for any exercise whose blank still raises `NotImplementedError`. Exercise 4's blank is a config file rather than Python, so it is not probed; gateway liveness stands in for it.

The **Routing Client** reads that dict: a JupyterLab launcher tile that renders your routing decisions live, one capability lighting up per blank you fill. It is a window, not a wizard — it holds no routing logic of its own, it imports yours. It ships with the rest of the module.

## Read the lesson

The full guided walkthrough (tokenomics, the routing taxonomy, the diagrams) is the web module — launch **"8. Agent Routing"** from the JupyterLab launcher, or serve it locally:

```bash
cd ../../.devx/8-agent-routing && python3 -m http.server 8138
# then open http://localhost:8138
```

---

## Maintainer

### Tests

The tests import the `.answers` module and run entirely offline — fake chat clients, no network, no key. Ambient python on this image is PEP 668 / externally managed, so pytest lives in the Switchyard venv rather than on the system interpreter:

```bash
PY=$(bash scripts/install_switchyard.sh --print-python)
"$PY" -m pip install pytest langchain-nvidia-ai-endpoints   # one-time: neither is a switchyard dep
"$PY" -m pytest tests/ -v
```

Once those are in the venv, the whole suite is one line:

```bash
$(bash scripts/install_switchyard.sh --print-python) -m pytest tests/ -v
```

### The canary

```bash
bash scripts/smoke_switchyard.sh
```

Fresh pinned install → validate the answers TOML → one live routed call through the gateway → one direct hosted call → drift vs the latest published version. Run it before every event and on every bump. It exits non-zero on the two ways this stack fails *while still returning a perfectly valid response*: the tier split collapsing (two targets colliding on one model id), and the judge burning its verdict budget on chain-of-thought.

### Pin-bump runbook

Pins are single-sourced. Package version, sha256s and the three model ids live in `scripts/install_switchyard.sh`; everything the lab code reads lives in `constants.py`. Never bump ad hoc — do this, in order:

1. **Bump the pin** in `scripts/install_switchyard.sh`: `SWITCHYARD_PIP_PIN`, `SWITCHYARD_VERSION`, and the `SHA256_*` block (re-download and re-hash every wheel).
2. **Run the canary**: `bash scripts/smoke_switchyard.sh`. It must exit 0.
3. **Run the answers end to end**: `python3 routing_lab.answers.py --exercise 1` through `--exercise 5`. Exercise 4 needs the gateway up in a second terminal.
4. **Recalibrate the printed numbers** if the outputs moved. The costs, the routing split and the 🧾 receipt are quoted in the lab page and in the module's close — stale numbers there are the failure this step exists to catch.
5. **Update the version stamp** in the `meet_switchyard.md` aside, so the page names the version that is actually installed.

If the SDK's *surface* changed rather than just its version, `switchyard_shim.py` is the only file that imports it — fix it there and nothing else moves. Its fallback is deliberate: an unusable SDK degrades to `MockRouter` behind a loud banner, so the exercise still teaches while you catch up.

Built on NVIDIA Nemotron + [NVIDIA NeMo Switchyard](https://github.com/NVIDIA-NeMo/Switchyard).
