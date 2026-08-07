# spec.yaml Reference

The `.project/spec.yaml` file is the central configuration for an AI Workbench project. It defines the container image, packages, applications, mounts, secrets, and resources.

## Complete Structure

```yaml
specVersion: v2
specMinorVersion: 2

meta:
    name: "project-name"
    image: "project-image-name"
    description: "Project description"
    labels: ["ml", "pytorch"]
    createdOn: "2025-01-01T00:00:00Z"
    defaultBranch: "main"

layout:
    - path: code/
      type: code
      storage: git
    - path: data/
      type: data
      storage: gitlfs
    - path: data/scratch/
      type: data
      storage: gitignore
    - path: models/
      type: models
      storage: gitlfs

environment:
    base:
        registry: nvcr.io
        image: nvidia/ai-workbench/python-basic:1.0.8
        build_timestamp: "20250101120000"
        name: "PyTorch"
        supported_architectures: []
        cuda_version: "12.0"
        description: "Environment description"
        entrypoint_script: ""
        labels: ["cuda12.0"]
        os: "linux"
        os_distro: "ubuntu"
        os_distro_release: "22.04"
        schema_version: v2
        user_info:
            uid: ""
            gid: ""
            username: ""
        icon_url: ""
        image_version: ""
        programming_languages:
            - python3
        package_managers:
            - name: apt
              binary_path: /usr/bin/apt
              installed_packages: [""]
            - name: pip
              binary_path: /usr/bin/pip
              installed_packages: ["jupyterlab"]
        package_manager_environment:
            name: ""
            target: ""
        apps:
            - name: jupyterlab
              type: jupyterlab
              class: webapp
              start_command: "jupyter lab --allow-root --port 8888 ..."
              health_check_command: "..."
              stop_command: "jupyter lab stop 8888"
              user_msg: ""
              logfile_path: ""
              timeout_seconds: 60
              icon_url: ""
              webapp_options:
                autolaunch: true
                port: "8888"
                proxy:
                    trim_prefix: false
                url_command: "jupyter lab list ..."
    compose_file_path: ""

execution:
    apps:
        - name: my-custom-app
          type: custom
          class: webapp
          start_command: "python serve.py"
          health_check_command: "curl -s http://localhost:8080"
          stop_command: "pkill -f serve.py"
          user_msg: ""
          logfile_path: ""
          timeout_seconds: 0
          icon_url: ""
          webapp_options:
            autolaunch: true
            port: "8080"
            proxy:
                trim_prefix: true
            url: ""
            url_command: ""
    resources:
        gpu:
            requested: 1
        sharedMemoryMB: 1024
    secrets:
        - variable: NVIDIA_API_KEY
          description: "NVIDIA API key for cloud endpoints"
        - variable: HF_TOKEN
          description: "Hugging Face API token"
    mounts:
        - type: project
          target: /project/
          description: "Project directory"
          options: rw
        - type: host
          target: /data/
          description: "Host data directory"
          options: ro
        - type: volume
          target: /data/tensorboard/logs/
          description: "Tensorboard Log Files"
          options: volumeName=tensorboard-logs-volume
```

## Section Details

### `meta`

Project metadata. The `name` and `image` fields are used to identify the project and its container image. Labels are used for categorization.

### `layout`

Defines the project directory structure. Each entry specifies:
- **`path`** — Directory path relative to project root
- **`type`** — Category: `code`, `data`, or `models`
- **`storage`** — Git strategy: `git` (tracked normally), `gitlfs` (large file storage), `gitignore` (not tracked)

Layout is fully customizable — you can have as many directories as needed with any names. Some projects use the standard 3-dir layout (code/, data/, models/), others define 7+ custom directories.

### `environment`

#### `environment.base`

Defines the base container image and its properties:
- **`registry`** / **`image`** — Container registry and image reference
- **`cuda_version`** — CUDA toolkit version
- **`os_distro`** / **`os_distro_release`** — Base OS (typically Ubuntu 22.04)
- **`user_info`** — Custom uid/gid/username for the container user
- **`package_managers`** — Declared package managers (apt, pip, optionally conda3)
- **`apps`** — Base applications (e.g., JupyterLab) included in the base image

