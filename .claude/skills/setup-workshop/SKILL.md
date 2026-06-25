---
name: setup-workshop
description: This skill should be used when the user wants to set up, install, deploy, bootstrap, or "spin up" the Build-an-Agent workshop (a.k.a. the DevX / DevX-Lab workshop) on local hardware, or says things like "run the workshop locally", "get DevX-Lab running in my browser", "install the workshop on my GPU box", "set up the build-an-agent workshop", or "reproduce the Brev workshop deployment locally". It installs NVIDIA AI Workbench (if needed), clones and builds the project, supplies API keys, configures the GPU/host mounts, starts the DevX-Lab JupyterLab app, and hands back a browser URL. For a local Linux NVIDIA GPU machine — not for provisioning Brev cloud instances.
disable-model-invocation: false
user-invocable: true
---

# Set Up & Run the Build-an-Agent Workshop Locally

Bring a local Linux NVIDIA GPU machine from bare to a browser-accessible
**DevX-Lab** — the workshop's JupyterLab environment for all seven modules. This
reproduces the Brev cloud deployment *minus* its cloud-only plumbing: no
cloud-user detection, and the nginx single-port router + systemd auto-start are
optional rather than default (local users reach the app directly via the
Workbench proxy URL).

## Outcome

A running DevX-Lab reachable at
`http://localhost:<proxyPort>/projects/<name>/applications/DevX-Lab/`
(proxyPort defaults to 10000). On a desktop it can auto-open; on a headless box
it is reached via SSH port-forward.

## When to use / not use

Use on a **local Linux host with an NVIDIA GPU** (x86_64 or aarch64). Trigger
on requests to set up / install / deploy / spin up / run the workshop or
DevX-Lab locally. Do **not** use this to provision a Brev cloud instance — that
is the `brev-cli` / `nvwb` Brev path; this skill is the local analog of the Brev
startup script.

## Required input

- **NVIDIA API key (mandatory).** Free at https://build.nvidia.com (log in →
  "Get API Key"). Every module calls NVIDIA NIM/Nemotron with it. The build
  succeeds without it, but every model call then returns 401.
- **Optional:** `TAVILY_API_KEY` (Module 1 web search), `LANGSMITH_API_KEY`
  (Module 3 tracing).
- Note: `secrets.env` is **gitignored**, so a fresh clone never contains keys —
  they must be supplied. Prompt the user for the NVIDIA key if it is not already
  provided or present in an existing `secrets.env`.

## Procedure

Drive these steps in order. Each script lives in `scripts/`. Report progress and
the final URL to the user.

### 1. Preflight

Run `scripts/preflight.sh`. It is read-only and prints PASS/WARN/FAIL with a
verdict (exit 1 if blocking). Resolve any **FAIL** (disk < 40 GB, no sudo, wrong
OS/arch). GPU/docker/Workbench/network **WARN**s are expected on a fresh box and
are handled by setup. If sudo is not passwordless, run `sudo -v` now — the
background setup cannot answer a password prompt.

### 2. Obtain the NVIDIA API key (and any optional keys)

If no `secrets.env` exists for the project yet, ask the user for their NVIDIA API
key (and optionally Tavily/LangSmith). There are two ways to get it in place —
pick based on whether the project is already cloned:

- **Not cloned yet (typical):** pass the key to setup.sh via its environment so
  it writes `secrets.env` *after* cloning (avoids the chicken-and-egg of the file
  living inside the not-yet-cloned project). See step 3.
- **Already cloned, or the user prefers to manage the file:** copy
  `assets/secrets.env.template` to `<project>/secrets.env`, fill in the key with
  the **Write tool** (never echo a key in a shell command — it leaks into history
  and process listings), then `chmod 600` it.

If a valid `secrets.env` already exists, no key is needed.

### 3. Run setup in the background, then wait

The first build downloads CUDA 12.8 and compiles `mamba-ssm`/`causal-conv1d` from
source — **20-45 minutes**, far beyond the foreground command limit. Launch
`scripts/setup.sh` as a **background** command, passing keys via the environment:

```bash
NVIDIA_API_KEY='nvapi-…' bash .claude/skills/setup-workshop/scripts/setup.sh
# optionally also: TAVILY_API_KEY='…' LANGSMITH_API_KEY='…'
# Not in the repo? Use the symlinked path: ~/.claude/skills/setup-workshop/scripts/setup.sh
```

