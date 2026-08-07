# AI Workbench Project Structure

## Standard Layout

```
project-root/
├── .project/
│   ├── spec.yaml          # Central config: container + runtime definition
│   └── configpacks/       # Additional config (usually empty)
├── .gitattributes         # Git LFS tracking rules
├── .gitignore             # Ignore patterns
├── apt.txt                # System packages (one per line, consumed during build)
├── requirements.txt       # Pip packages (consumed during build)
├── preBuild.bash          # Runs BEFORE package install during build
├── postBuild.bash         # Runs AFTER package install during build
├── variables.env          # Runtime env vars (KEY=VALUE format)
├── compose.yaml           # Optional multi-container services
├── code/                  # Code directory (type: code, storage: git)
├── data/                  # Data directory (type: data, storage: gitlfs)
└── models/                # Models directory (type: models, storage: gitlfs)
```

## File Roles

### Build-Time Files (changes require `nvwb build`)

**`apt.txt`** — System packages
- One apt package per line
- Comments with `#`
- Example:
```
poppler-utils
python3-pil
tesseract-ocr
```

**`requirements.txt`** — Pip packages
- Standard pip requirements format
- Example:
```
langchain==0.3.15
fastapi==0.111.0
gradio
```

**`preBuild.bash`** — Pre-install build script
- Runs before system and pip packages are installed
- CANNOT reference `/project/` — the project directory is not mounted during build
- Use for: upgrading pip, adding apt repos, pre-build setup

**`postBuild.bash`** — Post-install build script
- Runs after system and pip packages are installed
- CANNOT reference `/project/` — the project directory is not mounted during build
- Can use `$NVWB_UID` / `$NVWB_GID` for file ownership
- Can use `sudo` for additional system-level installs

### Runtime Files (changes require container restart)

**`variables.env`** — Environment variables
- `KEY=VALUE` format, one per line
- `#` for comments
- Sourced inside container at start
- NOT available during build — only at runtime
- Example:
```
TENSORBOARD_LOGS_DIRECTORY=/data/tensorboard/logs/
MAX_CONCURRENT_REQUESTS=1
AI_WORKBENCH_FLAG=true
```

### Configuration Files (careful editing)

**`.project/spec.yaml`** — Central project definition
- Defines container image, packages, apps, mounts, secrets, resources
- Use `nvwb validate project-spec` to check format after manual edits
- See `spec-reference.md` for full structure

### Compose Files

**`compose.yaml`** (or `docker-compose.yaml`)
- Standard Docker Compose format
- Can be at project root or custom path set in `spec.yaml`
- `/nvwb-shared-volume/` shared between project container and compose services
- Services communicate over shared Docker network
- Managed with `nvwb compose up/down/status/logs` from host

## Layout Directories

Layout directories are defined in `spec.yaml` under `layout`. The standard layout uses three directories:

| Directory | Type | Storage | Purpose |
|---|---|---|---|
| `code/` | code | git | Source code, tracked normally |
| `data/` | data | gitlfs | Datasets, tracked with Git LFS |
| `models/` | models | gitlfs | Model weights, tracked with Git LFS |

Storage strategies:
- **`git`** — Normal Git tracking
- **`gitlfs`** — Git Large File Storage (for large binaries)
- **`gitignore`** — Not tracked (scratch space, caches)

Layout is fully customizable. Some projects use 7+ directories with names like `docs/`, `services/`, `frontend/`, `tests/`.

## Build vs Runtime Summary

| File | Change Requires |
|---|---|
| Code in layout dirs | Nothing (live-mounted) |
| `apt.txt` | `nvwb build` |
| `requirements.txt` | `nvwb build` |
| `preBuild.bash` | `nvwb build` |
| `postBuild.bash` | `nvwb build` |
| `variables.env` | Container restart (`nvwb close` + `nvwb open`) |
| `.project/spec.yaml` (apps) | Container restart |
| `.project/spec.yaml` (packages) | `nvwb build` |
| `.project/spec.yaml` (mounts) | Container restart |
| `compose.yaml` | `nvwb compose down` + `nvwb compose up` |

## Anti-Patterns to Avoid

- **Using conda venvs inside `postBuild.bash`** — Workbench cannot manage these; prefer pip or base images with conda pre-installed
- **Heavy apt work in `preBuild.bash` bypassing `apt.txt`** — Workbench cannot track packages installed this way
- **Referencing `/project/` in build scripts** — The project directory is not mounted during build; this will fail silently or error
- **One fat container with conda venvs for isolation** — Use compose for separate services instead
- **Inline comments in `requirements.txt`** — Not supported; comments must be on their own lines with `#`
- **`--index-url` in `requirements.txt`** — Not supported by Workbench's package installer; use `preBuild.bash` for custom index configuration
