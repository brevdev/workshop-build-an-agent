# install basic deps
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

# upgrade to python 3.12
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3.12 python3.12-dev python3.12-venv
sudo rm -rf /usr/bin/pip*
sudo python3.12 -m ensurepip --upgrade
sudo ln -s $(which python3.12) /usr/local/bin/python
sudo ln -s $(which pip3.12) /usr/local/bin/pip
sudo pip install --upgrade setuptools pip

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
