#!/usr/bin/env python3
"""
NemoClaw Client detection diagnostic.

Run this inside the same environment that launches the NemoClaw Client
(i.e. the Workbench project container) to see what the detection logic
actually observes. Helps narrow down why "Live NemoClaw Agent" isn't the
default mode.

Usage:
    python3 code/6-agent-safety/scripts/diagnose-nemoclaw.py
"""

import os
import subprocess
import sys

# Make the wrapper importable regardless of cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
sys.path.insert(0, _PARENT)

import nemoclaw_wrapper as nw  # noqa: E402


def header(title: str) -> None:
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


header("Environment")
print(f"Python:      {sys.version.split()[0]}")
print(f"Executable:  {sys.executable}")
print(f"Cwd:         {os.getcwd()}")
print(f"User:        {os.environ.get('USER', '<unset>')}")
print(f"Home:        {os.environ.get('HOME', '<unset>')}")
print(f"PATH:        {os.environ.get('PATH', '<unset>')}")

header("Binary discovery")
print(f"Resolved binary: {nw._NEMOCLAW_BIN!r}")
print(f"_check_nemoclaw_cli(): {nw._check_nemoclaw_cli()}")

if not nw._NEMOCLAW_BIN:
    print()
    print("nemoclaw binary not found. Try:")
    print("  which nemoclaw")
    print("  ls -l /usr/local/bin/nemoclaw /usr/bin/nemoclaw ~/.local/bin/nemoclaw")
    sys.exit(1)

header(f"`nemoclaw {nw.SANDBOX_NAME} status` — raw capture")
try:
    result = subprocess.run(
        [nw._NEMOCLAW_BIN, nw.SANDBOX_NAME, "status"],
        capture_output=True,
        text=True,
        timeout=20,
    )
except Exception as e:
    print(f"Subprocess error: {e}")
    sys.exit(2)

print(f"Exit code:   {result.returncode}")
print(f"stdout bytes: {len(result.stdout)}")
print(f"stderr bytes: {len(result.stderr)}")
print()
print("--- stdout ---")
print(result.stdout)
print("--- stderr ---")
print(result.stderr)
print("--- stdout repr (first 400) ---")
print(repr(result.stdout[:400]))

header("Detection outcome")
ready = nw._check_sandbox_running(timeout=20)
print(f"_check_sandbox_running(): {ready}")
print(f"LAST_DETECT_ERROR:        {nw.LAST_DETECT_ERROR!r}")

if ready:
    print()
    print("OK — the NemoClaw Client should default to 'Live NemoClaw Agent'.")
    print("If it doesn't, restart Streamlit to clear @st.cache_resource.")
else:
    print()
    print("Detection failed. Use the stdout/stderr above to diagnose:")
    print("  - If stdout is empty but stderr has content, the status command")
    print("    is sending output to the wrong stream.")
    print("  - If stdout has ANSI escapes (\\x1b[...m bytes in repr), strip them.")
    print("  - If `Phase: Ready` is missing, the sandbox state isn't ready —")
    print("    re-run `bash code/6-agent-safety/scripts/install-nemoclaw.sh`.")