Common base images:
- `nvidia/ai-workbench/python-basic` — Lightweight Python environment
- `rapidsai/notebooks` — RAPIDS + CUDA data science stack

#### `environment.compose_file_path`

Path to a Docker Compose file if using multi-container services. Empty string means no compose. Can point to a subdirectory (e.g., `workbench/docker-compose.yaml`).

### `execution`

Runtime configuration that lives with the project.

#### `execution.apps`

Custom applications defined by the project. Each app has:
- **`name`** — Unique identifier
- **`type`** — `custom`, `jupyterlab`, `vs-code`, or `cursor`
- **`class`** — `webapp` (HTTP service), `process` (background), or `native` (IDE/desktop, managed by Workbench)
- **`start_command`** / **`stop_command`** — Shell commands to manage the app
- **`health_check_command`** — Command to verify the app is running
- **`timeout_seconds`** — Max wait time for health check (0 = no timeout)
- **`webapp_options`** — For webapp class: port, proxy settings, auto-launch, URL discovery
  - `url` and `url_command` are mutually exclusive; both require a trailing slash
  - `PROXY_PREFIX` env var is injected at runtime for apps behind the proxy — when using pipes or subshells in `start_command`, pass it explicitly: `PROXY_PREFIX=$PROXY_PREFIX python app.py | tee log`
- **`process_options`** — For process class: `wait_until_finished: true` makes the UI wait for the process to complete (useful for one-off tasks like model downloads)

**Native apps** (`class: native`, `type: cursor` or `type: vs-code`) are managed entirely by Workbench for IDE connectivity — do not add or modify these manually.

**Compose proxy routing**: for compose services exposed through the proxy, set `NVWB_TRIM_PREFIX=true` as an environment variable in the compose service (rather than in `webapp_options`).

Execution apps can override base apps with the same name.

#### `execution.resources`

Hardware requirements:
- **`gpu.requested`** — Number of GPUs (0 for CPU-only)
- **`sharedMemoryMB`** — Shared memory allocation

> **GPU reservation modes**: The default mode is `exclusive` — each project gets dedicated GPUs. On DGX Spark / GB10 hardware, Workbench defaults to `shared` mode (all containers share the single large-memory GPU). In `shared` mode `gpu.requested` is ignored and all GPUs are passed to all containers. Prefer CUDA 13+ on GB10 for best performance.

#### `execution.secrets`

Secret variable declarations committed to git (name + description only, no values):
- **`variable`** — Environment variable name
- **`description`** — Human-readable description

Set values with: `nvwb create environment-variable VAR value --is-sensitive`

#### `execution.mounts`

Mount definitions:
- **`type`** — `project` (the project dir), `host` (host filesystem), `volume` (Docker volume), `tmp` (temporary)
- **`target`** — Mount path inside container
- **`options`** — Mount options (`rw`, `ro`, `volumeName=...`)

Configure host mount sources with: `nvwb configure mounts /host/path:/container/path`

## Key Patterns

- **App override:** Define an app in both `environment.base.apps` and `execution.apps` to override the base version
- **Compose profiles:** Use `profiles: [local]` in compose for optional services, start with `nvwb compose up --profile local`
- **Conda support:** Declare in spec under `package_managers` but install via base image or postBuild.bash — no first-class build mechanism like pip/apt
- **Validation:** Run `nvwb validate project-spec` to check spec.yaml format
- **Do not manually edit** `package_managers.installed_packages` — use `nvwb add package` from the host. Note this list is informational and may not reflect actual installed packages; run `pip freeze` or `dpkg -l` in the container for ground truth
- **README `## Get Started` section** — the content of this section is rendered in the Workbench UI when a user opens the project. Keep it as a short bulleted quick-start guide. Removing the section entirely removes the widget from the UI.
