# Access path & sandbox lifecycle — details and failure modes

## Why the tunnel chain exists

Agent processes run in an **inner network namespace** inside the container
(outer `eth0` on the docker bridge, inner namespace behind a veth pair). A
server the agent binds — even to `0.0.0.0` — is unreachable at the container
IP (verified: connection refused / `http_code=000`). Docker publishes no ports
for the sandbox. The only inbound path is OpenShell's gRPC forward to the
sandbox **inner loopback**, then a normal SSH hop from the laptop:

```
laptop ──ssh/tsh -L 8888──▶ sandbox host ──openshell forward service (gRPC)──▶ 127.0.0.1:8888 inside sandbox
```

## Host leg

```bash
openshell forward service "$SANDBOX" --target-port 8888 --local 8888
```

- Runs in the **foreground** — leave the terminal open (or run under tmux).
- `openshell forward list` / `forward stop` do **NOT** track `forward service`
  tunnels (they manage `forward start` ones). Stop with Ctrl-C or
  `pkill -f "forward service $SANDBOX"`.
- Sanity check from another host shell:
  `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8888/lab` →
  `302` (auth redirect = alive; with the token appended it is `200`;
  `/api/status` without a token → `403` — all healthy signals).
- Token URL without asking the agent to paste secrets (the gateway masks
  tokens in agent output): `docker exec "$C" cat /sandbox/workshop-url.txt`.

## Laptop leg — vanilla SSH

```bash
ssh -N -L 8888:localhost:8888 <user>@<sandbox-host>
```

## Laptop leg — Teleport (tsh)

```bash
tsh ssh -N -L 8888:localhost:8888 <user>@<node-name>
```

1. **Use the Teleport NODE NAME** (from `tsh ls` on the laptop), not the
   host's DNS name or IP. `tsh` resolves targets against the Teleport cluster;
   an unmatchable target can hang node resolution indefinitely — the classic
   "tsh just hangs" cause.
2. **`-N` is SILENT when it works.** No prompt, no output — that IS the tunnel
   running. Open the browser before assuming a hang.
3. Fallbacks, in order:
   - Drop `-N`: `tsh ssh -L 8888:localhost:8888 <user>@<node-name>` gives a
     normal shell with the tunnel attached — keep the shell open. (Some tsh
     versions handle `-L` more reliably with a session attached.)
   - `tsh config >> ~/.ssh/config` once on the laptop, then use vanilla
     `ssh -N -L …` with the Teleport-generated host alias.
   - Browser "connection reset" + a tsh port-forwarding error → the Teleport
     role has `port_forwarding` disabled; that needs a Teleport admin.

Then open `http://localhost:8888/lab?token=…` in the laptop browser.

## Lifecycle & recovery

**Container restart (`docker restart`) — DON'T.** The container boots from a
static bootstrap JWT with a 1-hour TTL that is not refreshed on disk. A
restart re-reads the stale token and the supervisor crash-loops
(`Policy fetch failed … ExpiredSignature`), leaving the sandbox stuck in
`Provisioning`. Recovery requires re-minting the bootstrap token or a full
delete/recreate/restore cycle.

**If the container did restart anyway:** the supervisor comes back but the
agent stack (`nemoclaw-start`: agent, relay, bridges) stays down — and so does
JupyterLab. Relaunch the stack (community repo: `bash scripts/autoheal/watchdog.sh`),
then have the in-sandbox agent re-run `start-jupyter.sh`.

**Sandbox recreate wipes the container filesystem** — venv, netlink shim,
`secrets.env`, `.launcher-config`, the running server, `/sandbox/workshop-url.txt`.
Policy is re-rendered from the `policy.yaml` TEMPLATE at recreate, which is
why the workshop blocks must live in the template, not only in the live
policy. After a recreate:

1. Verify policy blocks survived (they did if the template was kept in sync):
   `openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc 'curl -s -o /dev/null -w "%{http_code}" https://pypi.org/simple/'`
2. Re-stage `secrets.env` (Phase 2).
3. Tell the in-sandbox agent to re-run `setup.sh` + `start-jupyter.sh` (both
   idempotent).
4. Re-open the forward (Phase 4).

**What survives what:**

| Event | Policy | /sandbox files (venv, shim, secrets) | Agent stack | Jupyter |
|---|---|---|---|---|
| Gateway restart | ✓ | ✓ | ✓ | ✓ |
| Container restart (avoid!) | ✓ (if JWT valid) | ✓ | ✗ relaunch stack | ✗ re-run start-jupyter.sh |
| Sandbox recreate | re-rendered from TEMPLATE | ✗ wiped | ✓ (fresh) | ✗ full redo from Phase 2 |

**Persona/SOUL gating (NemoClaw).** The agent's `SOUL.md` may prohibit
git/PyPI/web-serving, making it refuse newly-granted capabilities. The durable
copy lives in the operator repo (`agents/hermes/SOUL.md` in the community
example); the runtime copy at `/sandbox/.hermes-data/SOUL.md` (upload +
`chown sandbox:sandbox`). The gateway caches it at startup — until the stack
restarts, just tell the live agent explicitly what is now allowed ("Policy now
allows X — try again").

**Relay discipline.** When relaying setup guidance into the sandbox, relay
*capabilities* ("PyPI is open now"), not environment guesses. A wrongly
relayed TLS path (`/etc/ssl/certs/ca-certificates.crt`) once broke uv inside
the sandbox and cost debugging round-trips — the in-sandbox skill knows the
correct value (`/etc/openshell-tls/ca-bundle.pem`); don't override it.
