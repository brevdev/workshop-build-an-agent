"""Find exercise blanks you have not filled in yet.

    python code/workshop_support/blanks.py            # every module
    python code/workshop_support/blanks.py 2          # one module
    python code/workshop_support/blanks.py path.py    # specific files

Recognizes the workshop's placeholder styles: `...` in code (including `{...}`
inside f-strings), a `" ... "` string, a `TODO: ...` line inside a prompt
template, and `raise NotImplementedError("Complete Exercise ...")`. It reads
files only; it never runs your code. Exits 1 while blanks remain.
"""

import ast
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
EXERCISES = {
    1: ["code/1-build-an-agent/intro_to_agents.ipynb", "code/1-build-an-agent/docgen_client.ipynb"],
    2: ["code/2-agentic-rag/rag_agent.py"],
    3: ["code/3-agent-evaluation/evaluation_framework.py", "code/3-agent-evaluation/evaluate_rag_agent.ipynb",
        "code/3-agent-evaluation/evaluate_report_agent.ipynb"],
    4: ["code/4-agent-customization/bash_agent.ipynb", "code/4-agent-customization/01_synthetic_data_generation.ipynb",
        "code/4-agent-customization/02_grpo_training.ipynb", "code/4-agent-customization/03_run_agent.ipynb"],
    5: ["code/5-deep-agents/deep_agent.py"],
    6: ["code/6-agent-safety/agent_safety.py", "code/6-agent-safety/safety_eval_framework.py"],
    7: ["code/7-agent-harnesses/harness_lab.py", "code/7-agent-harnesses/harness_lab.ipynb"],  # two tracks of one lab
}
TODO_LINE = re.compile(r"^\s*TODO:\s*\.\.\.\s*$")
# Notebook-only syntax (magics, shell escapes, help) is not Python.
NOTEBOOK_ONLY = re.compile(r"^\s*(%|!|\?)")


def _code_blanks(source: str) -> set[int]:
    """Return 1-based line numbers of placeholders in one Python source."""
    lines = source.splitlines()
    found = {number for number, line in enumerate(lines, 1) if TODO_LINE.match(line)}
    try:
        tree = compile(source, "<exercise>", "exec", flags=ast.PyCF_ONLY_AST | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    except SyntaxError:
        # Fall back to the visible text so a half-edited file still reports.
        return found | {number for number, line in enumerate(lines, 1)
                        if re.search(r"(?<![\w.\"'])\.\.\.(?![\w.])", line)}
    # `...` has real meanings too: Tuple[int, ...], Callable[..., str], and
    # pydantic's required-field marker Field(...).
    legitimate = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            legitimate.update(id(child) for child in ast.walk(node.slice))
        elif isinstance(node, ast.Call) and node.args and getattr(node.func, "id", getattr(node.func, "attr", "")) == "Field":
            legitimate.add(id(node.args[0]))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and id(node) not in legitimate:
            # A placeholder string is padded (" ... "); "..." alone is ordinary text.
            if node.value is Ellipsis or (isinstance(node.value, str) and re.fullmatch(r"\s+\.\.\.\s+", node.value)):
                found.add(node.lineno)
        elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            func, args = node.exc.func, node.exc.args
            if (isinstance(func, ast.Name) and func.id == "NotImplementedError" and args
                    and isinstance(args[0], ast.Constant) and str(args[0].value).startswith("Complete Exercise")):
                found.add(node.lineno)
    return found


def find_blanks(path: Path) -> list[tuple[str, int, str]]:
    """Return (location, line number, line text) for each remaining blank in a .py or .ipynb file."""
    path = Path(path)
    results = []
    if path.suffix == ".ipynb":
        cells = json.loads(path.read_text())["cells"]
        code_cells = [cell for cell in cells if cell["cell_type"] == "code"]
        for index, cell in enumerate(code_cells, 1):
            source = "".join(cell["source"])
            python = "\n".join("pass" if NOTEBOOK_ONLY.match(line) else line for line in source.splitlines())
            lines = source.splitlines()
            for number in sorted(_code_blanks(python)):
                results.append((f"code cell {index}", number, lines[number - 1].strip()))
    else:
        source = path.read_text()
        lines = source.splitlines()
        results = [("", number, lines[number - 1].strip()) for number in sorted(_code_blanks(source))]
    return results


def main(argv: list[str]) -> int:
    if argv and all(arg.isdigit() for arg in argv):
        targets = [(int(arg), ROOT / name) for arg in argv for name in EXERCISES.get(int(arg), [])]
        if not targets:
            print("Modules are numbered 1 to 7.")
            return 2
    elif argv:
        targets = [(None, Path(arg)) for arg in argv]
    else:
        targets = [(module, ROOT / name) for module, names in EXERCISES.items() for name in names]
    remaining = 0
    for module, path in targets:
        if not path.exists():
            print(f"Not found: {path}")
            remaining += 1
            continue
        blanks = find_blanks(path)
        remaining += len(blanks)
        label = f"Module {module}: " if module else ""
        shown = path.resolve().relative_to(ROOT) if path.resolve().is_relative_to(ROOT) else path
        if not blanks:
            print(f"✓ {label}{shown}: no blanks left")
            continue
        print(f"• {label}{shown}: {len(blanks)} blank(s) left")
        for location, number, text in blanks:
            where = f"{location}, line {number}" if location else f"line {number}"
            print(f"    {where}: {text}")
    return 1 if remaining else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
