"""Install NemoClaw the way a learner does, then check it.

Types `yes` at the license notice and presses Enter at every other prompt, as the
setup lesson says. With --interrupt, it presses Ctrl+C at the first
"Apply this configuration?" prompt and checks that rerunning the installer
resumes onboarding. Needs Docker and the saved NVIDIA key; takes 5-15 minutes.

    python tests/e2e/nemoclaw_install.py [--interrupt]
    python tests/e2e/nemoclaw_install.py --uninstall     # remove it again afterwards
"""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

import pexpect

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "code/6-agent-safety/scripts"
sys.path.insert(0, str(ROOT / "code"))
from workshop_support import load_secrets  # noqa: E402

# Prompts a learner answers with Enter; anything in FAILURES ends the run.
PROMPTS = [r"continue \[no\]:", r"Choose \[\d+\]:", r"Choose model \[\d+\]:", r"\[Y/n\]:", r"\[y/N\]:",
           r"Press 1-\d+ to toggle", r"Select tier", r"Include presets", r"\[R/f\]:", r"Sandbox name \("]
FAILURES = [r"Invalid resource profile selection", r"Cannot resume non-interactive onboard"]


def environment():
    load_secrets()
    home = Path.home()
    return {**os.environ, "PATH": f"{home}/.local/bin:{home}/.npm-global/bin:{os.environ['PATH']}"}


def install(interrupt=False):
    """Run the installer once; return its exit status."""
    child = pexpect.spawn("bash", [str(SCRIPTS / "install-nemoclaw.sh")], cwd=str(ROOT), env=environment(),
                          encoding="utf-8", timeout=1800, dimensions=(50, 160))
    child.logfile_read = sys.stdout
    while True:
        index = child.expect(PROMPTS + FAILURES + [pexpect.EOF])
        if index == len(PROMPTS) + len(FAILURES):
            break
        if index >= len(PROMPTS):
            child.close(force=True)
            raise SystemExit(f"\nFAIL: the installer showed {child.after!r}")
        if index == 0:
            child.sendline("yes")
        elif interrupt and re.search(r"\[Y/n\]:", child.after):
            child.sendcontrol("c")
            interrupt = False
        else:
            child.send("\r")
    child.close()
    return child.exitstatus


def check():
    env = environment()
    health = subprocess.run(["bash", str(SCRIPTS / "nemoclaw-health.sh")], capture_output=True, text=True, env=env)
    print(health.stdout)
    assert "[FAIL]" not in health.stdout, "The health check found a broken layer."
    agent = subprocess.run([sys.executable, str(SCRIPTS / "check-nemoclaw-agent.py")], capture_output=True,
                           text=True, env=env, timeout=1200)
    print(agent.stdout, agent.stderr)
    assert "READY" in agent.stdout, "The agent check did not report READY."


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--interrupt", action="store_true", help="interrupt onboarding once, then resume")
    parser.add_argument("--uninstall", action="store_true", help="run uninstall-nemoclaw.sh --yes and exit")
    args = parser.parse_args()
    if args.uninstall:
        return subprocess.run(["bash", str(SCRIPTS / "uninstall-nemoclaw.sh"), "--yes"], env=environment()).returncode
    status = install(interrupt=args.interrupt)
    if args.interrupt:
        assert status != 0, "The interrupted install should not report success."
        print("\n--- Rerunning after the interruption; it should resume ---")
        status = install()
    assert status == 0, f"The installer exited with {status}."
    check()
    print("\nPASS: installed with default answers" + (" after an interrupted run" if args.interrupt else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
