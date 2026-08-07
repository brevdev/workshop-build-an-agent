"""Build harness_lab.ipynb / harness_lab.answers.ipynb from the .py sources.

Keeps the notebook and script versions mirrored: the .py files are the source
of truth; rerun this after editing them.

The exercise notebook's hand-authored "💡 NEED SOME HELP?" cells (id `help-ex*`)
are PRESERVED across regenerations: they're read back from the existing
harness_lab.ipynb and re-inserted after the same generated cell they followed.
Keep those cells in the committed notebook — that's where their content lives.
"""

import json
import re
from pathlib import Path

LAB_DIR = Path(__file__).parent.parent

SECTION_TITLES = {
    1: "Exercise 1 — Build the Minimal Harness",
    2: "Exercise 2 — Measure the Context Tax",
    3: "Exercise 3 — Author a Portable Skill",
    4: "Exercise 4 — Verified NVIDIA Skill, Real GPU",
    5: "Exercise 5 — The Self-Evolving Harness",
}

SECTION_BLURBS = {
    1: "pi proves a complete harness needs surprisingly little: a short system "
       "prompt, four tools, and a loop. Build exactly that around Nemotron.",
    2: "Count what your harness pays per turn — prompt plus tool schemas — "
       "against a maximal configuration, then implement lazy skill loading.",
    3: "Write `skills/dataset_profiler/SKILL.md` (format: `skills/code_review/SKILL.md` "
       "at the repo root), then run it through the lazy loader. The same folder also "
       "drops unchanged into Hermes's `~/.hermes/skills/` — one skill, two harnesses.",
    4: "Install and signature-verify the NVIDIA `accelerated-computing-cudf` skill:\n\n"
       "```bash\nbash scripts/install_nvidia_skill.sh accelerated-computing-cudf\n```\n\n"
       "Then open a terminal, keep `watch -n 0.5 nvidia-smi` visible, and run the next "
       "cell — you'll see your GPU light up while the agent works.",
    5: "The pi finale: after finishing a task, the agent reviews its own transcript, "
       "writes a new SKILL.md, and uses it on the next run.",
}

RUN_CELLS = {
    1: 'run = build_bare_agent()\nprint(run(\n    "Create a file named harness_hello.txt containing the words "\n    "\'minimal harness\', then read it back and confirm its contents."\n))',
    2: "measure_context_tax()\n_ = load_skills_lazily()",
    3: 'ensure_test_data()\nprint(run_with_skills(\n    f"Profile the dataset at {TEST_DATA} and report your findings."\n))',
    4: "print(run_gpu_task())",
    5: "run_self_evolution_demo()",
}

# Exercise-notebook-only intro paragraph (the answers notebook omits it).
EXERCISE_INTRO_EXTRA = (
    "This notebook is the self-contained track: every `# TODO: Exercise …` blank has a "
    "collapsible **💡 NEED SOME HELP?** solution right below its cell — try each blank "
    "yourself before peeking. (The guided pages follow `harness_lab.py` instead; the two "
    "mirror each other, so pick one and stick with it. Full answer key: `harness_lab.answers.ipynb`.)"
)


def cells_from_py(py_path: Path):
    source = py_path.read_text()
    # Drop the CLI entrypoint — notebooks use per-exercise run cells instead.
    source = source.split("# " + "-" * 75 + "\n\ndef main():")[0]
    banner = re.compile(r"# -{20,}\n(# Exercise \d.*?\n(?:#.*\n)*)# -{20,}\n")

    docstring = re.match(r'"""(.*?)"""', source, re.DOTALL).group(1).strip()
    title = "Module 7 Lab — Agent Harnesses & Skills"
    answers = ".answers" in py_path.name

    intro_extra = f"\n\n{EXERCISE_INTRO_EXTRA}" if not answers else ""
    cells = [md(f"# {title}{' (Answers)' if answers else ''}\n\n"
               "Complete the exercises in order. Docs: open the **7. Agent Harnesses** "
               f"launcher for the guided walkthrough.{intro_extra}\n\n"
               "> Needs `NVIDIA_API_KEY` — set it once with the Secrets Manager; "
               "the setup cell below loads it from `secrets.env`.")]

    chunks = banner.split(source)
    # chunks[0] = header+imports+tools+ex1, then alternating (banner_text, body)
    setup, *rest = chunks
    setup_code, ex1_code = setup.split("def build_bare_agent", 1)
    setup_code = re.sub(r'^""".*?"""\n*', "", setup_code, flags=re.DOTALL)
    cells.append(md("## Setup — secrets, test data, and the four pi-style core tools"))
    cells.append(code(setup_code.strip()))
    cells.append(md(f"## {SECTION_TITLES[1]}\n\n{SECTION_BLURBS[1]}"))
    cells.append(code(("def build_bare_agent" + ex1_code).strip()))
    cells.append(code(RUN_CELLS[1]))

    for i, n in zip(range(0, len(rest), 2), (2, 3, 4, 5)):
        body = rest[i + 1].strip()
        cells.append(md(f"## {SECTION_TITLES[n]}\n\n{SECTION_BLURBS[n]}"))
        if body:
            cells.append(code(body))
        cells.append(code(RUN_CELLS[n]))

    return cells


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": text.splitlines(keepends=True)}


def build(py_name, ipynb_name):
    out = LAB_DIR / ipynb_name

    # Preserve hand-authored "help-*" cells from an existing notebook: record which
    # generated cell each one followed, so we re-insert it there after regenerating.
    preserved = []
    existing_meta = None
    if out.exists():
        existing = json.loads(out.read_text())
        existing_meta = existing.get("metadata") or None
        prev_id = None
        for c in existing.get("cells", []):
            if str(c.get("id", "")).startswith("help-"):
                preserved.append((prev_id, c))
            prev_id = c.get("id")

    cells = cells_from_py(LAB_DIR / py_name)
    for i, cell in enumerate(cells):
        cell["id"] = f"cell-{i:02d}"  # nbformat 4.5 requires stable cell ids

    if preserved:
        merged = []
        for cell in cells:
            merged.append(cell)
            merged.extend(h for anchor, h in preserved if anchor == cell["id"])
        cells = merged

    # Normalize each cell's key order to match how Jupyter serializes on save, so
    # regenerating produces a minimal diff instead of reshuffling every cell.
    key_order = ["cell_type", "execution_count", "id", "metadata", "outputs", "source"]
    cells = [{k: c[k] for k in key_order if k in c} for c in cells]

    nb = {
        "cells": cells,
        # Preserve the existing notebook's kernel metadata (Jupyter writes a fuller
        # kernelspec/language_info than we need); fall back to a minimal default.
        "metadata": existing_meta or {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    # ensure_ascii=False keeps unicode (—, …, 💡) literal like Jupyter does, and the
    # trailing newline matches Jupyter's save format — both keep regeneration diffs minimal.
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
    print(f"Wrote {out} ({len(nb['cells'])} cells)")


if __name__ == "__main__":
    build("harness_lab.py", "harness_lab.ipynb")
    build("harness_lab.answers.py", "harness_lab.answers.ipynb")
