"""Start a module over: back up your work, restore its exercise files, stop its servers.

    python code/workshop_support/reset.py 2          # shows the plan and asks first
    python code/workshop_support/reset.py 2 --yes

Your current exercise files are copied to ~/workshop-backups/ first, so nothing
is lost. Close the module's notebooks in JupyterLab before resetting; an open
notebook can save its old copy over the restored file. Training outputs,
downloaded models and the Module 6 sandbox are left alone (see each lesson's
cleanup steps).
"""

import os
from datetime import datetime
from pathlib import Path
import shutil
import signal
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workshop_support.blanks import EXERCISES, ROOT

# Command-line fragments of the servers each module's lessons start.
SERVERS = {
    2: ["langgraph dev", "uvicorn mcp_server:app"],
    4: ["uvicorn app:app"],
    5: ["uvicorn server:app"],
}
CONTAINERS = {2: ["nemotron"]}


def matching_processes(fragments):
    """Return (pid, command line) for this user's processes whose command contains a fragment."""
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) in (os.getpid(), os.getppid()):
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").strip()
        except OSError:
            continue
        if any(fragment in command for fragment in fragments) and "reset.py" not in command:
            found.append((int(entry.name), command))
    return found


def main(argv):
    if not argv or not argv[0].isdigit() or int(argv[0]) not in EXERCISES:
        print(__doc__)
        return 2
    module, assume_yes = int(argv[0]), "--yes" in argv[1:]
    files = [ROOT / name for name in EXERCISES[module]]
    # Porcelain lines are "XY path"; keep their leading status columns intact.
    changed = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", *map(str, files)],
                             capture_output=True, text=True).stdout.rstrip("\n")
    processes = matching_processes(SERVERS.get(module, []))
    containers = [name for name in CONTAINERS.get(module, [])
                  if subprocess.run(["docker", "ps", "-aq", "--filter", f"name=^/{name}$"],
                                    capture_output=True, text=True).stdout.strip()]
    print(f"Module {module} reset plan:")
    print("  Restore exercise files:" if changed else "  Exercise files already match the original.")
    for line in changed.splitlines():
        print(f"    {line[3:]}")
    for pid, command in processes:
        print(f"  Stop server (pid {pid}): {command[:100]}")
    for name in containers:
        print(f"  Remove container {name} (its image and model cache are kept)")
    if not (changed or processes or containers):
        print("Nothing to do.")
        return 0
    if not assume_yes:
        try:
            answer = input("Continue? [y/N] ").strip().lower()
        except EOFError:
            answer = ""
        if answer not in ("y", "yes"):
            print("Nothing changed.")
            return 1
    if changed:
        backup = Path.home() / "workshop-backups" / f"{datetime.now():%Y%m%d-%H%M%S}-module-{module}"
        for path in files:
            if path.exists():
                target = backup / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        subprocess.run(["git", "-C", str(ROOT), "checkout", "HEAD", "--", *map(str, files)], check=True)
        print(f"Restored the exercise files. Your previous versions are in {backup}")
        print("If a restored notebook is open in JupyterLab, use File > Reload Notebook from Disk.")
    for pid, _ in processes:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    if processes:
        print(f"Stopped {len(processes)} server process(es). Restart them from the lesson when you need them.")
    for name in containers:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        print(f"Removed container {name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
