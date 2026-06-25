# Brev Cloud GPU Instances

Brev is a cloud GPU broker (acquired by NVIDIA in 2024) that provisions GPU instances across multiple cloud providers. The Workbench integration lets you use Brev instances as remote contexts, with lifecycle managed automatically.

Brev is a paid service. Instances are billed while running — deactivating a context stops the instance.

---

## Prerequisites

### 1. Connect the Brev integration

Brev uses OAuth2 — this opens a browser:

```bash
nvwb connect integration brev
# optional if account lookup fails:
nvwb connect integration brev --brev-email you@example.com
```

Verify it connected:

```bash
nvwb list integrations
```

### 2. Create an instance in the Brev console

`nvwb` cannot create cloud instances. Go to **https://brev.nvidia.com** and create one there. The instance must be running before you can register it.

---

## Check Instance Stoppability

Before registering an instance, verify it supports stop/start. Workbench auto-stops instances on deactivate — if an instance can only be terminated (not stopped), it cannot be managed by Workbench.

```bash
nvwb list brev instances
```

Output includes a `STOPPABLE` column:

```
NAME                               STATUS     ID         MACHINE                    STOPPABLE
my-gcp-instance                    🟢 Running  abc123     g2-standard-4:nvidia-l4:1  ✅
my-massed-compute-instance         ⚫ Stopped  def456     massedcompute_L40S         ❌
```

Only register instances marked ✅. Stoppability depends on the underlying cloud provider:

| Provider | Stoppable | Notes |
|---|---|---|
| AWS | ✅ | All instance types |
| GCP | ✅ | All instance types |
| Crusoe | ✅ | All instance types |
| Nebius | ✅ mostly | Most instances; check STOPPABLE column |
| Shadeform | ❌ | Marketplace aggregator (Massed Compute, etc.) — terminate-only |
| Lambda Labs | ❌ | Terminate-only |
| OCI | ❌ | Terminate-only |
| Launchpad | ❌ | Terminate-only |

If you need stoppable instances with high-end GPUs, GCP (A100, H100), Crusoe (A100, L40S), and Nebius (H100, H200, L40S) are good options.

### Managing orgs

`nvwb list brev instances` shows instances in the currently active Brev org. If your instance is in a different org, switch first using the Brev CLI:

```bash
nvwb list brev orgs          # see all orgs
brev set <org-name>          # switch active org
nvwb list brev instances     # now shows instances in that org
```

---

## Path A — Create + Register via CLI (fully scriptable)

Create a new instance with `brev create`, then bootstrap and register it — no browser, no interactive picker.

```bash
# 1. Create the instance (blocks until ready)
brev create <name> -g <gpu-type>

# 2. Refresh SSH config
brev refresh

# 3. Pull connection details from SSH config
grep -A6 "^Host <name>$" ~/.brev/ssh_config
# Fields needed: Hostname (IP), User, IdentityFile

# 4. Bootstrap Workbench on the instance
ssh <name> "mkdir -p \$HOME/.nvwb/bin && \
  curl -L https://workbench.download.nvidia.com/stable/workbench-cli/\$(curl -L -s https://workbench.download.nvidia.com/stable/workbench-cli/LATEST)/nvwb-cli-\$(uname)-\$(uname -m) \
  --output \$HOME/.nvwb/bin/nvwb-cli"
ssh <name> "chmod +x \$HOME/.nvwb/bin/nvwb-cli && \
  sudo -E \$HOME/.nvwb/bin/nvwb-cli install --noninteractive --accept --docker --drivers"

# 5. Register as a Workbench context (use IP from Hostname field, not SSH alias)
nvwb create context <name> <ip> \
  --ssh-username <user> \
  --ssh-key-path ~/.brev/brev.pem \
  --context-workbench-dir /home/<user>/.nvwb \
  --accept-ssh-fingerprints \
  --description "Brev <name> (<gpu-type>)"

# 6. Activate
nvwb activate <name>
```

**Notes:**
- `brev create` output gives the instance name but not the hostname or username — always run `brev refresh` and read `~/.brev/ssh_config` for those values
- Use the `Hostname` field (IP address) from `~/.brev/ssh_config` for `nvwb create context` — the SSH alias name does not work as a hostname for nvwb
- For GCP instances the username is `ubuntu`; always verify from the `User` field in SSH config
- `--context-workbench-dir` is `/home/<user>/.nvwb`

