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

**Container restart (`docker restart`) — only inside the token window.** The
container boots from a static bootstrap JWT written once at create
(`/etc/openshell/auth/sandbox.jwt`, ~1-hour TTL, never refreshed on disk —
mtime verified unchanged across a 22-hour run and across restarts). Within
the window a restart recovers cleanly and boots any dormant
`filesystem_policy` grants (verified on OpenShell v0.0.96: Ready in ~10 s,
`/dev/pts` grant live afterwards). Past the window the supervisor re-reads
the expired token and crash-loops (`Unauthenticated`/`ExpiredSignature`),
leaving the sandbox stuck in `Provisioning` — verified live on both a
v0.0.53-created and a v0.0.96-resumed sandbox. Recovery then requires a
recreate (no token re-mint exists in the CLI).

**Gateway upgrades restart sandbox containers.** A restarted (upgraded)
gateway resumes sandboxes by restarting their containers, so every sandbox
older than its token window bricks as above — observed live during the
0.0.53 → 0.0.96 upgrade. Recreate sandboxes around gateway upgrades.

**After any container restart** (including a Phase 1b grant-boot restart):
the supervisor comes back (token window permitting) but the agent stack
(`nemoclaw-start`: agent, relay, bridges) stays down — and so does
JupyterLab. Relaunch the stack with the deployment-derived env file
(§ Recovering lost create-time env below, which doubles as the post-restart
relaunch procedure), then have the in-sandbox agent re-run
`start-jupyter.sh`.

