# nvwb CLI Reference

## Global Options

| Option | Description |
|---|---|
| `--context, -c` | Specify context name for command execution |
| `--debug` | Enable debug logging |
| `--help, -h` | Display command help |
| `--output, -o` | Output format: `default`, `json`, or `jsonl` (JSON Lines / streaming) |
| `--project, -p` | Specify absolute project path |
| `--workbench-dir` | AI Workbench directory path (default: `~/.nvwb`) |

## CLI Execution Notes

- **Two modes:** Interactive (prompts for missing info) and Non-interactive (all args specified)
- **Output formats:** Rich text (default), JSON (`-o json`), or JSON Lines (`-o jsonl`)
- **One terminal = one active context and one open project**
- **`nvwb` is a shell function, not a binary.** The installer adds `source $HOME/.local/share/nvwb/nvwb-wrapper.sh` to `~/.bashrc`. The actual binary is `~/.nvwb/bin/nvwb-cli`. The wrapper is required — `activate`, `deactivate`, `open`, and `close` use `eval` to modify shell state; calling the binary directly for those commands will not work correctly. If `nvwb` is not found, run `source ~/.local/share/nvwb/nvwb-wrapper.sh` or start a new shell.
- **SSH auth:** Key-based only (RSA 2048+, ED25519, ECDSA), no password
- **SSH tunneling:** Service tunnel (port 10001), Proxy tunnel (port 10000), consecutive for multiple remotes

## Installation and System

| Command | Description |
|---|---|
| `nvwb install` | Install AI Workbench and dependencies (requires sudo). Options: `--noninteractive`, `--accept/-a`, `--drivers`, `--docker`, `--podman`, `--uid`, `--gid` |
| `nvwb uninstall` | Remove AI Workbench installation |
| `nvwb version` | Display current version information |
| `nvwb support create-bundle` | Generate a diagnostic support bundle |

Remote installation:
```bash
curl -L https://workbench.download.nvidia.com/stable/workbench-cli/$(curl -L -s https://workbench.download.nvidia.com/stable/workbench-cli/LATEST)/nvwb-cli-$(uname)-$(uname -m) \
  --output $HOME/.nvwb/bin/nvwb-cli && \
  chmod +x $HOME/.nvwb/bin/nvwb-cli && \
  sudo -E $HOME/.nvwb/bin/nvwb-cli install
```

## Context (Location) Management

| Command | Description |
|---|---|
| `nvwb list contexts [--wide]` | Display all configured contexts |
| `nvwb create context [name] [hostname]` | Register a new context/location. Options: `--accept-ssh-fingerprints`, `--brev`, `--context-workbench-dir`, `--description/-d`, `--ssh-key-path`, `--ssh-port`, `--ssh-username` |
| `nvwb delete context [name]` | Remove a context configuration |
| `nvwb activate <context_name>` | Activate a context; starts the AI Workbench service and container runtime. Option: `--external-access` |
| `nvwb deactivate` | Deactivate current context. Options: `--force/-f`, `--shutdown` |
| `nvwb update context` | Modify existing context settings |
| `nvwb list brev instances` | List Brev instances in the current org |
| `nvwb list brev orgs` | List Brev organizations the user belongs to |

**Context configuration file:**
- `~/.nvwb/contexts.json` — local file storing all context metadata: `hostname`, `workbenchDir`, `sshKeyPath`, `sshUsername`, `contextType`, proxy/service ports. The `workbenchDir` field is critical for locating `project-runtime-info/` on remote contexts.

**Brev context notes:**
- `nvwb list brev instances` output includes a `STOPPABLE` column (✅/❌) — only instances marked ✅ can be managed by Workbench (lifecycle requires stop/start support)
- `nvwb create context --brev` requires an interactive terminal (TUI picker) — cannot be scripted. For non-interactive use, manually bootstrap Workbench on the instance via SSH then register as a standard SSH context
- `--context-workbench-dir` is required for non-interactive `nvwb create context` (SSH path)
- Manually bootstrapped Brev instances register with `contextType: manual` (not `brev`) — this is expected and normal
- Brev SSH config is at `~/.brev/ssh_config` (included from `~/.ssh/config`) — instance names are the SSH aliases; run `brev refresh` after instance state changes
- Active Brev org affects which instances `nvwb list brev instances` shows — switch with `brev set <org-name>`
- See `references/nvwb-brev.md` for the full guide including manual bootstrap steps

## Project Management

| Command | Description |
|---|---|
| `nvwb list projects [--wide]` | Show projects in current/specified context |
| `nvwb create project [name]` | Initialize a new project. Options: `--base-environment-id`, `--base-url`, `--description`, `--projectPath` |
| `nvwb clone project [remoteURL]` | Clone an existing Git repo. Option: `--projectPath` |
| `nvwb delete project [name_or_path]` | Remove a project |
| `nvwb open [name_or_path]` | Open/activate a project (changes to project directory) |
| `nvwb close` | Close/deactivate current project. Option: `--force/-f` |
| `nvwb status` | Check project and container state |
| `nvwb list bases [--wide]` | Display available base environments |

## Container / Build Management

| Command | Description |
|---|---|
| `nvwb build` | Build the container. Options: `--full-build` (complete rebuild), `--stop` (stop in-progress build) |
| `nvwb attach` | Open a shell in the project container. Option: `--host` |
| `nvwb stop --container` | Stop the running container |

## Package Management

