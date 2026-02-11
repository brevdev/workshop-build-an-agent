#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

sudo npm install n -g
sudo n stable

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
