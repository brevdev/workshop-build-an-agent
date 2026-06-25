#!/usr/bin/env bash
# setup.sh — idempotent LOCAL bootstrap for the Build-an-Agent workshop.
#
# Bare NVIDIA GPU machine -> running DevX-Lab:
#   docker up -> install Workbench (if needed) -> activate local ->
#   clone (if needed) -> write secrets.env -> generate CDI spec +
#   configure GPU/host mounts -> build container -> start DevX-Lab -> URL.
#
# Safe to re-run. FIRST RUN CAN TAKE 20-45 MIN (CUDA 12.8 download + CUDA
# torch reinstall + mamba-ssm/causal-conv1d source builds). RUN IN BACKGROUND.
#
# Progress + result stream to $LOG_FILE. The caller waits for ONE sentinel:
#   "=== WORKSHOP SETUP COMPLETE ==="
#   "=== WORKSHOP SETUP FAILED: <reason> ==="
#
# Optional env overrides:
#   NVIDIA_API_KEY   used to write secrets.env after clone if it is absent
#   TAVILY_API_KEY   (optional) Module 1 web-research tool
#   LANGSMITH_API_KEY(optional) Module 3 tracing
#   GIT_REPO TARGET_BRANCH TARGET_APPLICATION LOG_FILE
set -o pipefail   # NOT -e/-u: we orchestrate the third-party nvwb function and decide on every failure ourselves

GIT_REPO="${GIT_REPO:-https://github.com/brevdev/workshop-build-an-agent}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"
TARGET_APPLICATION="${TARGET_APPLICATION:-DevX-Lab}"
LOG_FILE="${LOG_FILE:-$HOME/.workshop-setup.log}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec > >(tee -a "$LOG_FILE") 2>&1
say(){ echo "[$(date '+%F %T')] $*"; }
die(){ echo "=== WORKSHOP SETUP FAILED: $* ==="; exit 1; }

say "Starting setup (repo=$GIT_REPO branch=$TARGET_BRANCH app=$TARGET_APPLICATION)"

# 1) Docker up (best effort; needed for the container runtime)
if command -v docker >/dev/null 2>&1 && ! docker info >/dev/null 2>&1; then
  say "Starting docker..."; sudo systemctl start docker 2>/dev/null || say "WARNING: could not start docker (may already run rootless)"
fi

# 2) Install NVIDIA AI Workbench if missing
if [ ! -x "$HOME/.nvwb/bin/nvwb-cli" ]; then
  say "Installing NVIDIA AI Workbench (downloads CLI, installs docker + drivers; needs sudo)..."
  mkdir -p "$HOME/.nvwb/bin"
  latest="$(curl -fsSL https://workbench.download.nvidia.com/stable/workbench-cli/LATEST)" || die "cannot reach Workbench download server"
  curl -fsSL "https://workbench.download.nvidia.com/stable/workbench-cli/${latest}/nvwb-cli-$(uname)-$(uname -m)" \
    -o "$HOME/.nvwb/bin/nvwb-cli" || die "Workbench CLI download failed"
  chmod +x "$HOME/.nvwb/bin/nvwb-cli"
  sudo "$HOME/.nvwb/bin/nvwb-cli" install --noninteractive --accept --docker --drivers \
    --uid "$(id -u)" --gid "$(id -g)" || die "Workbench install failed (check sudo / drivers / docker)"
else
  say "NVIDIA AI Workbench already installed."
fi

# 3) Load the nvwb shell FUNCTION (it is not a binary; activate/open use eval).
#    ~/.bashrc often early-returns for non-interactive shells, so source the
#    wrapper file directly as well.
source "$HOME/.bashrc" >/dev/null 2>&1 || true
[ -f "$HOME/.local/share/nvwb/nvwb-wrapper.sh" ] && source "$HOME/.local/share/nvwb/nvwb-wrapper.sh" >/dev/null 2>&1 || true
type nvwb >/dev/null 2>&1 || die "nvwb function unavailable (expected ~/.local/share/nvwb/nvwb-wrapper.sh)"

# 4) Activate the local context (starts the Workbench service + container runtime)
say "Activating local context..."
nvwb activate local || die "nvwb activate local failed"

