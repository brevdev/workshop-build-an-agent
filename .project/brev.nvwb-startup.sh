#!/bin/bash

sudo -i -u ubuntu bash << 'EOF'
readonly GIT_REPO=https://github.com/nv-edwli/workshop-build-an-agent
readonly TARGET_BRANCH=develop
readonly TARGET_APPLICATION=DevX-Lab
sudo systemctl start docker
# Download and install NVIDIA AI Workbench only if not already present
if [ ! -d "$HOME/.nvwb/bin" ]; then
    echo "NVIDIA AI Workbench not found. Downloading and installing..."
    
    # Download NVIDIA AI Workbench
    mkdir -p $HOME/.nvwb/bin
    curl -L https://workbench.download.nvidia.com/stable/workbench-cli/$(curl -L -s https://workbench.download.nvidia.com/stable/workbench-cli/LATEST)/nvwb-cli-$(uname)-$(uname -m) --output $HOME/.nvwb/bin/nvwb-cli
    chmod +x $HOME/.nvwb/bin/nvwb-cli
    # Install NVIDIA AI Workbench
    sudo $HOME/.nvwb/bin/nvwb-cli install --noninteractive --accept --docker --drivers --uid 1000 --gid 1000
else
    echo "NVIDIA AI Workbench already installed. Skipping download and installation."
fi
export PATH="$HOME/.nvwb/bin:$PATH"
echo 'export PATH="$HOME/.nvwb/bin:$PATH"' >> ~/.bashrc
ln -sf $HOME/.nvwb/bin/nvwb-cli $HOME/.nvwb/bin/nvwb
# Clone workshop, avoid default branch build
nvwb activate local
nvwb clone project $GIT_REPO --context local
nvwb discard --context local --project $HOME/nvidia-workbench/*-build-an-agent
nvwb switch-branch $TARGET_BRANCH --context local --project $HOME/nvidia-workbench/*-build-an-agent
nvwb build --context local --project $HOME/nvidia-workbench/*-build-an-agent
nvwb start $TARGET_APPLICATION --context local --project $HOME/nvidia-workbench/*-build-an-agent
# Create reboot script for systemd service
cat > $HOME/nvwb-reboot.sh << 'REBOOT_EOF'
#!/bin/bash
# Wait for system to be fully ready
sleep 30
# Set environment
export PATH="$HOME/.nvwb/bin:$PATH"
readonly TARGET_APPLICATION=DevX-Lab
# Log output for debugging
exec > $HOME/nvwb-reboot.log 2>&1
echo "$(date): Starting NVIDIA AI Workbench reboot script"
# Activate local context and start the application
cd $HOME
nvwb activate local
nvwb start $TARGET_APPLICATION --context local --project $HOME/nvidia-workbench/*-build-an-agent
echo "$(date): NVIDIA AI Workbench reboot script completed"
REBOOT_EOF
chmod +x $HOME/nvwb-reboot.sh
EOF

# Create systemd service file
sudo tee /etc/systemd/system/nvwb-startup.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=NVIDIA AI Workbench Startup Service
After=network.target docker.service
Wants=docker.service
[Service]
Type=oneshot
User=ubuntu
Group=ubuntu
ExecStart=/home/ubuntu/nvwb-reboot.sh
WorkingDirectory=/home/ubuntu
Environment=HOME=/home/ubuntu
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Enable the service to run on boot
sudo systemctl daemon-reload
sudo systemctl enable nvwb-startup.service

echo "NVIDIA AI Workbench startup service has been created and enabled."
echo "The service will automatically start the workbench application on system reboot."
echo "You can check the service status with: sudo systemctl status nvwb-startup.service"
echo "View logs with: sudo journalctl -u nvwb-startup.service -f"