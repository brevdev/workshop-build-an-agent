---
name: nvwb
description: Manage NVIDIA AI Workbench projects, contexts, builds, and environments via the nvwb CLI. This skill should be used when the user wants to create, clone, build, manage, or configure AI Workbench projects, contexts, or environments.
disable-model-invocation: false
user-invocable: true
---

# NVIDIA AI Workbench — Local Machine (Control Plane)

NVIDIA AI Workbench is a lightweight, containerized development platform for GPU-accelerated AI/ML workflows. Every project is a Git repo with a `.project/spec.yaml` that defines the container environment. It supports Docker and Podman as container runtimes.

The `nvwb` CLI always runs on the **local machine** — the user's laptop or desktop. From there it manages contexts, which may be local (container on the same machine) or remote (container on a server or cloud instance accessed via SSH). Codex using this skill is on the local machine.

The user wants help with: $ARGUMENTS

## Core Concepts

- **Contexts** — Locations/machines where projects run (local, remote SSH, Brev cloud)
- **Projects** — Git repos with container configuration (`.project/spec.yaml`)
- **Applications** — Services inside the container (JupyterLab, VS Code, custom webapps/processes)
- **Environment Variables** — Runtime values set via CLI; sensitive ones (`--is-sensitive`) are masked in output. Values are never committed to Git. Projects may declare required secret variable names in `spec.yaml` under `execution.secrets`.

## Current State Detection

Before taking action, check the current state:

```bash
nvwb list contexts        # What locations are configured?
nvwb status               # Is a project open? Is the container running?
nvwb list projects        # What projects exist in the active context?
```

## Build vs Runtime Isolation

**Build-time** (changes require `nvwb build`):
- `apt.txt` — system packages
- `requirements.txt` — pip packages
- `preBuild.bash` / `postBuild.bash` — custom build scripts
- Package manager entries in `spec.yaml`

**Runtime** (changes require container restart: `nvwb close` + `nvwb open`):
- `variables.env` — environment variables
- Mount configuration changes
- App definitions in `spec.yaml`

**No action needed:**
- Code in layout directories (code/, data/, models/) — live-mounted at `/project/`

## Key Environment Variables

| Variable | Available | Description |
|---|---|---|
| `$NVWB_UID` | Build-time | User ID for file ownership in build scripts |
| `$NVWB_GID` | Build-time | Group ID for file ownership in build scripts |
| `$PROXY_PREFIX` | Runtime | URL prefix for proxied web apps |

## Error Handling

When a build fails:
1. Read the build output carefully for the error message
2. Common causes: bad package version in `requirements.txt`, missing apt dependency, bash syntax error in build scripts
3. For deeper logs, check `project-runtime-info/` inside the context's workbench directory — **this is on the machine running the Workbench service, not necessarily the local machine**. Find the right path first:
   ```bash
   cat ~/.nvwb/contexts.json   # workbenchDir field for each context
   ```
   - Local context: `~/.nvwb/project-runtime-info/`
   - Remote context (SSH or Brev): `<workbenchDir>/project-runtime-info/` on the remote — access via `ssh <context-name> "ls <workbenchDir>/project-runtime-info/"`
4. Fix the relevant config file
5. Run `nvwb build` again
6. For persistent issues, try `nvwb build --full-build` for a clean rebuild

## When to Rebuild vs Restart vs Do Nothing

| Change | Action |
|---|---|
| Edit code files | Nothing |
| Edit `apt.txt`, `requirements.txt`, build scripts | `nvwb build` |
| Edit `variables.env` | `nvwb close` then `nvwb open` |
| Change mounts or app config in `spec.yaml` | `nvwb close` then `nvwb open` |
| Change compose services | `nvwb compose down` then `nvwb compose up` |

## References

See the reference files for detailed information:
- `references/cli-reference.md` — Complete CLI command reference
- `references/spec-reference.md` — spec.yaml structure and fields
- `references/project-structure.md` — Project file layout and roles
- `references/workflows.md` — Multi-step workflow recipes
- `references/nvwb-brev.md` — Brev cloud GPU integration: stoppability, interactive vs manual bootstrap, org management, Brev CLI reference
- `references/codex-in-container.md` — Running Codex inside the container, credential persistence, and the host↔container bridge pattern
