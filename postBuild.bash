#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Some workbench base images don't ship npm. Install it before using `n`.
command -v npm >/dev/null 2>&1 || { sudo apt-get update && sudo apt-get install -y npm; }

sudo apt-get update && sudo apt-get install -y openssh-client

sudo npm install n -g
sudo n stable

# Deep Agent Setup File
sudo mkdir -p /tmp/deepagent_workspace
sudo chown workbench:workbench /tmp/deepagent_workspace
FILE_PATH_1="/tmp/deepagent_workspace/passwords.txt"
FILE_PATH_2="/tmp/deepagent_workspace/ssn_records.txt"

# Check if the file does NOT exist
if [ ! -e "$FILE_PATH_1" ]; then
    echo "Creating file and writing content..."
    echo "admin:SuperSecret123! \nroot:P@ssw0rd_2026 \ndb_user:mysql_prod_xK9#mN2" > "$FILE_PATH_1"
else
    echo "File already exists. No action taken."
fi

if [ ! -e "$FILE_PATH_2" ]; then
    echo "Creating file and writing content..."
    echo "user 1: 123-45-6789 \nuser 2: 987-65-4321" > "$FILE_PATH_2"
else
    echo "File already exists. No action taken."
fi

# Install CUDA Toolkit
# 1. Detect Architecture
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

if [ "$ARCH" = "x86_64" ]; then
    CUDA_URL="https://developer.download.nvidia.com/compute/cuda/12.8.0/local_installers/cuda_12.8.0_570.86.10_linux.run"
    INSTALLER_NAME="cuda_12.8_x86_64.run"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    CUDA_URL="https://developer.download.nvidia.com/compute/cuda/12.8.0/local_installers/cuda_12.8.0_570.86.10_linux_sbsa.run"
    INSTALLER_NAME="cuda_12.8_arm64.run"
else
    echo "Error: Unsupported architecture $ARCH"
    exit 1
fi

# 2. Download and Install
echo "Downloading CUDA 12.8 for $ARCH..."
cd /tmp
wget -O "$INSTALLER_NAME" "$CUDA_URL"

echo "Installing CUDA Toolkit (this may take a minute)..."
# Using 'sh' explicitly. redirecting output to suppress noise but keep errors visible if needed
sudo sh "$INSTALLER_NAME" --toolkit --silent --override

# 3. Configure Environment Variables
# Define the paths
CUDA_PATH="/usr/local/cuda-12.8"
BIN_PATH="$CUDA_PATH/bin"
LIB_PATH="$CUDA_PATH/lib64"

# Add to .bashrc only if not already there to avoid duplicates
if ! grep -q "export CUDA_HOME=$CUDA_PATH" ~/.bashrc; then
    echo "Updating ~/.bashrc..."
    echo "export CUDA_HOME=$CUDA_PATH" >> ~/.bashrc
    echo "export PATH=$BIN_PATH:\$PATH" >> ~/.bashrc
    echo "export LD_LIBRARY_PATH=$LIB_PATH:\$LD_LIBRARY_PATH" >> ~/.bashrc
fi

# Export for the current session immediately
export CUDA_HOME="$CUDA_PATH"
export PATH="$BIN_PATH:$PATH"
export LD_LIBRARY_PATH="$LIB_PATH:$LD_LIBRARY_PATH"

# 4. Verify Installation
echo "Verifying installation..."
if command -v nvcc &> /dev/null; then
    nvcc --version
    echo "SUCCESS: CUDA 12.8 installed and reachable."
else
    echo "WARNING: CUDA installed but 'nvcc' not found in PATH yet."
    echo "Try running: source ~/.bashrc"
fi

# Cleanup
rm "$INSTALLER_NAME"
cd - > /dev/null

# On aarch64, pypi's default torch==2.10.0 wheel is CPU-only (146MB).
# Force CUDA-enabled torch from pytorch.org/whl/cu128 for Grace-Blackwell (DGX Spark GB10).
# x86_64 pypi torch 2.10.0 is already CUDA-bundled (915MB), no override needed.
# --extra-index-url lets pip fall back to pypi for non-torch transitive deps.
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    echo "Reinstalling torch with CUDA 12.8 support for aarch64 (Grace-Blackwell)..."
    pip install --user --force-reinstall \
        --index-url https://download.pytorch.org/whl/cu128 \
        --extra-index-url https://pypi.org/simple \
        torch==2.10.0
    python3.12 -c "import torch; assert torch.version.cuda is not None, f'torch is not CUDA-enabled: {torch.__version__}'; print(f'torch={torch.__version__}, cuda={torch.version.cuda}')"
fi

