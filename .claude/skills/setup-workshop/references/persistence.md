# Optional persistence — Brev-parity extras

Neither of these is needed to use the workshop locally; they reproduce two
conveniences of the Brev deployment. Add them only if asked.

## A. Auto-start DevX-Lab on boot (systemd)
Goal: the lab comes back automatically after a reboot, like a cloud instance.

1. Copy `start-app.sh` to a stable location (so the unit doesn't depend on the
   skill's path), and make it executable:
   ```bash
   mkdir -p ~/.local/bin
   cp .claude/skills/setup-workshop/scripts/start-app.sh ~/.local/bin/workshop-start.sh
   chmod +x ~/.local/bin/workshop-start.sh
   ```
2. Render `assets/nvwb-workshop.service.template`, substituting:
   - `__INSTALL_USER__`  → `whoami`
   - `__INSTALL_GROUP__` → `id -gn`
   - `__INSTALL_HOME__`  → `echo $HOME`
   - `__START_SCRIPT__`  → `$HOME/.local/bin/workshop-start.sh`
3. Install and enable:
   ```bash
   sudo tee /etc/systemd/system/nvwb-workshop.service < /tmp/nvwb-workshop.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now nvwb-workshop.service
   systemctl status nvwb-workshop.service          # check
   journalctl -u nvwb-workshop.service -f          # follow logs
   ```

Notes:
- `Type=oneshot` + `RemainAfterExit=yes`: the unit "succeeds" once the app is
  launched and stays "active" without holding a foreground process.
- The unit must run as the user who installed Workbench (the context lives in
  that user's `~/.nvwb`). `Environment=HOME=...` ensures the wrapper resolves.
- It does NOT build. The container must already be built once (`setup.sh`).

## B. Single-port nginx router (:8888)
Goal: one clean port that forwards to the Workbench proxy and rewrites the Host
header — the front door a Brev instance exposes. Useful for shared hosts or to
avoid per-user SSH port-forwards.

1. Install nginx:
   ```bash
   DEBIAN_FRONTEND=noninteractive sudo apt-get update
   DEBIAN_FRONTEND=noninteractive sudo apt-get install -y nginx
   ```
2. Render `assets/nginx-workshop.conf.template`, substituting:
   - `__PROJECT_NAME__` → the project Name
     (`nvwb list projects -o json | jq -r '.result[]|select(.RemoteUrl|test("workshop-build-an-agent")).Name'`)
   - `__APP__`          → `DevX-Lab`
3. Install and (re)start:
   ```bash
   sudo cp /tmp/nginx-workshop.conf /etc/nginx/nginx.conf
   sudo nginx -t                       # validate config
   sudo systemctl enable --now nginx
   sudo systemctl restart nginx
   ```
4. Browse `http://<host>:8888/` — it 302-redirects into the DevX-Lab path.

Differences from the Brev config (intentional):
- Redirect uses **http** + `$scheme` (Brev hard-codes https because its ingress
  terminates TLS upstream; a bare local box has no TLS).
- Everything else (Host rewrite to `localhost`, WebSocket upgrade map, buffering
  off for Jupyter streaming, 3600s timeouts) is preserved — those are what make
  JupyterLab work through the proxy.

If `:8888` is taken, change `listen 8888;` to a free port. Open the port in any
host firewall (`ufw allow 8888/tcp`) only if external access is intended.
