"""E2E plumbing test for harness_lab.answers.py with a scripted mock model.

Verifies — without an NVIDIA_API_KEY — that:
  Ex1: build_bare_agent loop executes tool calls and terminates
  Ex2: context tax + lazy loading produce sane numbers
  Ex3: an authored skill is indexed and loadable through load_skill
  Ex5: self_evolve_skill validates + saves a model-authored skill, and the
       lazy loader picks it up on the next pass
  Ex4 plumbing: run_gpu_task degrades cleanly when the skill is missing

Run:  .venv/bin/python scripts/e2e_mock_test.py
"""

import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import AIMessage


def fail(msg):
    print(f"❌ FAIL: {msg}")
    sys.exit(1)


# import the answers module under its real filename
import importlib.util

spec = importlib.util.spec_from_file_location(
    "answers", Path(__file__).parent.parent / "harness_lab.answers.py"
)
answers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(answers)


class MockModel:
    """Stands in for ChatNVIDIA: plays a scripted conversation."""

    def __init__(self, script):
        self.script = list(script)

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        if not self.script:
            return AIMessage(content="done")
        step = self.script.pop(0)
        if isinstance(step, str):
            return AIMessage(content=step)
        return AIMessage(content="", tool_calls=step)


def run_test():
    workdir = Path(tempfile.mkdtemp(prefix="m7e2e_"))
    target = workdir / "hello.txt"

    # ---- Ex1: agent loop executes tools and terminates ----------------------
    script = [
        [{"name": "write_file", "args": {"path": str(target), "content": "minimal harness"}, "id": "c1"}],
        [{"name": "read_file", "args": {"path": str(target)}, "id": "c2"}],
        "Done - file created and verified: minimal harness",
    ]
    with patch.object(answers, "ChatNVIDIA", lambda **kw: MockModel(script)):
        run = answers.build_bare_agent()
        out = run("create hello.txt containing minimal harness, then verify it")
    if "Done" not in out:
        fail(f"Ex1 loop did not reach final answer: {out!r}")
    if target.read_text() != "minimal harness":
        fail("Ex1 write_file tool did not actually write the file")
    print("✅ Ex1: agent loop wires tools and terminates (2 tool turns + answer)")

    # ---- Ex2: context tax + lazy loading -----------------------------------
    tax = answers.measure_context_tax()
    if not (0 < tax["minimal"] < 1500 and tax["maximal"] > tax["minimal"] * 4):
        fail(f"Ex2 tax numbers implausible: {tax}")
    skills_dir = workdir / "skills"
    (skills_dir / "demo_skill").mkdir(parents=True)
    (skills_dir / "demo_skill" / "SKILL.md").write_text(
        "---\nname: demo_skill\ndescription: A demo skill for testing\n---\n\n# Demo\n\nBody here.\n"
    )
    index_text, load_skill = answers.load_skills_lazily(skills_dir)
    if "demo_skill" not in index_text:
        fail("Ex2 lazy index missing authored skill")
    body = load_skill.invoke({"name": "demo_skill"})
    if "Body here." not in body:
        fail("Ex2 load_skill did not return the full body")
    print("✅ Ex2: tax measured, lazy index 1-line/skill, on-demand body load works")

    # ---- Ex3: example dataset_profiler skill loads --------------------------
    example = Path(answers.SKILLS_DIR) / ".examples" / "dataset_profiler" / "SKILL.md"
    meta = answers.parse_frontmatter(example.read_text())
    if meta["name"] != "dataset_profiler":
        fail("Ex3 example skill frontmatter broken")
    print("✅ Ex3: example skill parses; format matches the loader contract")

    # ---- Ex5: self-evolution round trip -------------------------------------
    fake_skill = (
        "---\nname: null_check_procedure\ndescription: Check a CSV for nulls and duplicates\n---\n\n"
        "# Null Check\n\n1. Load the CSV\n2. df.isna().sum()\n3. df.duplicated().sum()\n4. Report one sentence.\n"
    )
    with patch.object(answers, "ChatNVIDIA", lambda **kw: MockModel([fake_skill])):
        saved = answers.self_evolve_skill("TASK: check nulls\nFINAL ANSWER: none found", skills_dir)
    if not saved.exists():
        fail("Ex5 did not save the authored skill")
    index2, load2 = answers.load_skills_lazily(skills_dir)
    if "null_check_procedure" not in index2:
        fail("Ex5 evolved skill not picked up by lazy loader on next run")
    print("✅ Ex5: agent-authored skill validated, saved, and indexed on next run")

    # ---- Ex5 guard: malformed skill is rejected BEFORE saving ----------------
    with patch.object(answers, "ChatNVIDIA", lambda **kw: MockModel(["no frontmatter at all"])):
        try:
            answers.self_evolve_skill("TASK: x", skills_dir)
            fail("Ex5 accepted a malformed skill (should raise)")
        except ValueError:
            print("✅ Ex5 guard: malformed skill rejected before it can break the loader")

    # ---- Ex4 plumbing: graceful degradation ---------------------------------
    with patch.object(answers, "SKILLS_DIR", workdir / "nope"):
        msg = answers.run_gpu_task()
    if "not installed" not in msg:
        fail(f"Ex4 missing-skill path wrong: {msg!r}")
    print("✅ Ex4: missing-skill path degrades with a clear message")

    shutil.rmtree(workdir)
    print("\nALL MOCK E2E CHECKS PASSED")


if __name__ == "__main__":
    run_test()
