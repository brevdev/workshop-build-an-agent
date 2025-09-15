#!/bin/bash

### STARTUP SCRIPT CONFIGURATION ###
readonly GIT_REPO="https://github.com/nv-edwli/workshop-build-an-agent"
readonly TARGET_BRANCH=rkraus/new-lab
readonly TARGET_APPLICATION=DevX-Lab
readonly LOG_FILE=/home/ubuntu/.startup-script.log

#################################
### END OF USER CONFIGURATION ###
#################################



### CREATE LOG FILE ###
cat > $LOG_FILE << EOF
### STARTUP SCRIPT LOG ###
$(date): Starting startup script
$(date): GIT_REPO: $GIT_REPO
$(date): TARGET_BRANCH: $TARGET_BRANCH
$(date): TARGET_APPLICATION: $TARGET_APPLICATION
$(date): BREV_PROJ_DIR: $BREV_PROJ_DIR

EOF

### WAIT FOR APT TO BE READY ###
while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || sudo fuser /var/cache/apt/archives/lock >/dev/null 2>&1; do
    echo "$(date): APT is locked, waiting 10 seconds..." | tee -a $LOG_FILE
    sleep 10
done

### STARTUP SCRIPT ###
sudo -i -u ubuntu /bin/bash --login << EOF 2>&1 | tee -a $LOG_FILE
### INSTALL NVIDIA AI WORKBENCH ###
sudo systemctl start docker

# Download and install NVIDIA AI Workbench only if not already present
if [ ! -d "~/.nvwb/bin" ]; then
    echo "NVIDIA AI Workbench not found, lets fix that..."

    # Download NVIDIA AI Workbench
    echo "Downloading NVIDIA AI Workbench..."
    mkdir -p ~/.nvwb/bin
    curl -L https://workbench.download.nvidia.com/stable/workbench-cli/$(curl -L -s https://workbench.download.nvidia.com/stable/workbench-cli/LATEST)/nvwb-cli-$(uname)-$(uname -m) --output ~/.nvwb/bin/nvwb-cli
    chmod +x ~/.nvwb/bin/nvwb-cli

    # Install NVIDIA AI Workbench
    echo "Installing NVIDIA AI Workbench..."
    sudo ~/.nvwb/bin/nvwb-cli install --noninteractive --accept --docker --drivers --uid 1000 --gid 1000
else
    echo "NVIDIA AI Workbench already installed. Skipping download and installation."
fi
EOF


sudo -i -u ubuntu /bin/bash --login << EOF 2>&1 | tee -a $LOG_FILE
### CLONE AND CONFIGURE WORKSHOP ###
# Ensure workbench is loaded
source ~/.bashrc
source ~/.local/share/nvwb/nvwb-wrapper.sh

# Clone workshop
nvwb activate local
nvwb clone project $GIT_REPO --context local

# Locate the project's file path
export PROJECT_PATH=\$(nvwb list projects -o json | jq -r '.result[] | select(.RemoteUrl == "'$GIT_REPO'").Path')
export PROJECT_NAME=\$(nvwb list projects -o json | jq -r '.result[] | select(.RemoteUrl == "'$GIT_REPO'").Name')
echo "Project name: \$PROJECT_NAME"
echo "Project path: \$PROJECT_PATH"

# Stop any current activity and switch to the target branch
nvwb discard --context local --project \$PROJECT_PATH
nvwb switch-branch $TARGET_BRANCH --context local --project \$PROJECT_PATH

# Build the application
nvwb build --context local --project \$PROJECT_PATH

# Configure project's system mounts
nvwb configure mounts /var/run/:/var/host-run/ --project \$PROJECT_PATH --context local


### CONFIGURE WORKSHOP SERVICE UNIT FILE ###
# Create startup script for systemd service
cat > ~/nvwb-startup.sh << SCRIPT_EOF
#!/bin/bash
source ~/.bashrc
source ~/.local/share/nvwb/nvwb-wrapper.sh

# Locate the project's file path
export PROJECT_PATH=\$(nvwb list projects -o json | jq -r '.result[] | select(.RemoteUrl == "'$GIT_REPO'").Path')
echo "Starting project: \$PROJECT_PATH"

# Activate local context and start the application
cd ~
nvwb activate local
nvwb start $TARGET_APPLICATION --context local --project \$PROJECT_PATH

echo "NVIDIA AI Workbench startup script completed"
SCRIPT_EOF
chmod +x ~/nvwb-startup.sh

# Create systemd service file
sudo tee /etc/systemd/system/nvwb-workshop.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=DevX Workshop with NVIDIA AI Workbench
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
User=ubuntu
Group=ubuntu
ExecStart=/home/ubuntu/nvwb-startup.sh
WorkingDirectory=/home/ubuntu
Environment=HOME=/home/ubuntu
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Enable and run the service
sudo systemctl daemon-reload
sudo systemctl enable --now nvwb-workshop.service
echo "NVIDIA AI Workbench workshop service has been created and enabled."
echo "The service will automatically start the workbench application on system reboot."
echo "You can check the service status with: sudo systemctl status nvwb-workshop.service"
echo "View logs with: sudo journalctl -u nvwb-workshop.service -f"



### NGINX SERVICE ROUTER ###
# Install nginx
DEBIAN_FRONTEND=noninteractive sudo apt-get install -y nginx

# Create nginx configuration
sudo tee /etc/nginx/nginx.conf > /dev/null << NGINX_EOF
user  www-data;
worker_processes  auto;

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    # --- Upgrade mapping for WebSockets ---
    map \\\$http_upgrade \\\$connection_upgrade {
        default upgrade;
        ''      close;
    }

    # --- AI Workbench proxy server ---
    upstream workbench_proxy {
        server 127.0.0.1:10000;
        keepalive 32;
    }

    # --- Main server ---
    server {
        listen 8888;
        server_name _;

        # 1) Proxy requests that begin with /projects/
        location ^~ /projects/ {
            proxy_pass         http://workbench_proxy;
            proxy_http_version 1.1;

            # Backend must see "localhost" as the Host header
            proxy_set_header Host               localhost;
            proxy_set_header Origin             http://localhost;
            proxy_set_header X-Forwarded-Host   \\\$host;

            # Forward client info
            proxy_set_header X-Real-IP          \\\$remote_addr;
            proxy_set_header X-Forwarded-For    \\\$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto  http;

            # WebSockets / streaming
            proxy_set_header Upgrade            \\\$http_upgrade;
            proxy_set_header Connection         \\\$connection_upgrade;
            proxy_read_timeout                  3600;
            proxy_send_timeout                  3600;

            # Disable buffering for Jupyter streaming
            proxy_buffering                     off;
            proxy_cache                         off;
        }

        # 2) Everything else: redirect into the Jupyter app path
        location / {
            return 302 https://\\\$host/projects/\$PROJECT_NAME/applications/$TARGET_APPLICATION\\\$request_uri;
        }
    }
}
NGINX_EOF

# Enable and start nginx
sudo systemctl enable --now nginx
sudo systemctl restart nginx
EOF


### LOG FILE COMPLETION ###
cat >> $LOG_FILE << EOF
### STARTUP SCRIPT LOG ###
$(date): Startup script completed
EOF
