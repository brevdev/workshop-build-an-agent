# AI Workbench Configuration Files Reference

## `.project/spec.yaml`

- **Location:** `.project/spec.yaml` (relative to project root)
- **Format:** YAML (specVersion v2)
- **Effect of changes:** Depends on section — layout/package changes need rebuild; app/mount changes need restart
- **Validation:** Run `nvwb validate project-spec` on the host after manual edits
- **Pitfall:** Do not manually edit `environment.base.package_managers.installed_packages` — use `nvwb add package` from the host. This list is informational and may not accurately reflect what is actually installed; run `pip freeze` or `dpkg -l` in the container for ground truth

Key sections:
- `meta` — Project name, description, labels
- `layout` — Directory structure and Git storage strategies
- `environment.base` — Base container image, package managers, built-in apps
- `environment.compose_file_path` — Path to compose file (empty if none)
- `execution.apps` — Custom application definitions
- `execution.resources` — GPU count, shared memory
- `execution.secrets` — Secret variable declarations
- `execution.mounts` — Mount definitions (project, host, volume, tmp)

## `apt.txt`

- **Location:** Project root
- **Format:** One apt package name per line, `#` for comments
- **Effect:** Triggers container rebuild (`nvwb build`)
- **Example:**
```
poppler-utils
python3-pil
tesseract-ocr
libtesseract-dev
```

## `requirements.txt`

- **Location:** Project root
- **Format:** Standard pip requirements format (supports version pinning, extras)
- **Effect:** Triggers container rebuild (`nvwb build`)
- **Constraints:**
  - `--index-url` and `--extra-index-url` are **not supported** — if a package requires a custom index (e.g. PyTorch with a specific CUDA wheel), install it in `preBuild.bash` instead so it is available before requirements.txt is processed
  - Comments must be on their own line — inline comments (e.g. `torch  # for GPU`) will break the install
- **Example:**
```
jupyterlab>3.0
langchain==0.3.15
fastapi==0.111.0
gradio
torch>=2.0
```

## `preBuild.bash`

- **Location:** Project root
- **Format:** Bash script (must be executable)
- **Effect:** Triggers container rebuild (`nvwb build`)
- **Runs:** Before system and pip packages are installed
- **CANNOT reference `/project/`** — project directory is not mounted during build
- **Example:**
```bash
#!/bin/bash
# Runs before package install
pip install --upgrade pip
```

## `postBuild.bash`

- **Location:** Project root
- **Format:** Bash script (must be executable)
- **Effect:** Triggers container rebuild (`nvwb build`)
- **Runs:** After system and pip packages are installed
- **CANNOT reference `/project/`** — project directory is not mounted during build
- **Available variables:** `$NVWB_UID`, `$NVWB_GID` for file ownership
- **Example:**
```bash
#!/bin/bash
# Runs after package install
# Can use sudo for extra system installs
sudo apt-get update && sudo apt-get install -y some-package
# Fix ownership for directories created during build
chown -R $NVWB_UID:$NVWB_GID /some/path
```

## `variables.env`

- **Location:** Project root
- **Format:** `KEY=VALUE` (one per line), `#` for comments
- **Effect:** Requires container restart (`nvwb close` + `nvwb open`)
- **NOT available during build** — only sourced at runtime inside the container
- **Example:**
```
# Runtime environment variables
TENSORBOARD_LOGS_DIRECTORY=/data/tensorboard/logs/
MAX_CONCURRENT_REQUESTS=1
API_SERVICE_URL=http://pdf-to-podcast-api-service-1:8002
AI_WORKBENCH_FLAG=true
```

## `compose.yaml` / `docker-compose.yaml`

- **Location:** Project root or custom path set in `spec.yaml` `environment.compose_file_path`
- **Format:** Standard Docker Compose format
- **Effect:** Managed with `nvwb compose up/down/status/logs` on the host
- **Key patterns:**
  - `/nvwb-shared-volume/` is automatically created and shared between all containers
  - Services communicate over a shared Docker network using service names as hostnames
  - Use `profiles: [local]` for optional services (started with `nvwb compose up --profile local`)
  - The project container can reach compose services by their service names

## `README.md`

- **Location:** Project root
- **Special behavior:** The `## Get Started` section is rendered in the Workbench UI when a user opens the project — keep it as a short bulleted quick-start guide (e.g. "Start JupyterLab → open this notebook → run all cells"). Removing the section entirely removes the widget from the UI.

## `.gitattributes`

- **Location:** Project root
- **Format:** Standard Git attributes format
- **Purpose:** Defines Git LFS tracking rules for layout directories with `storage: gitlfs`
- **Auto-generated** by Workbench based on `layout` in `spec.yaml`

## `.gitignore`

- **Location:** Project root
- **Format:** Standard gitignore format
- **Purpose:** Ignore patterns for layout directories with `storage: gitignore` and other untracked files
- **Auto-generated** by Workbench based on `layout` in `spec.yaml`

## Runtime vs Build Privileges

| Context | `sudo` available? |
|---|---|
| Running container (terminal, app) | No — runs as `workbench` user |
| `preBuild.bash` / `postBuild.bash` | Yes — passwordless sudo during build |

If you need system-level changes (installing system packages, writing to `/usr/`, etc.), they must go in the build scripts. You cannot use `sudo` in a running container terminal.

## Summary: What Triggers What

| File | Change Requires | Command (run on host) |
|---|---|---|
| Code in layout dirs | Nothing | — |
| `apt.txt` | Rebuild | `nvwb build` |
| `requirements.txt` | Rebuild | `nvwb build` |
| `preBuild.bash` | Rebuild | `nvwb build` |
| `postBuild.bash` | Rebuild | `nvwb build` |
| `variables.env` | Restart | `nvwb close` + `nvwb open` |
| `spec.yaml` (apps) | Restart | `nvwb close` + `nvwb open` |
| `spec.yaml` (packages) | Rebuild | `nvwb build` |
| `spec.yaml` (mounts) | Restart | `nvwb close` + `nvwb open` |
| `compose.yaml` | Recompose | `nvwb compose down` + `nvwb compose up` |