setup.sh is idempotent: it starts docker, installs Workbench (if absent),
activates the local context, clones (if absent), writes `secrets.env`, generates
the GPU CDI spec, configures the `/run/cdi/` and `/var/host-run/` mounts, builds,
and starts DevX-Lab. It streams to `~/.workshop-setup.log` and ends with exactly
one sentinel:

- `=== WORKSHOP SETUP COMPLETE ===`
- `=== WORKSHOP SETUP FAILED: <reason> ===`

While it runs, check progress with `tail -n 30 ~/.workshop-setup.log`. The
harness re-invokes when the background command exits — then read the log tail to
find the sentinel.

### 4. On completion

- **COMPLETE** → read `~/.workshop-app-url` for the URL and surface it with the
  right access instructions for the user's situation (see step 5).
- **FAILED** → read the reason plus the log tail, consult
  `references/troubleshooting.md`, fix the root cause, and re-run setup.sh (it
  resumes idempotently). The most common failures: missing/placeholder
  `secrets.env` (401s), a network drop mid-build, or a missing `/run/cdi` source.

### 5. Tell the user how to open it

Determine the box type and give matching instructions (full detail in
`references/access.md`):

- **Desktop with a browser:** open the URL (or re-run `start-app.sh` without
  `--no-browser` to auto-open).
- **Headless GPU box (most common):** the proxy binds to localhost, so forward
  it — `ssh -N -L 10000:localhost:10000 <user>@<host>` — then open the URL on the
  laptop.
- **Need a shareable link:** `nvwb activate local --external-access` then
  `nvwb create share-url DevX-Lab` (≈48-hour public URL).

### 6. Offer optional persistence

Only if the user wants Brev-style behavior, offer the extras in
`references/persistence.md`: a **systemd** unit that auto-starts DevX-Lab on
reboot, and/or an **nginx** router that serves a clean single port (:8888) with
the Host-header rewrite. Neither is required for normal local use.

## Restart / re-resolve later

To restart the app after a reboot or to re-print the URL, run
`scripts/start-app.sh` (it resolves the project, starts the app idempotently, and
rewrites `~/.workshop-app-url`). No rebuild needed unless package/build files
changed.

## nvwb gotchas (and why the scripts look the way they do)

- `nvwb` is a **shell function**, not a binary. Scripts must
  `source ~/.local/share/nvwb/nvwb-wrapper.sh` (after `~/.bashrc`). Never run
  `timeout nvwb …` — `timeout` execs a binary and can't see the function. The
  scripts here source the wrapper for exactly this reason.
- The `/run/cdi/` and `/var/host-run/` host mounts are declared in `spec.yaml`,
  so their **sources must exist before `nvwb build`/`start`** — setup generates
  the CDI spec first to avoid a cryptic "mount source not found".
- `secrets.env` / `variables.env` are **runtime** config: after editing them,
  restart the container (`nvwb close` then `nvwb open`) — a rebuild is not needed.
  Package/`apt.txt`/build-script changes do need `nvwb build`.
- Scripts pass `--context local --project <path>` explicitly instead of relying
  on an "open" project, so they work non-interactively.

## Resources

### scripts/
- **`preflight.sh`** — read-only environment readiness check (run first).
- **`setup.sh`** — idempotent end-to-end bootstrap; run in the background.
- **`start-app.sh`** — (re)start DevX-Lab and resolve the URL; reused by setup
  and the optional systemd unit.

### references/
- **`troubleshooting.md`** — build failures, 401s, mounts/CDI, GPU, docker,
  ports, clean-slate reset.
- **`access.md`** — desktop / headless port-forward / share-url / nginx access
  modes and how to verify the app is up.
- **`persistence.md`** — optional systemd auto-start and nginx :8888 router.

### assets/
- **`secrets.env.template`** — the keys file to fill in (NVIDIA required).
- **`nvwb-workshop.service.template`** — systemd unit (placeholders to substitute).
- **`nginx-workshop.conf.template`** — single-port router (placeholders to substitute).

### Related skills (bundled in this repo)
- **`nvwb`** — full AI Workbench CLI reference (contexts, clone, build, apps,
  mounts, env vars). Consult it for any nvwb command this skill invokes.
- **`nvwb-project`** — in-container project awareness for `.project/spec.yaml`;
  useful once working inside DevX-Lab. See `.claude/skills/VENDORED.md` for
  provenance and re-sync.