# 5) Clone if absent; resolve PROJECT_PATH / PROJECT_NAME (tolerant match)
# Null-safe match: some local projects have RemoteUrl=null; coerce to "" so
# jq's test()/sub() never throw (a thrown jq error would dirty the pipeline).
SEL='.result[] | (.RemoteUrl // "") as $u | select($u==$r or ($u|sub("\\.git$";""))==$r or ($u|test("workshop-build-an-agent")))'
rp(){ nvwb list projects -o json 2>/dev/null | jq -r --arg r "$GIT_REPO" "$SEL | .Path" | head -1; }
rn(){ nvwb list projects -o json 2>/dev/null | jq -r --arg r "$GIT_REPO" "$SEL | .Name" | head -1; }
PROJECT_PATH="$(rp)"
if [ -z "$PROJECT_PATH" ]; then
  say "Cloning $GIT_REPO ..."
  nvwb clone project "$GIT_REPO" --context local || die "nvwb clone failed"
  PROJECT_PATH="$(rp)"
fi
[ -n "$PROJECT_PATH" ] || die "could not resolve project path after clone"
PROJECT_NAME="$(rn)"
say "Project: name=$PROJECT_NAME path=$PROJECT_PATH"

# 6) Ensure secrets.env (gitignored, so never present in a fresh clone).
#    NVIDIA_API_KEY is mandatory; the build succeeds without it but every
#    model call 401s. NGC keys are derived from it by preBuild.bash.
SECRETS="$PROJECT_PATH/secrets.env"
if [ ! -f "$SECRETS" ]; then
  if [ -n "${NVIDIA_API_KEY:-}" ]; then
    say "Writing $SECRETS from provided NVIDIA_API_KEY..."
    ( umask 077; {
        echo "NVIDIA_API_KEY=${NVIDIA_API_KEY}"
        echo "NGC_API_KEY=${NVIDIA_API_KEY}"
        echo "NGC_CLI_API_KEY=${NVIDIA_API_KEY}"
        echo "NVIDIA_NIM_API_KEY=${NVIDIA_API_KEY}"
        [ -n "${TAVILY_API_KEY:-}" ]    && echo "TAVILY_API_KEY=${TAVILY_API_KEY}"
        [ -n "${LANGSMITH_API_KEY:-}" ] && echo "LANGSMITH_API_KEY=${LANGSMITH_API_KEY}"
      } > "$SECRETS" )
    chmod 600 "$SECRETS"
  else
    die "missing $SECRETS and no NVIDIA_API_KEY env var. Create it from assets/secrets.env.template (build.nvidia.com key), then re-run."
  fi
else
  grep -q '^NVIDIA_API_KEY=nvapi-' "$SECRETS" \
    || say "WARNING: $SECRETS exists but NVIDIA_API_KEY looks unset/placeholder — model calls will 401 until fixed."
fi

# 7) GPU CDI spec + host mounts. These host paths are declared in spec.yaml,
#    so their SOURCES must exist before nvwb validates mounts at build/start.
say "Preparing GPU CDI spec and host mounts..."
sudo mkdir -p /run/cdi
sudo nvidia-ctk cdi generate --output=/run/cdi/nvidia.yaml 2>/dev/null \
  || say "WARNING: nvidia-ctk cdi generate failed — M6 GPU attach may not work"
nvwb configure mounts /var/run/:/var/host-run/ --project "$PROJECT_PATH" --context local \
  || say "WARNING: could not configure /var/host-run mount"
nvwb configure mounts /run/cdi/:/run/cdi/   --project "$PROJECT_PATH" --context local \
  || say "WARNING: could not configure /run/cdi mount"

# 8) Build (the long pole)
say "Building container — CUDA 12.8 + torch + mamba/causal-conv1d source build. 20-45 min. Be patient."
if nvwb build --context local --project "$PROJECT_PATH"; then
  say "Build succeeded."
else
  die "nvwb build failed — inspect project-runtime-info/<hash>/build-output.failure under the workbenchDir in ~/.nvwb/contexts.json (see references/troubleshooting.md)."
fi

# 9) Start DevX-Lab + resolve the browser URL (delegated to start-app.sh)
say "Starting $TARGET_APPLICATION ..."
TARGET_APPLICATION="$TARGET_APPLICATION" PROJECT_PATH="$PROJECT_PATH" PROJECT_NAME="$PROJECT_NAME" \
  bash "$SCRIPT_DIR/start-app.sh" || die "could not start $TARGET_APPLICATION"

say "DevX-Lab URL: $(cat "$HOME/.workshop-app-url" 2>/dev/null || echo '<unresolved>')"
echo "=== WORKSHOP SETUP COMPLETE ==="
