#!/usr/bin/env python3
"""neutralize_pip_cells.py — comment out blocking `%pip install` / `!pip install`
lines in every workshop notebook under code/ (all modules + answer keys).

Why: the uv-created venv has no pip, so those cells print a confusing
"No module named pip" error; and where pip DOES exist (bare-metal), the
root requirements.txt pulls torch/cudf/unsloth (GPU deps) which hang the
sandbox. Everything the notebooks need is pre-installed from
templates/requirements-sandbox.txt, so the cells are redundant here.
We preserve everything else in the cell (notably any load_dotenv() calls).

Idempotent: skips lines already neutralized.
Usage: python neutralize_pip_cells.py /sandbox/workshop-build-an-agent
"""
import glob
import json
import os
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "/sandbox/workshop-build-an-agent"
MARKER = "# [sandbox] pip install skipped"
NOTE = MARKER + " — deps pre-installed via uv (requirements-sandbox.txt); pip is absent from this venv\n"


def is_pip_line(line: str) -> bool:
    s = line.lstrip()
    return (s.startswith("%pip install") or s.startswith("!pip install")) and "pip install" in s


pattern = os.path.join(REPO, "code", "**", "*.ipynb")
changed = 0
for path in sorted(glob.glob(pattern, recursive=True)):
    if ".ipynb_checkpoints" in path or "/.audit-" in path:
        continue
    with open(path) as f:
        nb = json.load(f)
    dirty = False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", [])
        joined = "".join(src)
        if MARKER in joined or "pip install" not in joined:
            continue
        new_src = [NOTE if is_pip_line(line) else line for line in src]
        if new_src != src:
            cell["source"] = new_src
            dirty = True
    if dirty:
        with open(path, "w") as f:
            json.dump(nb, f, indent=1)
            f.write("\n")
        changed += 1
        print(f"neutralized: {path}")

print(f"done: {changed} notebook(s) modified")
