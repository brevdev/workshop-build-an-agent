---
name: nvwb-project
description: Apply when working in a directory containing .project/spec.yaml — provides NVIDIA AI Workbench project awareness for in-container development. This skill provides context about project structure, environment configuration, and rebuild/restart requirements.
user-invocable: false
---

# NVIDIA AI Workbench — In-Container Project Awareness

This skill activates when Codex is working inside an AI Workbench project container (detected by `.project/spec.yaml` existing in or above the current working directory).

## Detection

If `.project/spec.yaml` exists in the project root, this is a Workbench project. Read it first to understand the project's layout, apps, mounts, and resources.

## Key Facts

- The project root is bind-mounted at `/project/` inside the container
- The `nvwb` CLI is **NOT available inside the container** — all `nvwb` commands must run on the user's local machine (the control plane)
- This container may be running locally or on a remote — it does not matter for in-container work; the project files are always at `/project/`
- Code in layout directories is live-mounted — edits take effect immediately
- The environment variable `AI_WORKBENCH_FLAG=true` may be set to detect Workbench context
- Compose services are reachable by service name (e.g. `curl http://api:8080/`) via the shared `workbench` network

## What's Safe to Edit

**Freely editable** — no action needed:
- Any files in layout directories (code/, data/, models/ or custom paths from `spec.yaml`)
- Application code, scripts, notebooks

**Requires rebuild** — inform user to run `nvwb build` on the host:
- `apt.txt` — system packages
- `requirements.txt` — pip packages
- `preBuild.bash` — pre-install build script
- `postBuild.bash` — post-install build script

**Requires restart** — inform user to run `nvwb close` then `nvwb open` on the host:
- `variables.env` — runtime environment variables
- Mount configuration changes in `.project/spec.yaml`
- App definitions in `.project/spec.yaml`

**Edit carefully** — validate format:
- `.project/spec.yaml` — do not break YAML structure; suggest `nvwb validate project-spec` after changes

## When Informing the User

After editing a build-time or runtime file, always tell the user what action is needed. Examples:

> I've updated `requirements.txt` to add the `transformers` package. You'll need to run `nvwb build` on the host to rebuild the container with this change.

> I've added `CUDA_VISIBLE_DEVICES=0` to `variables.env`. This will take effect after a container restart — run `nvwb close` then `nvwb open` on the host.

## Compose Awareness

If `compose.yaml` or `docker-compose.yaml` exists, multi-container services may be running alongside the project container:
- Services communicate over a shared Docker network — use service names as hostnames (e.g. `http://api:8080/`)
- `/nvwb-shared-volume/` is shared between containers
- Changes to compose files require `nvwb compose down` + `nvwb compose up` on the host — request this via the bridge if running as inner agent
- Compose services exposed through the Workbench proxy use `NVWB_TRIM_PREFIX=true` as an environment variable in the service definition (not in spec.yaml)

## Host↔Container Bridge

If `/project/agent-bridge/` exists, this project is set up for communication between inner agent (here, in the container) and outer agent (on the user's local machine, where `nvwb` is installed).

**When you need a local-machine action** (compose restart, rebuild, `nvwb` command):
1. Read `common-context/context.md` for current task state
2. Write a clear request to `/project/agent-bridge/inner.md`
3. Wait for the user to relay it to outer agent on their local machine
4. Read the response from `/project/agent-bridge/outer.md`

**Rules**: Do not copy files into or out of `agent-bridge/` — it is a communication channel, not a file staging area. The content of `inner.md` and `outer.md` is unrestricted — include logs, snippets, and diagnostics as needed.

**Sandbox**: If hooks are configured, your actions are enforced — `nvwb` commands are blocked (use the bridge), sensitive environment variables are scrubbed from your shell commands, writes inside `agent-bridge/` are restricted to your designated files, and reads of sensitive files and hook configuration are blocked. Do not attempt to modify hook configuration or settings files.

Note: if this project is running in a remote context, the bridge files live on the remote machine. The context name (from `nvwb list contexts`) is also the SSH alias — Workbench adds a matching entry to `~/.ssh/config`. Outer agent can SSH directly using the context name to read and write bridge files without involving the user as a relay.

Requests can be rich prose — include what you changed, what you need done, and what you want reported back (logs, curl output, etc.).

See `references/agent-bridge.md` for templates and the full format guide.

## Runtime Constraints

**`sudo` is NOT available in the running container** — the container runs as the `workbench` user without elevated privileges at runtime. If a task requires system-level changes, it must go in `preBuild.bash` or `postBuild.bash`.

## Build Script Constraints

Build scripts (`preBuild.bash`, `postBuild.bash`) run during container image build:
- They CANNOT reference `/project/` — the project directory is not mounted during build
- Available variables: `$NVWB_UID`, `$NVWB_GID` for file ownership
- **Both scripts run as the `workbench` user (not root)** — any write to a system directory requires `sudo`. This includes `mkdir`, `npm install -g`, writing to `/usr/local/`, etc. Shell redirections (`>`, `>>`) also run as `workbench`, so use `sudo tee` instead of `sudo command > /path`.

## References

See `references/config-files.md` for detailed information about each configuration file.
