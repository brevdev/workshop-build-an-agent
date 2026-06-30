# Module 6 Troubleshooting — tutor reference

**Triage first.** Environment/runtime (give direct fixes), exercise blank (guide — see
`exercises.md`), or security reasoning (teaching — see `concepts.md`)? The biggest M6
runtime issue is the **NemoClaw control plane** — fixing it is environment work you can
give directly.

## The control plane can be down (the #1 M6 issue)
The live hardening exercises need a working **OpenShell gateway**, the `nemoclaw`/`openshell`
CLIs, and a **socat tunnel** bridging the Workbench container to the host gateway. On some
builds these are degraded ("Live NemoClaw agent isn't the default", `nemoclaw connect` hangs,
`openshell` can't reach the gateway). This is an **environment problem, not the learner's
code.** Steps:
1. **Diagnose:** `python3 code/6-agent-safety/scripts/diagnose-nemoclaw.py` — reports what the
   detection logic actually sees (CLIs present? gateway reachable? sandbox running?).
2. **Re-run the installer (idempotent):** `bash code/6-agent-safety/scripts/install-nemoclaw.sh`
   — if already installed + healthy it just restarts the **socat tunnel** (`127.0.0.1:8080` →
   the Docker-bridge gateway) and exits; if a prior attempt half-failed it cleans up + retries.
   Logs: `/tmp/nemoclaw-tunnel.log`.
3. **Full reset:** `docker rm -f nemoclaw-openshell-gateway` then re-run `install-nemoclaw.sh`.
- The tunnel/gateway plumbing is a workaround for **NemoClaw v0.0.49** specifically (its
  preflight wants :8080 free in the container but its readiness wants to *reach* the gateway).
- **Key reassurance for the learner:** even with the live stack down, the **Python safety-eval
  exercises run against the mock agent + `test_data/` fixtures** — the concept/code learning
  (classify, red-team scoring, judge, suite) is fully doable. The live two of the three agents
  auto-skip (`_check_openclaw_cli()`/`_check_gateway_via_cli()`/`_check_nemoclaw_cli()`/
  `_check_sandbox_running()` gate them).

## Docker & sandbox image
- NemoClaw needs **Docker** (the Workbench mounts the host socket via `/var/run/`→`/var/host-run/`;
  see the `setup-workshop` skill). `install-nemoclaw.sh` builds a ~2.4 GB sandbox image, uploads
  it to the gateway, configures DNS, and launches OpenClaw — minutes on first run.
- **Docker-driver mode vs cluster mode:** this workshop runs OpenShell single-container
  (Docker driver). In-provider **model** swaps (`openshell inference set --model`) work; a full
  **provider** swap (cloud→local Ollama) needs **cluster mode** (the `inference.local` DNS
  refresh path). So "switch to local model didn't stick" via `nemoclaw connect` is expected here.

## Landlock / kernel
- Landlock LSM needs **Linux kernel ≥ 5.13**. Filesystem enforcement (Ex 3 writes failing) won't
  behave as documented on older kernels. `filesystem_policy`/`landlock`/`process` are **static** —
  trying to `openshell policy set` them on a live sandbox is *rejected by design* ("cannot be
  changed on a live sandbox"); recreate the sandbox to change them.

## Inference / credentials / secrets
- `secrets.env` (repo root) needs **`NVIDIA_API_KEY`** (the gateway's Provider record + the judge).
- Inside the sandbox, `NVIDIA_API_KEY` is **intentionally absent** — only `OPENCLAW_GATEWAY_TOKEN`
  (a loopback bearer token, not a vendor key). That's the credential-isolation lesson, not a bug.
- `inference.local` calls failing with HTTP 500 → the gateway couldn't resolve a placeholder
  token (fails closed by design) — check the host-side Provider config.

## Safety-eval code (the Python sidekicks)
- Judge: `ChatNVIDIA(model="nvidia/nemotron-3-super-120b-a12b", temperature=0.0)` — keep temp 0
  for consistent grading. JSON parse should have a **regex fallback** (some judge outputs aren't
  clean JSON), exactly like Module 3.
- **A live three-way run is slow** (~5–10 min per agent, 15–20 min total for 16 probes) — that's
  expected, not a hang; watch per-probe progress. Use the mock alone for fast iteration.
- "My refusal text counts as a failure" → the **refusal-aware gating** (Ex 3) must check the
  *opening* of the response before the injection/path heuristics; the data-leak check stays
  unconditional.
- Helper scripts: `scripts/dump_nemoclaw_probes.py` (inspect probe data),
  `scripts/recompute_with_refusal_logic.py` (re-score existing results with the refusal logic).

## Fake demo data (not an incident)
The red-team `sensitive_strings` (e.g. `SuperSecret123!`, `SSN: 123-45-6789`) and the seeded
workspace files are **fabricated props** for the safety probes — same as Module 5. The point is
to show whether the agent leaks them; explain that purpose, don't treat it as a live breach.

## Conceptual confusions (teaching moments)
- "The Privacy Router should auto-send my PII to a local model" → no — it enforces the operator's
  chosen backend + injects credentials; the **classifier you build** (Ex 5) makes per-request
  decisions. (See `concepts.md`; the module quizzes this twice.)
- "Same pass rate, why does sandboxed score higher?" → defense-in-depth weights kernel blocks
  (1.0, non-defeasible) above prompt refusals (0.7, defeasible).
- "Why didn't the network/FS/process layers stop memory poisoning?" → it's **in-boundary** (a
  permitted `/sandbox` write) — exactly why continuous evaluation exists.