| Command | Description |
|---|---|
| `nvwb list packages [--package-manager/-m apt\|pip]` | Show installed/available packages |
| `nvwb add package [package-manager] [package-reference]` | Install a package |
| `nvwb remove package [package-manager] [package-reference]` | Remove a package |

## Application Management

| Command | Description |
|---|---|
| `nvwb list apps` | Display project applications |
| `nvwb list built-in-apps` | Show available built-in applications |
| `nvwb create app [name] [type]` | Add an application. Types: `custom`, `vs-code`, `jupyterlab`. Classes: `webapp`, `process`, `native` |
| `nvwb delete app [name]` | Remove an application |
| `nvwb start [app_name]` | Launch an application. Options: `--container` (start container only, no app), `--no-browser` (suppress auto-open), `--no-gpus` (launch without GPUs), `--timeout <seconds>` (web app ready wait, default 5) |
| `nvwb stop [app_name]` | Terminate an application. Option: `--container` (stop container even if other apps are running). Note: stopping the last running app automatically stops the container. |
| `nvwb create share-url [app_name]` | Generate a 48-hour shareable URL for a webapp (requires external access mode) |

`nvwb create app` options: `--app-class`, `--health-check-cmd`, `--icon-url`, `--start-cmd`, `--stop-cmd`, `--timeout-seconds`, `--user-msg`, `--webapp-auto-launch`, `--webapp-port`, `--webapp-proxy-trim-prefix`, `--webapp-url`, `--webapp-url-cmd`, `--process-wait-until-finished`

## Mount Management

| Command | Description |
|---|---|
| `nvwb list mounts [--wide]` | Display configured mounts |
| `nvwb create mount [type] [target]` | Create a new mount. Types: `PROJECT`, `HOST`, `VOLUME`, `TMP`. Options: `--description`, `--options` |
| `nvwb configure mounts [source1:target1] [--wide]` | Modify mount configuration |
| `nvwb delete mount [target]` | Remove a mount definition |

**Note:** Mount targets cannot be edited in place. To change a mount's target path, delete it and recreate it.

## Resource Management

| Command | Description |
|---|---|
| `nvwb list resources` | Show hardware requirements/allocation |
| `nvwb update resources` | Modify hardware allocation (GPU count, shared memory) |

## Environment Variables and Secrets

There is no separate secrets subsystem. Sensitive values are environment variables created with `--is-sensitive`, which masks the value in all output. Secret *declarations* (name + description, no value) can appear in `execution.secrets` in `spec.yaml` and are committed to git; values are set via the CLI commands below.

| Command | Description |
|---|---|
| `nvwb list environment-variables` | Display defined env vars |
| `nvwb create environment-variable <variable> <value\|-> ` | Define a new env var. Use `-` to read value from stdin. Options: `--description`, `--is-sensitive` (mask value in output). Note: container must not be running. |
| `nvwb update environment-variable <variable> <value\|->` | Update the value of an existing env var |
| `nvwb delete environment-variable [variable]` | Remove an env var |

## Multi-Container (Docker Compose)

| Command | Description |
|---|---|
| `nvwb compose up [--profile <name>]` | Start compose services |
| `nvwb compose down` | Stop compose services |
| `nvwb compose status` | Check service state |
| `nvwb compose logs` | Retrieve service logs |

Compose files: `compose.yaml`, `compose.yml`, `docker-compose.yml`, or `docker-compose.yaml` in project root or `deploy/`. Customizable via `environment:compose-file-path` in `spec.yaml`. Shared volume at `/nvwb-shared-volume/`.

## Version Control (Git Operations)

| Command | Description |
|---|---|
| `nvwb clone project [remoteURL]` | Clone a remote repo. Option: `--projectPath` |
| `nvwb commit` | Stage and commit. Options: `--message/-m`, `--overrideWarnings` |
| `nvwb discard [file1] [file2]...` | Remove uncommitted changes |
| `nvwb fetch` | Retrieve remote updates |
| `nvwb pull` | Fetch and integrate remote changes |
| `nvwb push` | Upload commits |
| `nvwb publish <remote-url> <namespace> <visibility>` | Push to Git server first time. Visibility: `public`, `private`, `internal` |
| `nvwb merge [branch-name]` | Combine branch changes |
| `nvwb history [--number/-n <count>]` | Display commit log |
| `nvwb list branches` | Show available branches |
| `nvwb create branch [name]` | Create new branch. Option: `--carry` |
| `nvwb delete branch [name]` | Remove branch. Option: `--force` |
| `nvwb switch-branch [branch-name]` | Change active branch |

## Integration Management

| Command | Description |
|---|---|
| `nvwb list integrations [--wide]` | Show available integrations |
| `nvwb create integration` | Define a new integration |
| `nvwb delete integration [name]` | Remove an integration |
| `nvwb connect integration [name] [token]` | Authorize. Option: `--no-browser/-n`, `--brev-email`. Types: NGC, Github, Gitlab, Brev. Brev uses OAuth2 (browser) — token arg not used for Brev. |
| `nvwb disconnect integration [name]` | Revoke access |
| `nvwb update integration` | Modify settings |

## Validation and Scripts

| Command | Description |
|---|---|
| `nvwb validate project-spec` | Validate/lint `spec.yaml` |
| `nvwb edit script` | Open a build script (`preBuild.bash` or `postBuild.bash`) for editing |
| `nvwb edit file` | Open a project file for editing |
| `nvwb update base` | Switch the base environment |
