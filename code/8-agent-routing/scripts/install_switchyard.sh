#!/bin/bash
# THE single pin record for Module 8's Switchyard stack (spec §8b.2/§8b.7).
# Bump pins ONLY via the runbook in code/8-agent-routing/README.md.
#
# Idempotent: re-running is a no-op once the pinned version is importable.
#
# Verified facts behind this script (full evidence: docs/specs/switchyard-api-notes.md):
#   * `nemo-switchyard` ships prebuilt cp312-abi3 wheels for linux aarch64 AND x86_64;
#     no compiler, no cargo, no Rust toolchain is needed.
#   * There is NO standalone `switchyard-server` binary to fetch: the GitHub releases
#     carry source tarballs only, and the crates.io `switchyard-server` crate would mean
#     a full `cargo install --locked` release build. We deliberately do neither --
#     the same Rust gateway is embedded in the wheel and reachable from Python as
#     `switchyard_rust.server.Server("routes.toml", port=4000)`.
#   * The published wheel requires Python >= 3.12 (the upstream README's `--python 3.10`
#     does not resolve).
#
# Usage:
#   bash install_switchyard.sh                 # install / verify
#   bash install_switchyard.sh --print-python  # same, but print ONLY the interpreter path
#
# Override the fallback venv location with SWITCHYARD_VENV=/some/path.

set -euo pipefail

# ---------------------------------------------------------------- pins ----
SWITCHYARD_PIP_PIN="nemo-switchyard[cli]==0.2.0"
SWITCHYARD_VERSION="0.2.0"
SWITCHYARD_MIN_PY="3.12"

# sha256 of every published 0.2.0 wheel (PyPI, uploaded 2026-08-10). The one matching
# this machine's wheel tag is verified before install; the rest are the audit record.
SHA256_manylinux_aarch64="18ec104d044161a15979f562cfdc4a132543e882d051ed80d052219d78333378"
SHA256_manylinux_x86_64="5691b5df6573ac21a2f2fb76050d957e99340536b0536a1c85278892a5808e76"
SHA256_macosx_arm64="46afd9b3df91cdc91b8544572cf3ec7106a0d5c75a785ee0677f0e45ac2461f1"
SHA256_macosx_x86_64="746d4307011a29e1b0a8126b3e615cea2d1c1493dbd0c5fcf36db4538c737203"
SHA256_win_amd64="4641d19c6e7fd6d64d05bd8354f409e9f6a80a1472f7f0518a5ecc9c4347dbb1"
SHA256_win_arm64="5ea9e65a751da540e7231d39f28ecf66af06e90ffccec36a05ca755875430c05"
SHA256_sdist="da76a59ea88563d12828a439ae51475b4ffef2f231a6f44bde47eb2eda5e3648"

# Hosted model ids the lab routes between (single-source; see also routes.toml).
# Recorded here so a pin bump and a model-id drift are reviewed in the same place.
MODEL_EFFICIENT="nvidia/nemotron-3.5-lightning-30b-a3b"
MODEL_CAPABLE="nvidia/nemotron-3-super-120b-a12b"
MODEL_JUDGE="nvidia/nemotron-3-nano-30b-a3b"
# ---------------------------------------------------------------------------

PRINT_ONLY=0
if [ "${1:-}" = "--print-python" ]; then
    PRINT_ONLY=1
    # Keep the real stdout on fd 3 and send everything else to stderr, so the only
    # thing on stdout is the interpreter path -- safe to capture with $(...) even on
    # a cold box where this call has to do the whole install.
    exec 3>&1 1>&2
fi

SWITCHYARD_VENV="${SWITCHYARD_VENV:-$HOME/.local/share/module8-switchyard-venv}"

say() { [ "$PRINT_ONLY" -eq 1 ] || echo "$@"; }

# Does $1 (a python interpreter) already have the pinned version importable?
has_pin() {
    "$1" -c "
import sys, switchyard, switchyard_rust.server
sys.exit(0 if switchyard.__version__ == '${SWITCHYARD_VERSION}' else 1)
" >/dev/null 2>&1
}

# Is $1 a python >= SWITCHYARD_MIN_PY?
py_ok() {
    "$1" -c "
import sys
need = tuple(int(p) for p in '${SWITCHYARD_MIN_PY}'.split('.'))
sys.exit(0 if sys.version_info[:len(need)] >= need else 1)
" >/dev/null 2>&1
}

# ------------------------------------------------- pick an interpreter ----
# Prefer one that already satisfies the pin (idempotency), then the ambient
# python, then a dedicated venv we own.
PY=""
for cand in "$SWITCHYARD_VENV/bin/python" python3.12 python3 python; do
    command -v "$cand" >/dev/null 2>&1 || [ -x "$cand" ] || continue
    if has_pin "$cand"; then PY="$cand"; break; fi
done