---

## Path B — Interactive Registration (automatic bootstrap)

`nvwb create context --brev` handles SSH setup and Workbench installation on the instance automatically, but **requires an interactive terminal** (TUI arrow-key picker — cannot be scripted). Only use this path when you already have a running Brev instance and want Workbench to auto-bootstrap it.

```bash
nvwb create context <context_name> --brev --accept-ssh-fingerprints
# interactive picker appears — select the running instance
nvwb activate <context_name>
```

Workbench bootstraps itself on the instance during `activate`. After that, use it like any other context.

---

## Path C — Register Existing Instance Manually (non-interactive, scriptable)

When you have an existing Brev instance and need non-interactive registration, bootstrap Workbench on the instance via SSH then register as a standard SSH context.

The Brev CLI maintains SSH config at `~/.brev/ssh_config` (included from `~/.ssh/config`). Instance names are the SSH aliases:

```bash
# Refresh SSH config after creating or starting an instance
brev refresh

# The alias is just the instance name — check the config if needed
cat ~/.brev/ssh_config
```

### Step 1 — Download nvwb-cli on the instance

```bash
ssh <instance-name> "mkdir -p \$HOME/.nvwb/bin && \
  curl -L https://workbench.download.nvidia.com/stable/workbench-cli/\$(curl -L -s https://workbench.download.nvidia.com/stable/workbench-cli/LATEST)/nvwb-cli-\$(uname)-\$(uname -m) \
  --output \$HOME/.nvwb/bin/nvwb-cli"
```

### Step 2 — Install Workbench on the instance

```bash
ssh <instance-name> "chmod +x \$HOME/.nvwb/bin/nvwb-cli && \
  sudo -E \$HOME/.nvwb/bin/nvwb-cli install \
  --noninteractive \
  --accept \
  --docker \
  --drivers"
```

### Step 3 — Register as a standard SSH context

`--context-workbench-dir` is required for non-interactive registration:

```bash
nvwb create context <context_name> <hostname> \
  --ssh-username <user> \
  --ssh-key-path ~/.brev/brev.pem \
  --context-workbench-dir /home/<user>/.nvwb \
  --accept-ssh-fingerprints \
  --description "Brev <instance-name>"
```

The hostname, username, and key are all in `~/.brev/ssh_config`. For GCP-backed instances the user is typically `ubuntu`; other providers vary (e.g. `shadeform` for Massed Compute).

### Step 4 — Activate

```bash
nvwb activate <context_name>
```

> **Note:** Contexts registered via Path B show `contextType: manual` in `~/.nvwb/contexts.json`. This is expected — they function identically to any other SSH context.

---

## Using the Context

Once activated, a Brev context works identically to any other remote context:

```bash
nvwb clone project https://github.com/me/my-project
nvwb open my-project
nvwb build
nvwb start jupyterlab
```

---

## Cost Management

```bash
# Stop work — deactivates context and stops the instance
nvwb deactivate

# Resume — activates context and restarts the instance
nvwb activate <context_name>
```

> Always verify instance status in the Brev console at **https://brev.nvidia.com** after closing Workbench — confirm the instance stopped to avoid unexpected charges.

---

## Brev CLI Reference

The Brev CLI (`~/.local/bin/brev`) is installed alongside Workbench and manages Brev-specific operations that `nvwb` doesn't expose:

| Command | Description |
|---|---|
| `brev ls` | List instances in active org |
| `brev ls --all --org <name>` | List all instances in a specific org |
| `brev ls orgs` | List all orgs |
| `brev set <org-name>` | Switch active org |
| `brev refresh` | Refresh SSH config after instance state changes |
| `brev start <instance>` | Start a stopped instance |
| `brev stop <instance>` | Stop a running instance |
| `brev create` | Create a new instance (GPU: `-g`, CPU: `-c`) |
| `brev delete <instance>` | Delete an instance |

The Brev SSH config lives at `~/.brev/ssh_config` and is included from `~/.ssh/config` automatically. Instance names are the SSH host aliases.