# Install Mamba/Nemotron CUDA extensions (must be built with CUDA + torch present)
# TORCH_CUDA_ARCH_LIST is arch-specific to compile only SMs reachable on each arch:
#   - x86_64: sm_80 (A100) + sm_90 (H100). sm_121 (Grace-Blackwell) is aarch64-exclusive.
#   - aarch64: sm_121 (DGX Spark GB10). sm_80 can never be reached on aarch64 (A100 is
#     x86_64-only); sm_90 (GH200) is a rare enterprise platform outside workshop scope.
# If you ever need to run the aarch64 container on GH200, change aarch64's list to
# "9.0;12.1". Compile time scales linearly with target count, so narrowing both arches
# cuts mamba-ssm+causal-conv1d build time by 33% on x86_64 and 66% on aarch64.
# CUDA_HOME/PATH/LD_LIBRARY_PATH were exported above so nvcc is reachable.
if [ "$ARCH" = "x86_64" ]; then
    export TORCH_CUDA_ARCH_LIST="8.0;9.0"
else
    export TORCH_CUDA_ARCH_LIST="12.1"
fi
# Force gcc/g++ as the C/C++ compiler for from-source extension builds.
# Our Python comes from python-build-standalone (see preBuild.bash), whose
# upstream artifacts are compiled with clang — so sysconfig.get_config_var('CXX')
# returns 'clang++'. setuptools then tries to invoke clang++, which isn't in
# the image, and the build dies with "clang++: No such file or directory".
# Torch's CUDA extensions are validated against g++ on Linux anyway (the
# WRONG_COMPILER_WARNING explicitly names g++), and g++ is installed via apt.txt.
# Note: the precompiled-wheel fallback masks this on x86_64 because causal-conv1d's
# setup.py hardcodes a 'linux_x86_64' URL, so the wheel download succeeds there
# and no source build happens. On aarch64 the URL 404s and we hit source build.
export CC=gcc
export CXX=g++

echo "Building causal-conv1d and mamba-ssm for TORCH_CUDA_ARCH_LIST=$TORCH_CUDA_ARCH_LIST (CC=$CC CXX=$CXX)..."

pip install --no-build-isolation "causal-conv1d @ git+https://github.com/Dao-AILab/causal-conv1d.git@v1.5.2"
pip install --no-build-isolation "mamba-ssm @ git+https://github.com/state-spaces/mamba.git@v2.2.5"

# Patch mamba-ssm for transformers 5.x compatibility
# (mamba-ssm 2.2.5 imports GreedySearchDecoderOnlyOutput which was removed in transformers 5.x)
MAMBA_GEN=$(python3.12 -c "import importlib.util; spec = importlib.util.find_spec('mamba_ssm'); print(spec.submodule_search_locations[0])" 2>/dev/null)/utils/generation.py
if [ -f "$MAMBA_GEN" ]; then
    sed -i 's/from transformers.generation import GreedySearchDecoderOnlyOutput, SampleDecoderOnlyOutput, TextStreamer/try:\n    from transformers.generation import GreedySearchDecoderOnlyOutput, SampleDecoderOnlyOutput, TextStreamer\nexcept ImportError:\n    from transformers.generation import GenerateDecoderOnlyOutput as GreedySearchDecoderOnlyOutput, GenerateDecoderOnlyOutput as SampleDecoderOnlyOutput, TextStreamer/' "$MAMBA_GEN"
    echo "Patched mamba-ssm for transformers 5.x compatibility"
else
    echo "WARNING: Could not find mamba-ssm generation.py to patch"
fi

# Patch trl's import_utils to force-disable any _X_available flag where
# `import X` actually fails. trl 0.24.0's _is_package_available() can return
# True from orphan .dist-info metadata (or PEP-420 namespace-package false
# positives), triggering eager import chains at module-load time that break
# trl's grpo_trainer. Real dependencies (unsloth, pydantic, fastapi, etc.)
# still import successfully, so their flags stay True and no legitimate
# functionality is disabled — only broken/absent packages get silenced.
#
# Confirmed orphan flags on the 2026-04 build: mergekit, llm_blender, weave.
# This loop auto-handles those plus any future ones (e.g. if trl ships a new
# optional extra in a minor version), so no manual list maintenance required.
TRL_IMPORT_UTILS=$(python3.12 -c "import importlib.util; print(importlib.util.find_spec('trl.import_utils').origin)" 2>/dev/null)
if [ -f "$TRL_IMPORT_UTILS" ]; then
    for pkg in $(grep -oP '_\w+_available = _is_package_available\("\K[^"]+' "$TRL_IMPORT_UTILS"); do
        if python3.12 -c "import ${pkg}" >/dev/null 2>&1; then
            echo "trl/import_utils.py: ${pkg} imports cleanly, leaving flag as-is"
        else
            sed -i "s/_${pkg}_available = _is_package_available(\"${pkg}\")/_${pkg}_available = False  # Patched: import test failed (see postBuild.bash)/" "$TRL_IMPORT_UTILS"
            echo "Patched trl/import_utils.py: _${pkg}_available = False (import test failed)"
        fi
    done
else
    echo "WARNING: trl/import_utils.py not found; skipping trl availability-flag patches"
fi