if [ -n "$PY" ]; then
    say "==> nemo-switchyard ${SWITCHYARD_VERSION} already present (${PY}) — nothing to do."
else
    for cand in python3.12 python3 python; do
        command -v "$cand" >/dev/null 2>&1 || continue
        if py_ok "$cand"; then PY="$cand"; break; fi
    done
    if [ -z "$PY" ]; then
        echo "ERROR: no Python >= ${SWITCHYARD_MIN_PY} found." >&2
        echo "       nemo-switchyard ${SWITCHYARD_VERSION} publishes cp312-abi3 wheels only." >&2
        exit 1
    fi
    say "==> Using $($PY -c 'import sys,platform; print(sys.executable, platform.machine())')"

    # ------------------------------------ download + verify sha256 --------
    TMPDIR_DL="$(mktemp -d)"
    trap 'rm -rf "$TMPDIR_DL"' EXIT

    say "==> Downloading ${SWITCHYARD_PIP_PIN} wheel (no deps) for checksum verification..."
    "$PY" -m pip download --quiet --no-deps --only-binary=:all: \
        "nemo-switchyard==${SWITCHYARD_VERSION}" -d "$TMPDIR_DL"

    WHEEL="$(ls "$TMPDIR_DL"/nemo_switchyard-*.whl 2>/dev/null | head -1)"
    if [ -z "$WHEEL" ]; then
        echo "ERROR: pip produced no wheel for nemo-switchyard==${SWITCHYARD_VERSION}." >&2
        echo "       There is no source-build fallback (the package is a maturin/Rust extension)." >&2
        exit 1
    fi

    case "$(basename "$WHEEL")" in
        *manylinux*aarch64*)     EXPECTED="$SHA256_manylinux_aarch64" ;;
        *manylinux*x86_64*)      EXPECTED="$SHA256_manylinux_x86_64" ;;
        *macosx*arm64*)          EXPECTED="$SHA256_macosx_arm64" ;;
        *macosx*x86_64*)         EXPECTED="$SHA256_macosx_x86_64" ;;
        *win_amd64*)             EXPECTED="$SHA256_win_amd64" ;;
        *win_arm64*)             EXPECTED="$SHA256_win_arm64" ;;
        *)
            echo "ERROR: unrecognised wheel '$(basename "$WHEEL")' — no pinned sha256 on record." >&2
            echo "       Add it to this script (and to docs/specs/switchyard-api-notes.md) before trusting it." >&2
            exit 1 ;;
    esac

    say "==> Verifying sha256 of $(basename "$WHEEL")..."
    echo "${EXPECTED}  ${WHEEL}" | sha256sum -c - >/dev/null
    say "    ✅ sha256 matches the pin record."

    # --------------------------------------------------- install ----------
    # `pip install "<wheel>[cli]"` installs the verified artifact and resolves the
    # cli extra (prompt-toolkit) plus runtime deps from the index.
    if "$PY" -m pip install --quiet "${WHEEL}[cli]" 2>/dev/null; then
        say "==> Installed into the ambient environment."
    else
        say "==> Ambient environment is not writable (PEP 668 / externally managed)."
        say "    Falling back to a dedicated venv: ${SWITCHYARD_VENV}"
        [ -x "$SWITCHYARD_VENV/bin/python" ] || "$PY" -m venv "$SWITCHYARD_VENV"
        PY="$SWITCHYARD_VENV/bin/python"
        "$PY" -m pip install --quiet --upgrade pip
        "$PY" -m pip install --quiet "${WHEEL}[cli]"
    fi
fi

# ------------------------------------------------------------ verify ----
VERSION="$("$PY" -c 'import switchyard; print(switchyard.__version__)')"
if [ "$VERSION" != "$SWITCHYARD_VERSION" ]; then
    echo "ERROR: expected nemo-switchyard ${SWITCHYARD_VERSION}, got ${VERSION}." >&2
    exit 1
fi
# The embedded Rust gateway is the module's server (there is no separate binary).
"$PY" -c 'from switchyard_rust.server import Server' >/dev/null
# The in-process router used by Exercise 3 / the shim.
"$PY" -c 'from switchyard.libsy import LlmTarget, TaskClassifierConfig, algorithms' >/dev/null

# Always hand back an absolute path -- $PY may still be a bare name like `python3.12`.
PY="$("$PY" -c 'import sys; print(sys.executable)')"

if [ "$PRINT_ONLY" -eq 1 ]; then
    echo "$PY" >&3
    exit 0
fi

echo "✅ nemo-switchyard ${VERSION} ready"
echo "   interpreter        : ${PY}"
echo "   in-process router  : switchyard.libsy (LlmTarget / algorithms.*)"
echo "   embedded gateway   : switchyard_rust.server.Server('routes.toml', port=4000)"
echo "   model pool         : ${MODEL_EFFICIENT} (efficient) | ${MODEL_CAPABLE} (capable) | ${MODEL_JUDGE} (judge)"
