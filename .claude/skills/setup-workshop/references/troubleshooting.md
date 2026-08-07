# Troubleshooting — local Build-an-Agent setup

Work top-down: most failures are one of (1) `nvwb` not sourced, (2) missing
`secrets.env`, (3) a build download/compile error, or (4) a missing host mount
source. Each section gives the symptom, the cause, and the fix.

## `nvwb: command not found` / `timeout: failed to run command 'nvwb'`
`nvwb` is a **shell function**, not a binary — the installer sources
`~/.local/share/nvwb/nvwb-wrapper.sh` from `~/.bashrc`. Non-login/non-interactive
shells (scripts, `bash -c`, systemd) don't load it.
- Fix: `source ~/.local/share/nvwb/nvwb-wrapper.sh` (the scripts here already do).
- Never wrap it in `timeout` / `env` / `xargs` — those exec a binary and the
  function is invisible to them. `activate`, `open`, and `close` also use `eval`
  to mutate the current shell, so they must not run inside `$(...)` or a pipe.

## Every model call returns 401 / "invalid API key" (build was fine)
`secrets.env` is **gitignored** — a fresh clone never has it.
- Fix: create `<project>/secrets.env` from `assets/secrets.env.template` with a
  real `NVIDIA_API_KEY` (https://build.nvidia.com). `chmod 600` it.
- Env-var changes are **runtime**, not build-time. After editing `secrets.env`
  restart the container so notebooks re-source it: `nvwb close` then `nvwb open`
  (or restart the app). A rebuild is not required.
- Verify inside the container: `nvwb attach` then `echo "${NVIDIA_API_KEY:0:8}"`.

## `nvwb build` failed
Read the tail of setup's log first: `tail -n 60 ~/.workshop-setup.log`. For the
full Containerfile execution log, find the workbench dir then the build output:
```bash
jq -r '.[] | select(.name=="local").workbenchDir' ~/.nvwb/contexts.json   # usually ~/.nvwb
ls   ~/.nvwb/project-runtime-info/*/build-output.failure
tail -n 120 ~/.nvwb/project-runtime-info/*/build-output.failure
```
Common causes:
- **Network drop during the CUDA 12.8 or torch download** (postBuild pulls
  multi-GB installers from `developer.download.nvidia.com` and
  `download.pytorch.org`). Re-run setup — the build resumes/retries. For a clean
  slate: `nvwb build --full-build`.
- **`npm`/`n` install error.** Already pinned to `n@10.2.0` in `postBuild.bash`
  (a security-hold on newer `n` previously broke fresh builds). If it resurfaces,
  confirm the pin is intact.
- **`clang++: No such file or directory`** while building `causal-conv1d`/
  `mamba-ssm`. postBuild exports `CC=gcc CXX=g++` to avoid this — ensure `g++` is
  in `apt.txt` and the export survived any local edits.
- **Slow first build is normal**, especially on aarch64 where torch is force-
  reinstalled from the cu128 index and the SM 12.1 (GB10) kernels compile from
  source. 20-45 min is expected; it is not hung if the log is still advancing.

## `mount source ... does not exist` at build/start
The `/run/cdi/` and `/var/host-run/` host mounts are declared in `spec.yaml`;
their **sources** must exist on the host first.
```bash
sudo mkdir -p /run/cdi
sudo nvidia-ctk cdi generate --output=/run/cdi/nvidia.yaml   # needs nvidia-ctk
```
`/var/run/` always exists. setup.sh runs these before build; if you build
manually, run them first. If `nvidia-ctk` is missing, install the NVIDIA
Container Toolkit (it ships with `nvwb install --drivers`); M6's GPU attach
needs the populated `/run/cdi/nvidia.yaml`.

## No GPU / `nvwb start` refuses to launch
The project requests 1 GPU. Without one:
```bash
nvwb start DevX-Lab --no-gpus --context local --project <path>
```
M1-M3 call hosted NIM endpoints and run fine GPU-less. M4 (RL/GRPO with unsloth)
and M6 (NemoClaw local inference) require a physical NVIDIA GPU.

## Docker permission denied / daemon not running
```bash
sudo systemctl start docker
docker info >/dev/null && echo ok
```
If the container can't reach the host docker socket (M5 sandboxing), it joins the
socket's group via `/etc/profile.d/join-docker-group.sh` (set up in preBuild) —
open a fresh shell inside the container (`nvwb attach`) so the group membership
takes effect.

## Background setup hangs early (no progress in the log)
Usually a `sudo` password prompt that a backgrounded process can't answer
(first-time install or the CDI step). Cache credentials first: run `sudo -v` in
the foreground, then relaunch setup. Or configure passwordless sudo for the user.

## App URL is blank / 404 / connection refused
- Confirm it's running: `nvwb status` and `nvwb list apps`.
- Confirm the proxy port: `jq '.[]|select(.name=="local").proxyPort' ~/.nvwb/contexts.json` (default 10000).
- Use the full app path `http://localhost:<proxyPort>/projects/<name>/applications/DevX-Lab/`.
- Headless box: the proxy listens on localhost only — port-forward it (see `access.md`).
- Re-resolve the URL any time with `scripts/start-app.sh`.

## `apt` is locked (fresh box, cloud-init still running)
A background `apt`/`unattended-upgrades` holds the lock. Wait for it:
```bash
while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do sleep 10; done
```

## Start over cleanly
```bash
source ~/.local/share/nvwb/nvwb-wrapper.sh
nvwb stop DevX-Lab --context local --project <path>   # stop app (+ container)
nvwb build --full-build --context local --project <path>   # clean rebuild
# Full reset (drops the project; you re-clone): nvwb delete project <path>
```
