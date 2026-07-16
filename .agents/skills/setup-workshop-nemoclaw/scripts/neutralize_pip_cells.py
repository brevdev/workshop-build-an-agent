#!/usr/bin/env python3
"""neutralize_pip_cells.py — comment out the blocking `%pip install -r
../../requirements.txt` cell in every secrets_management_*.ipynb.

Why: that cell tries to install torch/cudf/unsloth (GPU deps) at kernel start.
In the sandbox those installs hang forever, so voila never finishes rendering
("Running…"). Deps are already pre-installed via uv, so the cell is redundant.
We preserve everything else in the cell (notably any load_dotenv() calls).

Idempotent: skips cells already neutralized.
Usage: python neutralize_pip_cells.py /sandbox/workshop-build-an-agent
"""
import json, sys, glob, os

REPO = sys.argv[1] if len(sys.argv) > 1 else "/sandbox/workshop-build-an-agent"
MARKER = "# [sandbox] pip install of requirements.txt skipped"
NOTE = (MARKER +
        " \u2014 deps pre-installed via uv; installing torch/cudf/unsloth here hangs voila\n")

# Only touch the real notebooks, never the .ipynb_checkpoints copies.
pattern = os.path.join(REPO, "code", "secrets_management", "secrets_management_*.ipynb")
changed = 0
for path in sorted(glob.glob(pattern)):
    if ".ipynb_checkpoints" in path:
        continue
    with open(path) as f:
        nb = json.load(f)
    dirty = False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", [])
        joined = "".join(src)
        if MARKER in joined:
            continue  # already neutralized
        if "%pip install" in joined and "requirements.txt" in joined:
            new_src = []
            for line in src:
                if line.lstrip().startswith("%pip install") and "requirements.txt" in line:
                    new_src.append(NOTE)
                else:
                    new_src.append(line)
            cell["source"] = new_src
            dirty = True
    if dirty:
        with open(path, "w") as f:
            json.dump(nb, f, indent=1)
            f.write("\n")
        changed += 1
        print(f"neutralized: {path}")

print(f"done: {changed} notebook(s) modified")
