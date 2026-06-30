#!/usr/bin/env bash
# preflight.sh — read-only environment readiness check for a LOCAL
# Build-an-Agent workshop install. Makes NO changes. Prints PASS/WARN/FAIL
# per check and a verdict. Exit 0 when no blocking (FAIL) issues, else 1.
#
# FAIL  = will block setup; fix before proceeding.
# WARN  = expected on a fresh box, or non-fatal; setup handles most of these.
set -uo pipefail

pass=0; warn=0; fail=0
P(){ printf '  \033[32mPASS\033[0m  %s\n' "$1"; pass=$((pass+1)); }
W(){ printf '  \033[33mWARN\033[0m  %s\n' "$1"; warn=$((warn+1)); }
F(){ printf '  \033[31mFAIL\033[0m  %s\n' "$1"; fail=$((fail+1)); }

echo "== Build-an-Agent workshop — local preflight =="

# --- OS / arch (hard requirements) ---
[ "$(uname -s)" = "Linux" ] && P "OS is Linux" || F "OS is $(uname -s); NVIDIA AI Workbench targets Linux"
arch="$(uname -m)"
case "$arch" in
  x86_64|aarch64|arm64) P "CPU architecture: $arch (supported)";;
  *) F "CPU architecture: $arch (unsupported; need x86_64 or aarch64)";;
esac

# --- GPU (strong WARN: M1-M3 use hosted NIMs; M4 RL + M6 NemoClaw need a local GPU) ---
if command -v nvidia-smi >/dev/null 2>&1; then
  gpu="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)"
  [ -n "$gpu" ] && P "NVIDIA GPU: $gpu" \
    || W "nvidia-smi present but reports no GPU — M4 (RL) and M6 (NemoClaw) will not run"
else
  W "No nvidia-smi / NVIDIA GPU — M1-M3 work via hosted NIMs, but M4/M6 need a local GPU; 'nvwb start' may require --no-gpus"
fi

# --- Disk (CUDA toolkit + torch + container images are large) ---
avail_gb=$(( $(df -Pk / | awk 'NR==2{print $4}') / 1024 / 1024 ))
if   [ "$avail_gb" -ge 60 ]; then P "Disk free on /: ${avail_gb} GB"
elif [ "$avail_gb" -ge 40 ]; then W "Disk free on /: ${avail_gb} GB (tight; build wants ~40-60 GB)"
else F "Disk free on /: ${avail_gb} GB (need ~40 GB+; CUDA 12.8 + torch + images)"; fi

# --- RAM (source compiles of mamba-ssm/causal-conv1d are memory-hungry) ---
mem_gb=$(( $(awk '/MemTotal/{print $2}' /proc/meminfo) / 1024 / 1024 ))
[ "$mem_gb" -ge 16 ] && P "RAM: ${mem_gb} GB" || W "RAM: ${mem_gb} GB (16 GB+ recommended)"

# --- sudo (first-time Workbench/driver/docker install + CDI need it) ---
if sudo -n true 2>/dev/null; then P "Passwordless sudo available"
elif sudo -v 2>/dev/null;  then W "sudo works but may prompt — run 'sudo -v' just before BACKGROUND setup (it cannot answer a prompt)"
else F "No non-interactive sudo — run 'sudo -v' first (or configure passwordless sudo); BACKGROUND setup cannot answer a password prompt"; fi

# --- docker ---
if command -v docker >/dev/null 2>&1; then
  docker info >/dev/null 2>&1 && P "Docker reachable as this user" \
    || W "Docker installed but not reachable (daemon down or group not joined); setup tries 'sudo systemctl start docker'"
else
  W "Docker not installed — 'nvwb install --docker' installs it on first run (needs sudo + network)"
fi

# --- nvidia-ctk (CDI spec for the /run/cdi GPU mount used by M6) ---
command -v nvidia-ctk >/dev/null 2>&1 && P "nvidia-ctk present (CDI/GPU mount ready)" \
  || W "nvidia-ctk missing — installed with 'nvwb install --drivers'; needed for the M6 GPU mount"

# --- Workbench already installed? ---
[ -x "$HOME/.nvwb/bin/nvwb-cli" ] && P "NVIDIA AI Workbench already installed" \
  || W "NVIDIA AI Workbench not installed — setup downloads + installs it (first run)"

# --- Network reachability (WARN, not FAIL: corporate proxies/IPv6 cause false negatives; setup fails loudly if truly blocked) ---
R(){ curl -fsSL --max-time 12 -o /dev/null "$1" 2>/dev/null && P "Reachable: $2" || W "Unreachable: $2 — required on a FRESH box ($1)"; }
R "https://github.com"                                                  "github.com (clone + source builds)"
R "https://workbench.download.nvidia.com/stable/workbench-cli/LATEST"   "workbench.download.nvidia.com (Workbench CLI)"
R "https://build.nvidia.com"                                            "build.nvidia.com (NIM endpoints + API keys)"

echo
echo "== Summary: ${pass} pass, ${warn} warn, ${fail} fail =="
if [ "$fail" -gt 0 ]; then echo "Blocking issues present — resolve FAILs before running setup.sh."; exit 1; fi
echo "No blocking issues. Ready for setup.sh."; exit 0
