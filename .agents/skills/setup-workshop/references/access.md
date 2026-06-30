# Accessing DevX-Lab in a browser

After setup, the URL is written to `~/.workshop-app-url` and printed by
`scripts/start-app.sh`. It looks like:
```
http://localhost:<proxyPort>/projects/<PROJECT_NAME>/applications/DevX-Lab/
```
`<proxyPort>` is the local Workbench proxy (default **10000**; confirm with
`jq '.[]|select(.name=="local").proxyPort' ~/.nvwb/contexts.json`). The
Workbench proxy binds to **localhost only** — that single fact decides which
access mode applies.

## Mode A — desktop on the GPU machine (simplest)
The machine has a graphical browser. Open the URL directly. To let Workbench
auto-open it, start without `--no-browser`:
```bash
nvwb start DevX-Lab --context local --project <path>
```

## Mode B — headless GPU box, browser on a laptop (most common)
No GUI on the GPU host; reach it over SSH. Forward the proxy port, then browse
locally:
```bash
# On the laptop:
ssh -N -L 10000:localhost:10000 <user>@<gpu-host>
# then open in the laptop's browser:
http://localhost:10000/projects/<PROJECT_NAME>/applications/DevX-Lab/
```
Forwarding *to* `localhost:10000` means the browser's Host header is
`localhost:10000`, which the proxy accepts. Match the left-hand port to the
actual `proxyPort` if it isn't 10000. Keep the SSH session open while you work.
VS Code / Cursor "Forward a Port" on 10000 does the same thing through the UI.

## Mode C — temporary public share link (no SSH for the viewer)
Workbench can mint a time-boxed public URL (good for demos / sharing):
```bash
nvwb activate local --external-access
nvwb create share-url DevX-Lab --context local --project <path>   # ~48-hour link
```
Use sparingly — it exposes the lab to anyone with the link for the link's
lifetime.

## Mode D — clean single port (:8888) like Brev
For a tidy single-port entry or shared-host access without per-user port-forward,
run the optional nginx router from `references/persistence.md`. It serves :8888,
rewrites Host to localhost, and 302-redirects the bare path to the app — the same
front door a Brev instance presents. Not required for normal local use.

## Verifying it's actually up
```bash
source ~/.local/share/nvwb/nvwb-wrapper.sh
nvwb status                 # project open, container running
nvwb list apps              # DevX-Lab shown as running
curl -sI -H 'Host: localhost' http://localhost:10000/projects/<PROJECT_NAME>/applications/DevX-Lab/ | head -1
```
A `200`/`302` confirms the proxy is serving the app.
