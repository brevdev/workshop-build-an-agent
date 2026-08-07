# AI Workbench Workflows

## Create a New Project from Scratch

```bash
nvwb activate local
nvwb create project my-ml-project
nvwb open my-ml-project
nvwb add package pip torch transformers
nvwb build
nvwb start jupyterlab
# ... develop ...
nvwb stop jupyterlab
nvwb commit -m "Add training pipeline"
nvwb publish https://github.com me public
nvwb close
nvwb deactivate --shutdown
```

## Clone and Run an Existing Project

```bash
nvwb activate local
nvwb clone project https://github.com/NVIDIA/workbench-example-agentic-rag
nvwb open workbench-example-agentic-rag
# Set any required sensitive values (container must not be running)
nvwb create environment-variable NVIDIA_API_KEY sk-xxxx --is-sensitive
nvwb create environment-variable TAVILY_API_KEY tvly-xxxx --is-sensitive
nvwb build
# Start the app (check `nvwb list apps` for app names)
nvwb start chat
```

## Add a Remote Context (SSH)

```bash
nvwb create context my-remote-gpu myhost.example.com \
  --ssh-username user \
  --ssh-key-path ~/.ssh/id_ed25519 \
  --ssh-port 22
nvwb activate my-remote-gpu
# Enable external access for remote app access
nvwb activate my-remote-gpu --external-access
nvwb clone project https://github.com/me/my-project.git
nvwb open my-project
nvwb build
nvwb start jupyterlab
```

## Create a Brev Instance and Add as Workbench Location

Full end-to-end: provision a GPU instance on Brev, bootstrap Workbench, and register it as a context.

```bash
# 1. Create instance (blocks until ready — ~2-3 min)
brev create my-gpu-instance -g g2-standard-4:nvidia-l4:1

# 2. Get connection details
brev refresh
grep -A6 "^Host my-gpu-instance$" ~/.brev/ssh_config
# Note: Hostname (IP), User, IdentityFile

# 3. Bootstrap Workbench on the instance
ssh my-gpu-instance "mkdir -p \$HOME/.nvwb/bin && \
  curl -L https://workbench.download.nvidia.com/stable/workbench-cli/\$(curl -L -s https://workbench.download.nvidia.com/stable/workbench-cli/LATEST)/nvwb-cli-\$(uname)-\$(uname -m) \
  --output \$HOME/.nvwb/bin/nvwb-cli"
ssh my-gpu-instance "chmod +x \$HOME/.nvwb/bin/nvwb-cli && \
  sudo -E \$HOME/.nvwb/bin/nvwb-cli install --noninteractive --accept --docker --drivers"

# 4. Register as Workbench context (use IP, not SSH alias)
nvwb create context my-gpu-instance 34.x.x.x \
  --ssh-username ubuntu \
  --ssh-key-path ~/.brev/brev.pem \
  --context-workbench-dir /home/ubuntu/.nvwb \
  --accept-ssh-fingerprints \
  --description "Brev my-gpu-instance (L4)"

# 5. Activate and use
nvwb activate my-gpu-instance
nvwb clone project https://github.com/me/my-project
nvwb open my-project
nvwb build
```

For stoppable GPU options see `nvwb-brev.md`. The Brev integration must be connected first (`nvwb connect integration brev`).

## Use a Brev Cloud Instance

See `references/nvwb-brev.md` for the full guide. Three paths:

**Path A — create + register via CLI** (scriptable, recommended):
Use `brev create` to provision, then bootstrap and register. See full workflow above.

**Path B — interactive** (existing instance, requires a TTY):
```bash
nvwb list brev instances     # check STOPPABLE column — must be ✅
nvwb create context <context_name> --brev   # interactive picker, auto-bootstraps
nvwb activate <context_name>
```

**Path C — register existing instance manually** (scriptable):
```bash
# Bootstrap nvwb on the instance via SSH, then register
nvwb create context <context_name> <ip> \
  --ssh-username <user> \
  --ssh-key-path ~/.brev/brev.pem \
  --context-workbench-dir /home/<user>/.nvwb \
  --accept-ssh-fingerprints
nvwb activate <context_name>
```