**Sandbox recreate wipes the container filesystem** — venv, netlink shim,
`secrets.env`, `.launcher-config`, the running server, `/sandbox/workshop-url.txt`.
The sanctioned recreate path is the deployment's own machinery
(the example's `scripts/bring-up.sh` / `scripts/03-sandbox.sh`); it re-renders the
STOCK `policy.yaml` template, so every workshop grant (network AND
filesystem) reverts by design. After a recreate:

1. Re-apply the workshop policy (SKILL.md Phase 1) and boot the fs grants
   with the Phase 1b restart — the fresh sandbox is well inside the token
   window. Probe:
   `openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc 'curl -s -o /dev/null -w "%{http_code}" https://pypi.org/simple/'`
2. Verify the create-time authorization env survived (expect ≥ 1; if 0, see
   § Recovering lost create-time env below):
   `docker exec "$C" sh -c 'pid=$(pgrep -f "[h]ermes gateway run" | head -1); tr "\0" "\n" < /proc/$pid/environ' | grep -cE '^(SLACK_ALLOW|OUTLOOK_)'`
3. Re-stage `secrets.env` (Phase 2).
4. Tell the in-sandbox agent to re-run `setup.sh` + `start-jupyter.sh` (both
   idempotent).
5. Re-open the forward (Phase 4).

**What survives what:**

| Event | Policy | /sandbox files (venv, shim, secrets) | Agent stack | Jupyter |
|---|---|---|---|---|
| Gateway restart (same version) | ✓ | ✓ | ✓ | ✓ |
| Gateway upgrade (resume restarts containers) | ✓ | ✓ | ✗ | ✗ — and sandboxes past the token window brick |
| Container restart, inside token window | ✓ (dormant fs grants boot) | ✓ | ✗ relaunch stack | ✗ re-run start-jupyter.sh |
| Container restart, past token window | sandbox bricked (`ExpiredSignature`) — recreate | ✓ but unreachable | ✗ | ✗ |
| Sandbox recreate (recipe machinery) | STOCK template — re-run Phase 1 + 1b | ✗ wiped | ✓ (fresh) | ✗ full redo from Phase 2b |

## Recovering lost create-time env (Slack pairing-code regression)

The deployment recipe injects per-user **authorization** env at create
(`scripts/03-sandbox.sh` `-- env …`): `SLACK_ALLOWED_USERS` *or*
`SLACK_ALLOW_ALL_USERS`, plus `OUTLOOK_TARGET_MAILBOX` / `OUTLOOK_REPLY_TO` /
`OUTLOOK_ALLOWED_SENDERS`. These ride the exec session running
`nemoclaw-start`, NOT `/proc/1/environ` (PID 1 = supervisor: image ENV only).
The Slack/GitHub/Graph *tokens* are different: providers inject them into
every supervisor session, so they survive a recreate untouched.

Symptom set when the recreate lost the authorization env (all verified live):
the Slack bot still answers (tokens fine) but greets EVERY user with a pairing
code — `run.py:_is_user_authorized` finds neither `SLACK_ALLOWED_USERS` nor
`SLACK_ALLOW_ALL_USERS`; `ps` shows no `outlook-bridge.py`; the gateway env
check (recreate step 2 above) returns 0.

Fix WITHOUT another recreate (which would wipe the built workshop):

```bash
# 1. Rebuild the values exactly as scripts/03-sandbox.sh does, from the
#    deployment's .env (values never echoed):
cd <nemoclaw-community>/examples/recipes/nvidia/agentic-ai-learning-path
(
  set -a; source ./.env; set +a
  mapfile -t B64 < <(python3 scripts/lib/build-channels.py)
  ids=$(printf '%s' "${B64[1]}" | base64 -d | python3 -c 'import json,sys; print(",".join(json.load(sys.stdin).get("slack", [])))')
  umask 077
  {
    if [ -n "${SLACK_BOT_TOKEN:-}${SLACK_APP_TOKEN:-}" ]; then
      if [ -n "$ids" ]; then printf 'export SLACK_ALLOWED_USERS=%q\n' "$ids"
      else printf 'export SLACK_ALLOW_ALL_USERS=true\n'; fi
    fi
    printf 'export OUTLOOK_TARGET_MAILBOX=%q\n'  "${OUTLOOK_TARGET_MAILBOX:-}"
    printf 'export OUTLOOK_REPLY_TO=%q\n'        "${OUTLOOK_REPLY_TO:-}"
    printf 'export OUTLOOK_ALLOWED_SENDERS=%q\n' "${OUTLOOK_ALLOWED_SENDERS:-}"
  } > /tmp/nemoclaw-restore-env.sh
)
docker cp /tmp/nemoclaw-restore-env.sh "$C:/tmp/nemoclaw-restore-env.sh"
docker exec "$C" chown sandbox:sandbox /tmp/nemoclaw-restore-env.sh

# 2. Kill the stack, then relaunch it under a SUPERVISOR session — leave this
#    stream running (tmux/background); it is the stack's parent:
docker exec "$C" bash -c 'pkill -f "[h]ermes gateway run"; pkill -f "[s]ocat TCP-LISTEN:8642"; pkill -f "[n]emo-relay --bind"; pkill -f "[o]utlook-bridge.py"; pkill -f "bash /usr/local/bin/[n]emoclaw-start"'
openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc 'set -a; . /tmp/nemoclaw-restore-env.sh; set +a; exec /usr/local/bin/nemoclaw-start'

# 3. From another shell — verify, then detach the LOCAL client (the remote
#    session and the stack survive, same detach as the recipe's create flow):
docker exec "$C" sh -c 'pid=$(pgrep -f "[h]ermes gateway run" | head -1); tr "\0" "\n" < /proc/$pid/environ' | grep -cE '^(SLACK_ALLOW|OUTLOOK_)'   # ≥ 1
openshell sandbox exec -n "$SANDBOX" --no-tty -- sh -lc '. /sandbox/.hermes-data/.env >/dev/null 2>&1; curl -sS --max-time 12 -X POST -H "Authorization: Bearer ${SLACK_APP_TOKEN}" https://slack.com/api/apps.connections.open'   # → "ok":true
pkill -f "sandbox [e]xec -n $SANDBOX"
docker exec "$C" rm -f /tmp/nemoclaw-restore-env.sh
```

Do NOT relaunch the stack via `docker exec` — both variants fail (observed
live). As root: `drop_capabilities` strips `CAP_DAC_OVERRIDE`, so
`nemoclaw-start` dies reading the sandbox-owned config — and its early log
setup leaves root-owned `/tmp/nemoclaw-start.log` + `/tmp/nemoclaw-proxy-env.sh`
that block every later sandbox-user relaunch (sticky `/tmp`; clean them as
root first if this happened). As `-u sandbox`: the stack starts, but it lives
OUTSIDE the supervisor's inner netns, so the L7 proxy cannot attribute its
flows — Slack connects die with `403 http://10.200.0.1:3128` and the audit log
fills with `graph.microsoft.com … failed to resolve peer binary`. Also avoid
`setsid nohup … &` inside the supervisor session (hung the session twice,
never spawning); the plain foreground `exec` form starts immediately.

Durability: `nemoclaw-start` re-emits the restored vars into
`/tmp/nemoclaw-proxy-env.sh` (sourced by later `bash -l` sessions), so
profile-based relaunches keep them from then on. JupyterLab daemonizes outside the stack: token, URL, and the host forward
all survive this surgery.

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
