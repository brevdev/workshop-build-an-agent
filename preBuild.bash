#!/bin/bash
set -e  # Fail fast so silent install failures don't cascade into corrupted apt sources / missing python3.12

# install basic deps
# NOTE: `apt-get update` is required first — the base image
# (nvcr.io/nvidia/ai-workbench/python-basic) ships with a pruned
# /var/lib/apt/lists/, so a bare `apt-get install` would fail to resolve
# packages. If lsb-release silently fails to install here, the docker.list
# write below evaluates `$(lsb_release -cs)` to empty and produces a
# malformed apt source (missing Component field), which then breaks every
# subsequent `apt-get update` in the build.
sudo apt-get update
sudo apt-get install -y software-properties-common lsb-release ca-certificates gnupg

# configure user default profile
cat <<EOM >> ~/.bashrc
# configure support for loading secrets from project file
if [ -f /project/secrets.env ]; then
    set -a
    source /project/secrets.env
    set +a
fi

# configure support for local home directory bin
export PATH=~/.local/bin/:~/bin:\$PATH

# helper for NGC keys
export NGC_API_KEY=\$NVIDIA_API_KEY
export NGC_CLI_API_KEY=\$NVIDIA_API_KEY
EOM

# Install Python 3.12 from python-build-standalone (pre-built CPython tarball).
# NOTE: This block previously used deadsnakes PPA via add-apt-repository, but
# launchpadlib times out reaching api.launchpad.net from some Brev networks
# (e.g. Crusoe). python-build-standalone is a single tarball served from
# github.com, which is reliably reachable. deepagents (and other deps in
# requirements.txt) require Python >= 3.11, so 3.10 fallback is not viable.
ARCH=$(uname -m)
PBS_DATE="20260414"
PY_VERSION="3.12.13"
if [ "$ARCH" = "x86_64" ]; then
    PBS_TRIPLE="x86_64-unknown-linux-gnu"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    PBS_TRIPLE="aarch64-unknown-linux-gnu"
else
    echo "Unsupported architecture: $ARCH"; exit 1
fi
PBS_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PBS_DATE}/cpython-${PY_VERSION}%2B${PBS_DATE}-${PBS_TRIPLE}-install_only.tar.gz"
echo "Downloading Python ${PY_VERSION} from python-build-standalone..."
curl -fsSL "$PBS_URL" | sudo tar -xz -C /opt/
sudo ln -sf /opt/python/bin/python3.12 /usr/local/bin/python3.12
sudo ln -sf /opt/python/bin/pip3.12 /usr/local/bin/pip3.12
sudo ln -sf /opt/python/bin/python3.12 /usr/local/bin/python
sudo ln -sf /opt/python/bin/pip3.12 /usr/local/bin/pip
sudo /opt/python/bin/pip3.12 install --upgrade setuptools pip

# configure custom docker apt repo
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# configure support for dynamic docker group gid
cat <<EOM | sudo tee /etc/profile.d/join-docker-group.sh > /dev/null
if [ -S /var/host-run/docker.sock ]; then
    if [ "\$(id -u)" -ne 0 ]; then
        docker_gid=\$(stat -c %g /var/host-run/docker.sock)
        current_user=\$(whoami)

        # Check if user is already in the group that owns docker.sock (by GID)
        if ! id -G "\$current_user" | grep -q "\\b\$docker_gid\\b"; then
            # Try to find existing group with this GID
            existing_group=\$(getent group "\$docker_gid" | cut -d: -f1)

            if [ -n "\$existing_group" ]; then
                # Group exists, add user to it
                sudo usermod -aG "\$existing_group" "\$current_user"
            else
                # Group doesn't exist, create it and add user
                sudo groupadd -g \$docker_gid host-docker
                sudo usermod -aG host-docker "\$current_user"
            fi
        fi
    fi
fi
export DOCKER_HOST="unix:///var/host-run/docker.sock"
EOM

# configure permanent sudo without password
echo "$(whoami) ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/workbench-persist > /dev/null
