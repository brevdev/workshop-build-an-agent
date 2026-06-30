# Running Codex Inside a Workbench Container

Codex CLI can be installed inside the project container, enabling in-container vibe coding via the JupyterLab terminal. This page covers setup and the host↔container communication pattern. (For Claude Code, the equivalent guide is `claude-in-container.md` in the Claude skill tree — the two are intentionally parallel.)

## Setup

### 1. Install Codex and clone skills in `postBuild.bash`

```bash
# Install Node.js 20 via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Codex CLI globally (sudo required — postBuild runs as workbench user)
sudo npm install -g @openai/codex

# Optional: clone companion skills into ~/.codex/skills/ so they work outside /project too
# (seeded into the volume on first container start). Project skills in <repo>/.agents/skills/
# are discovered automatically when codex runs from /project — no clone needed for those.
git clone https://github.com/nv-twhitehouse/nvwb-skills /home/workbench/.codex/skills/
```

> **How this interacts with the volume**: `~/.codex/` is mounted as a VOLUME (see step 2). VOLUME mounts are seeded from the image on first use, then persist independently. A build-time clone gets baked into the image — on first container start, the VOLUME is seeded with it. After that, the VOLUME is self-contained; rebuilding the container will not update those skills. Run `git -C ~/.codex/skills pull` inside the container to update them. (The workshop's own tutor skills live in-repo at `/project/.agents/skills/`, so they update with the repo and need no clone.)

### 2. Add a volume mount for `~/.codex/`

```bash
nvwb create mount VOLUME /home/workbench/.codex/ --description "Persistent Codex settings, auth, and skills"
```

This persists Codex's settings, memory, auth, and skills across container rebuilds.

> **Credentials persist (unlike Claude Code).** Codex stores its login in `~/.codex/auth.json` — *inside* the mounted directory. Because `codex login` happens at runtime (not build time), the credential is written into the VOLUME and survives rebuilds, so you do **not** re-auth after each rebuild. (Claude Code keeps credentials in `~/.claude.json` one level up, outside its volume, so it re-auths each rebuild.)

> **Why not mount all of `/home/workbench/`?** NVWB installs pip packages via `pip install --user` into `~/.local/lib/`. Mounting the entire home directory shadows that path, making packages from `requirements.txt` silently disappear after the first rebuild. Mounting only `~/.codex/` avoids the conflict.

### 3. Rebuild and restart

```bash
nvwb build
nvwb close
nvwb open <project>
```

### 4. Launch

```bash
nvwb start jupyterlab
```

Open a terminal in JupyterLab and run `codex`. On first launch, authenticate once with `codex login` (ChatGPT account) or by exporting `OPENAI_API_KEY` — thanks to the `~/.codex/` volume, this persists across rebuilds.

---

## Host ↔ Container Communication (the Bridge)

The project directory is bind-mounted at `/project/` in the container. This means any file written there is immediately visible on the host, and vice versa — no extra mounts needed.

Create a bridge directory once:

```bash
mkdir -p <project-path>/agent-bridge/common-context/
```

Inside the container it appears at `/project/agent-bridge/`.

The `common-context/` subdirectory holds shared task state (`context.md`) and nvwb skill reference files pre-populated by the user — this gives the outer agent working knowledge of Workbench without needing a separate skills installation.

Add an `AGENTS.md` to the project root that points the outer agent at `agent-bridge/` — this bootstraps its awareness of the bridge, the common context, and the communication protocol. See `nvwb-project/references/agent-bridge.md` for a template.

Optional: copy the sandbox hook scripts into `agent-bridge/hooks/` and wire them up in Codex's hooks config to enforce agent constraints (command allowlists, sensitive variable scrubbing, bridge file ownership). See the **Sandboxing with Hooks** section in `nvwb-project/references/agent-bridge.md`.

See `nvwb-project/references/agent-bridge.md` for the full format guide, templates, rules, and Codex / Claude / Cursor differences.

### How it works

**Inner agent** (Codex running in the container via JupyterLab terminal) writes requests to `/project/agent-bridge/inner.md`.

**Outer agent** (running on the user's local machine, in their main session) reads the file, takes action (e.g. runs `nvwb compose down && nvwb compose up`), and writes results to `/project/agent-bridge/outer.md`.

The inner agent reads the response and continues.

Because both sides are agents, communication can be rich prose — not just command names but context, logs, questions, and diagnostic output.

### Example: requesting a compose restart

The inner agent writes to `/project/agent-bridge/inner.md`:
```
I've updated /project/code/server.py to add a /status endpoint.
Please run `nvwb compose down && nvwb compose up` and paste me the
compose logs and the output of `curl http://api:8080/status`.
```

The outer agent runs the commands, then writes to `/project/agent-bridge/outer.md`:
```
Done. Compose restarted cleanly. curl returned: {"status":"ok","uptime":3}
Compose logs showed no errors on startup.
```

---

## What the Inner Agent Can and Cannot Do

| Capability | Inner agent | Outer agent |
|---|---|---|
| Edit files in `/project/` | ✓ | ✓ |
| Run code and tests | ✓ | — |
| `curl` compose services by name | ✓ | — |
| Read `/nvwb-shared-volume/` | ✓ | — |
| Run `nvwb` commands | ✗ | ✓ |
| Restart compose services | ✗ | ✓ |
| Trigger `nvwb build` | ✗ | ✓ |
| Start/stop apps | ✗ | ✓ |

For anything requiring `nvwb`, the inner agent writes a request to the bridge and the outer agent handles it.

---

## Notes

- The `nvwb-wrapper.sh` shell function is not available inside the container — `nvwb` commands must run on the local machine
- Compose services are reachable from the project container by service name (e.g. `http://api:8080/`) via the shared `workbench` network
- Add `agent-bridge/` to `.gitignore` — bridge messages should not be committed
- For remote contexts, the outer agent can access bridge files via SSH — the context name (from `nvwb list contexts`) is also the SSH alias. Workbench adds a matching entry to `~/.ssh/config`, so `ssh <context-name>` works directly
