"""Release checks that need no GPU, keys or network: run with `python -m pytest tests`.

They catch drift between the exercises, answer keys, lessons and tutor skills,
and run every module's own test suite. The end-to-end runner
(tests/e2e/run_e2e.py) covers the live, hosted-model parts.
"""

import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from workshop_support.blanks import EXERCISES, find_blanks  # noqa: E402

ANSWER_KEYS = {
    1: [],  # Module 1's solutions are the notebooks' own "NEED SOME HELP" cells.
    2: ["code/2-agentic-rag/rag_agent.answers.py"],
    3: ["code/3-agent-evaluation/evaluation_framework.answers.py", "code/3-agent-evaluation/evaluate_rag_agent.answers.ipynb",
        "code/3-agent-evaluation/evaluate_report_agent.answers.ipynb"],
    4: sorted(str(p.relative_to(ROOT)) for p in (ROOT / "code/4-agent-customization/answer_key").glob("*.ipynb")),
    5: ["code/5-deep-agents/deep_agent.answers.py"],
    6: ["code/6-agent-safety/agent_safety.answers.py", "code/6-agent-safety/safety_eval_framework.answers.py"],
    7: ["code/7-agent-harnesses/harness_lab.answers.py"],
}
MODULE_TESTS = sorted({p.parent for p in ROOT.glob("code/*/tests/test_*.py")})


def source_text(path):
    path = ROOT / path
    if path.suffix == ".ipynb":
        return "\n".join("".join(cell["source"]) for cell in json.loads(path.read_text())["cells"])
    return path.read_text()


@pytest.mark.parametrize("module", sorted(EXERCISES))
def test_every_exercise_still_has_its_blanks(module):
    for name in EXERCISES[module]:
        assert find_blanks(ROOT / name), f"{name} has no blanks left; was a solution committed?"


@pytest.mark.parametrize("path", [p for paths in ANSWER_KEYS.values() for p in paths])
def test_answer_keys_have_no_blanks(path):
    assert not find_blanks(ROOT / path), f"{path} still has placeholders"


def module1_solutions():
    """Module 1 solutions: the code in each notebook's "NEED SOME HELP" cells."""
    text = []
    for name in EXERCISES[1]:
        for cell in json.loads((ROOT / name).read_text())["cells"]:
            source = "".join(cell["source"])
            if "NEED SOME HELP" in source:
                text += re.findall(r"```python\n(.*?)```", source, re.S)
    return "\n".join(text)


def normalize(code):
    """Compare code by its tokens: drop comments, whitespace and trailing commas."""
    code = re.sub(r"(?m)#(?![^\n]*[\"']\s*[,)]).*$", "", code)
    code = re.sub(r"\s+", "", code)
    return re.sub(r",([)\]}])", r"\1", code)


def looks_like_code(span):
    import ast
    candidate = span.replace("…", "...").strip()
    for text in (candidate, candidate + "\n    pass"):
        try:
            ast.parse(text)
            return bool(re.search(r"[(=\[]", candidate))
        except SyntaxError:
            continue
    return False


def code_targets(module):
    """Code spans on the tutor's **Target:** lines for one module."""
    text = (ROOT / f".claude/skills/module-{module}/references/exercises.md").read_text()
    targets = []
    for line in text.splitlines():
        if "**Target:**" in line:
            line = line.split(". (")[0]  # a trailing "(... also works)" note is not the target
            targets += [span.replace("…", "...") for span in re.findall(r"`([^`]+)`", line) if looks_like_code(span)]
    return targets


@pytest.mark.parametrize("module", sorted(ANSWER_KEYS))
def test_tutor_targets_match_the_answer_keys(module):
    """Each code Target must appear in the answer key (whitespace-insensitive; `...` matches anything)."""
    keys = module1_solutions() if module == 1 else "\n".join(source_text(p) for p in ANSWER_KEYS[module])
    # Steps whose solution lives in the lesson page, such as Module 2's local-NIM change.
    keys += "\n".join(re.findall(r"```python\n(.*?)```", "".join(
        p.read_text() for p in sorted(ROOT.glob(f".devx/{module}-*/*.md"))), re.S))
    keys = normalize(keys)
    missing = []
    for target in code_targets(module):
        pattern = ".*?".join(re.escape(normalize(part)) for part in target.split("..."))
        if not re.search(pattern, keys, re.S):
            missing.append(target)
    assert not missing, f"Module {module} Targets not found in its answer key: {missing}"


def test_codex_skills_are_in_sync():
    result = subprocess.run(["bash", ".agents/sync-codex-skills.sh", "--check"], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


LESSONS = sorted(ROOT.glob(".devx/*/*.md"))


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_lesson_file_links_and_code_selectors_resolve(lesson):
    text, problems = lesson.read_text(), []
    # openOrCreate... creates a missing file by design; generated (ignored) files appear later.
    for path in re.findall(r"openExistingFileInJupyterLab\('([^']+)'\)", text):
        ignored = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode == 0
        if not path.startswith(("~", "/")) and not (ROOT / path).exists() and not ignored:
            problems.append(f"missing file {path}")
    for path, selector in re.findall(r"goToLineAndSelect\('([^']+)',\s*'([^']*)'\)", text):
        if not (ROOT / path).exists():
            problems.append(f"missing file {path}")
        elif selector not in source_text(path):
            problems.append(f"{path} has no text {selector!r}")
    assert not problems, problems


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_lesson_images_exist(lesson):
    text = lesson.read_text()
    paths = re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", text) + re.findall(r'<img src="([^"]+)"', text)
    missing = [p for p in paths if not p.startswith(("http", "data:")) and not (lesson.parent / p).exists()]
    assert not missing, missing


@pytest.mark.parametrize("path", [
    "code/4-agent-customization/outputs/grpo_langgraph_cli/merged_model/model.safetensors",
    "code/4-agent-customization/unsloth_compiled_cache/UnslothGRPOTrainer.py",
    "code/4-agent-customization/data/langgraph_cli/generated/train.jsonl",
    "code/3-agent-evaluation/runs/rag-1/results.json",
    "data/evaluation/synthetic_rag_agent_test_cases.json",
    "code/3-agent-evaluation/artifacts/rag_agent_test_cases/parquet-files/batch_00000.parquet",
    "secrets.env",
])
def test_workshop_outputs_and_secrets_are_ignored(path):
    assert subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode == 0, f"{path} is not ignored"


@pytest.mark.parametrize("tests", MODULE_TESTS, ids=lambda p: p.parent.name)
def test_module_test_suite(tests):
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
                            cwd=tests.parent, capture_output=True, text=True, timeout=900)
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-2000:]
