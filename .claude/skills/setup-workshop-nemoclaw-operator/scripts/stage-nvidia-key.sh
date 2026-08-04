#!/usr/bin/env bash
# stage-nvidia-key.sh — OPTIONALLY write API keys into the sandbox's workshop
# secrets.env WITHOUT them touching chat, argv, logs, or shell history.
# Run on the sandbox HOST. A human should run this (it moves credentials).
#
# ⚠️ NOT the primary path for NVIDIA_API_KEY. The workshop's own **Secrets
# Manager** tile (JupyterLab launcher) is the intended way for the learner to
# set it, and leaving the key UNSET at server-launch time is deliberate — see
# "Why unset is the default" below. Use this script only to pre-seed a key from
# the host (e.g. an unattended classroom image).
#
# Key sources (first match wins), per key, ALL OPTIONAL:
#   1. $NVIDIA_API_KEY / $TAVILY_API_KEY / $LANGSMITH_API_KEY already exported
#   2. --env-file <path>  : a dotenv file carrying any of those three names
#   3. stdin (piped, NVIDIA only):  printf '%s' "$KEY" | stage-nvidia-key.sh
#
# ⚠️ There is deliberately NO fallback to COMPATIBLE_API_KEY / OPENAI_API_KEY.
# Those name the NemoClaw *agent's* inference credential, which in the community
# example is an `sk-…` key for the host TLS proxy — NOT a build.nvidia.com
# `nvapi-…` key. Injecting it produced a secrets.env that looked correctly
# populated but made every notebook fail with a confusing
# `AuthenticationError: 401 Unauthorized` against integrate.api.nvidia.com.
# To stage a key, pass a real `nvapi-…` one explicitly.
#
# Why unset is the default: start-jupyter.sh `set -a`-sources secrets.env into
# the Jupyter server env at launch, and kernels inherit that env. python-dotenv's
# load_dotenv() does NOT override variables already present in the environment,
# so a value baked in at launch SHADOWS later edits to the file — the learner
# sets the key in the Secrets Manager, the file on disk is correct, and the
# kernel still sends the old value until the server restarts. Leaving
# NVIDIA_API_KEY absent at launch keeps load_dotenv() authoritative, so a
# Secrets Manager change takes effect on the next cell run with no restart.
# That is exactly why the TAVILY and LANGSMITH keys never showed this problem.
set -euo pipefail

SANDBOX="${SANDBOX:-hermes-direct}"
DEST="${DEST:-/sandbox/workshop-build-an-agent/secrets.env}"
ENV_FILE=""
[ "${1:-}" = "--env-file" ] && ENV_FILE="${2:?usage: stage-nvidia-key.sh [--env-file <path>]}"

# Exact, fail-closed container selection (shared helper).
. "$(dirname "$0")/lib.sh"
C=$(resolve_sandbox_container "$SANDBOX") || { echo "FATAL: container selection failed"; exit 1; }

# Resolve keys into vars without echoing them.
KEY="${NVIDIA_API_KEY:-}"
TAVILY="${TAVILY_API_KEY:-}"
LANGSMITH="${LANGSMITH_API_KEY:-}"
if [ -n "$ENV_FILE" ]; then
  [ -f "$ENV_FILE" ] || { echo "FATAL: env file not found: $ENV_FILE"; exit 1; }
  # Subshell substitutions — values never touch disk or argv. Note the absence
  # of any COMPATIBLE_API_KEY fallback (see the header).
  # shellcheck disable=SC1090
  [ -n "$KEY" ]       || KEY=$(set -a; . "$ENV_FILE" >/dev/null 2>&1; printf '%s' "${NVIDIA_API_KEY:-}")
  # shellcheck disable=SC1090
  [ -n "$TAVILY" ]    || TAVILY=$(set -a; . "$ENV_FILE" >/dev/null 2>&1; printf '%s' "${TAVILY_API_KEY:-}")
  # shellcheck disable=SC1090
  [ -n "$LANGSMITH" ] || LANGSMITH=$(set -a; . "$ENV_FILE" >/dev/null 2>&1; printf '%s' "${LANGSMITH_API_KEY:-}")
fi
if [ -z "$KEY" ] && [ ! -t 0 ]; then
  KEY=$(cat)
fi

if [ -z "$KEY" ] && [ -z "$TAVILY" ] && [ -z "$LANGSMITH" ]; then
  cat >&2 <<'MSG'
Nothing to stage: no NVIDIA_API_KEY, TAVILY_API_KEY, or LANGSMITH_API_KEY found
(checked exported env, --env-file, and stdin). In the normal flow this is NOT a
problem — NVIDIA_API_KEY is meant to be left unset so the learner sets it in the
workshop's Secrets Manager tile, where it takes effect without a JupyterLab
restart. Nothing was written; any existing secrets.env is untouched.
MSG
  exit 1
fi

# Warn loudly on a non-build.nvidia.com key — the exact mistake the old
# COMPATIBLE_API_KEY fallback used to make silently.
if [ -n "$KEY" ] && [ "${KEY#nvapi-}" = "$KEY" ]; then
  echo "WARNING: NVIDIA_API_KEY does not start with 'nvapi-'. The workshop calls" >&2
  echo "         integrate.api.nvidia.com, which accepts only build.nvidia.com keys." >&2
  echo "         Staging it anyway; expect 401 if this is not an NVIDIA key." >&2
fi

# MERGE into secrets.env rather than truncating: the Secrets Manager tile owns
# this file too (it rewrites it wholesale), so a truncating write here would
# silently destroy keys the learner already set.
{
  # if/fi, not `[ … ] && printf`: with a key absent, a false guard as the
  # group's last command fails the whole pipeline under pipefail and set -e
  # kills the script right after the write — no verify, no message.
  if [ -n "$KEY" ];       then printf 'NVIDIA_API_KEY=%s\n' "$KEY"; fi
  if [ -n "$TAVILY" ];    then printf 'TAVILY_API_KEY=%s\n' "$TAVILY"; fi
  if [ -n "$LANGSMITH" ]; then printf 'LANGSMITH_API_KEY=%s\n' "$LANGSMITH"; fi
} | docker exec -i "$C" python3 -c '
import os, sys
dest = sys.argv[1]
new, order, vals = {}, [], {}
for line in sys.stdin:
    line = line.strip()
    if "=" in line:
        k, v = line.split("=", 1)
        new[k] = v
if os.path.exists(dest):
    with open(dest) as f:
        for line in f:
            line = line.rstrip("\n")
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if k not in vals:
                    order.append(k)
                vals[k] = v
for k in new:
    if k not in vals:
        order.append(k)
vals.update(new)
os.umask(0o077)
tmp = dest + ".tmp"
with open(tmp, "w") as f:
    for k in order:
        f.write("%s=%s\n" % (k, vals[k]))
os.replace(tmp, dest)
os.chmod(dest, 0o600)
' "$DEST"
docker exec "$C" chown sandbox:sandbox "$DEST"

# Verify by NAME only — never read values back.
echo "Staged into $DEST in $C (mode 600, owner sandbox). Keys now present:"
docker exec "$C" sh -c "sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/  \1/p' '$DEST'"
echo
echo "NOTE: if JupyterLab is already running, a key staged HERE is invisible to"
echo "      existing kernels — start-jupyter.sh captures secrets.env into the server"
echo "      env at launch. Re-run start-jupyter.sh (token/URL survive) so kernels see"
echo "      it. Keys set via the Secrets Manager tile need NO restart, provided the"
echo "      variable was absent from the server env at launch."