## Debug a Failed Build

1. Run `nvwb build` and read the output carefully
2. Look for error messages — common causes:
   - Bad package version in `requirements.txt`
   - Missing system dependency in `apt.txt`
   - Bash syntax error in `preBuild.bash` or `postBuild.bash`
   - Referencing `/project/` in build scripts (not available during build)
3. For more detail, check the build logs in `project-runtime-info/` inside the context's workbench directory. The workbench directory varies per context — look it up first:
   ```bash
   # Find the workbenchDir for any context
   cat ~/.nvwb/contexts.json
   # or
   nvwb list contexts --wide
   ```
   - **Local context:** `~/.nvwb/project-runtime-info/` (workbenchDir is `~/.nvwb` by default)
   - **Remote context (SSH or Brev):** on the remote machine at `<workbenchDir>/project-runtime-info/` — access via SSH:
     ```bash
     ssh <context-name> "ls <workbenchDir>/project-runtime-info/"
     ```

   The `project-runtime-info/<project-hash>/` directory contains:

   | File | Description |
   |---|---|
   | `build-output.success` / `build-output.failure` | Full build log including Containerfile execution output |
   | `Containerfile` | The generated Containerfile used for the last build |
   | `compose-rendered.yaml` | The rendered Docker Compose file (with variable substitution applied) |
   | `compose-up.log` | Output from the last `nvwb compose up` |
   | `<app-name>-start.log` | Log from starting a specific app (e.g. `jupyterlab-start.log`) |
   | `runtime-flags.json` | Runtime configuration flags for the container |
   | `cache/` | Cached build inputs (package lists, script hashes) |
   | `rebuild.cache` / `edit.cache` | Change detection caches used to decide if rebuild is needed |

4. Fix the relevant config file
5. Run `nvwb build` again
6. For persistent issues: `nvwb build --full-build` for a clean rebuild

## Add Packages and Rebuild

```bash
nvwb open my-project
# Add packages
nvwb add package pip numpy pandas scikit-learn
nvwb add package apt libgl1-mesa-glx
# Rebuild to apply
nvwb build
```

## Environment Customization

```bash
nvwb open my-project
# Environment variables (container must not be running)
nvwb create environment-variable MY_VAR my_value
# Sensitive values — value is masked in all output
nvwb create environment-variable API_KEY sk-xxxx --is-sensitive --description "External API key"
# Update a value later
nvwb update environment-variable API_KEY new-value
# Mounts
nvwb create mount HOST /data/ --description "Training data"
nvwb configure mounts /home/user/datasets:/data/
# Rebuild for packages, restart for env/mounts
nvwb build
```

## Set Up Compose Services

```bash
# Compose files: compose.yaml at project root or custom path
# Start all services
nvwb compose up
# Start with optional profile
nvwb compose up --profile local
# Check status
nvwb compose status
# View logs
nvwb compose logs
# Stop
nvwb compose down
```

Key compose patterns:
- `/nvwb-shared-volume/` is shared between project container and compose services
- Service names work as hostnames for inter-container communication
- Use `profiles: [local]` for optional services

## Branching and Publishing

```bash
# Create a feature branch (--carry brings uncommitted changes)
nvwb create branch feature-new-model --carry
# Work and commit
nvwb commit -m "WIP new model architecture"
# Switch back and merge
nvwb switch-branch main
nvwb merge feature-new-model
nvwb push
# Clean up
nvwb delete branch feature-new-model
```

## Manage Environment Variables and Mounts

```bash
# List what's defined
nvwb list environment-variables
nvwb list mounts --wide
# Create sensitive env vars (masked in output)
nvwb create environment-variable NVIDIA_API_KEY sk-xxxx --is-sensitive
nvwb create environment-variable HF_TOKEN hf_xxxx --is-sensitive
# Configure host mount sources
nvwb configure mounts /local/data:/data/ /local/models:/models/
```
