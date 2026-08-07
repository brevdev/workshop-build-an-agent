# Running Claude Code Inside a Workbench Container

Claude Code can be installed inside the project container, enabling in-container vibe coding via the JupyterLab terminal. This page covers setup and the host↔container communication pattern.

## Setup

### 1. Install Claude Code and clone skills in `postBuild.bash`

```bash
# Install Node.js 20 via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Claude Code globally (sudo required — postBuild runs as workbench user)
sudo npm install -g @anthropic-ai/claude-code

# Clone skills into ~/.claude/skills/ (seeded into the volume on first container start)
git clone https://github.com/nv-twhitehouse/nvwb-skills /home/workbench/.claude/skills/
```

> **How this interacts with the volume**: `~/.claude/` is mounted as a VOLUME (see step 2). VOLUME mounts are seeded from the image on first use, then persist independently. The clone runs at build time and gets baked into the image — on first container start, the VOLUME is seeded with it. After that, the VOLUME is self-contained; rebuilding the container will not update the skills. Run `git -C ~/.claude/skills pull` inside the container to get updates.

### 2. Add a volume mount for `~/.claude/`

```bash
nvwb create mount VOLUME /home/workbench/.claude/ --description "Persistent Claude settings and skills"
```

This persists Claude's settings, memory, and skills across container rebuilds. It deliberately excludes `~/.claude.json` (the credentials file, which lives one level up), so you will re-auth after each rebuild — the API key is reusable.

> **Why not mount all of `/home/workbench/`?** NVWB installs pip packages via `pip install --user` into `~/.local/lib/`. Mounting the entire home directory shadows that path, making packages from `requirements.txt` silently disappear after the first rebuild. Mounting only `~/.claude/` avoids the conflict.

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

Open a terminal in JupyterLab and run `claude`. On first launch after each rebuild, Claude Code will prompt for an API key — the key is reusable, so copy it from a previous session or your Anthropic console.

> **Why re-auth on each rebuild?** Claude Code stores credentials in `~/.claude.json` under `/home/workbench/`. Mounting `/home/workbench/` as a VOLUME would persist credentials, but it also shadows the image layer where NVWB installs pip packages via `pip install --user` — packages added to `requirements.txt` after the first build silently disappear at runtime. The trade-off: skip the home volume mount, accept re-auth per rebuild.

---

## Host ↔ Container Communication (the Bridge)

The project directory is bind-mounted at `/project/` in the container. This means any file written there is immediately visible on the host, and vice versa — no extra mounts needed.

Create a bridge directory once:

```bash
mkdir -p <project-path>/agent-bridge/common-context/
```

Inside the container it appears at `/project/agent-bridge/`.

The `common-context/` subdirectory holds shared task state (`context.md`) and nvwb skill reference files pre-populated by the user — this gives the outer agent working knowledge of Workbench without needing a separate skills installation.

Add a `CLAUDE.md` to the project root that points outer Claude at `agent-bridge/` — this bootstraps its awareness of the bridge, the common context, and the communication protocol. See `nvwb-project/references/agent-bridge.md` for a template.

Optional: copy the sandbox hook scripts into `agent-bridge/hooks/` and wire them up in `.claude/settings.json` to enforce agent constraints (command allowlists, sensitive variable scrubbing, bridge file ownership). See the **Sandboxing with Hooks** section in `nvwb-project/references/agent-bridge.md`.

See `nvwb-project/references/agent-bridge.md` for the full format guide, templates, rules, and Claude vs Cursor differences.

### How it works

**Inner Claude** (running in the container via JupyterLab terminal) writes requests to `/project/agent-bridge/inner.md`.

**Outer Claude** (running on the user's local machine, in their main session) reads the file, takes action (e.g. runs `nvwb compose down && nvwb compose up`), and writes results to `/project/agent-bridge/outer.md`.

Inner Claude reads the response and continues.

Because both sides are Claude, communication can be rich prose — not just command names but context, logs, questions, and diagnostic output.

### Example: requesting a compose restart

Inner Claude writes to `/project/agent-bridge/inner.md`:
```
I've updated /project/code/server.py to add a /status endpoint.
Please run `nvwb compose down && nvwb compose up` and paste me the
compose logs and the output of `curl http://api:8080/status`.
```

Outer Claude runs the commands, then writes to `/project/agent-bridge/outer.md`:
```
Done. Compose restarted cleanly. curl returned: {"status":"ok","uptime":3}
Compose logs showed no errors on startup.
```

---

## What Inner Claude Can and Cannot Do

| Capability | Inner Claude | Outer Claude |
|---|---|---|
| Edit files in `/project/` | ✓ | ✓ |
| Run code and tests | ✓ | — |
| `curl` compose services by name | ✓ | — |
| Read `/nvwb-shared-volume/` | ✓ | — |
| Run `nvwb` commands | ✗ | ✓ |
| Restart compose services | ✗ | ✓ |
| Trigger `nvwb build` | ✗ | ✓ |
| Start/stop apps | ✗ | ✓ |

For anything requiring `nvwb`, inner Claude writes a request to the bridge and outer Claude handles it.

---

## Notes

- The `nvwb-wrapper.sh` shell function is not available inside the container — `nvwb` commands must run on the local machine
- Compose services are reachable from the project container by service name (e.g. `http://api:8080/`) via the shared `workbench` network
- Add `agent-bridge/` to `.gitignore` — bridge messages should not be committed
- For remote contexts, outer Claude can access bridge files via SSH — the context name (from `nvwb list contexts`) is also the SSH alias. Workbench adds a matching entry to `~/.ssh/config`, so `ssh <context-name>` works directly
