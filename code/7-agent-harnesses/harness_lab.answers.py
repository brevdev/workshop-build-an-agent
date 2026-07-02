"""Module 7 Lab — Agent Harnesses & Skills (ANSWERS).

Five exercises that take apart the harness layer:

  1. Build the minimal harness  (build_bare_agent)
  2. Measure the context tax    (measure_context_tax, load_skills_lazily)
  3. Author a portable skill    (skills/dataset_profiler/SKILL.md)
  4. Verified NVIDIA skill, real GPU (run_gpu_task)
  5. The self-evolving harness  (self_evolve_skill)

Run a single exercise:  python harness_lab.answers.py --exercise 1
"""

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path

import tiktoken
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA

LAB_DIR = Path(__file__).parent
SKILLS_DIR = LAB_DIR / "skills"
TEST_DATA = LAB_DIR / "test_data" / "sensor_readings.csv"
REPO_ROOT = LAB_DIR.parents[1]

# The Secrets Manager persists keys to <repo>/secrets.env — load them here so
# terminal runs and notebook kernels both see NVIDIA_API_KEY.
load_dotenv(REPO_ROOT / "variables.env")
load_dotenv(REPO_ROOT / "secrets.env")
if not os.environ.get("LANGSMITH_API_KEY"):
    os.environ["LANGSMITH_TRACING"] = "false"  # tracing without a key only 401-spams

MODEL_NAME = "nvidia/nemotron-3-super-120b-a12b"


def ensure_test_data():
    """Exercises 3-5 profile/aggregate this CSV; generate it on first use."""
    if not TEST_DATA.exists():
        subprocess.run(["python", str(LAB_DIR / "scripts" / "make_test_data.py")], check=True)

# ---------------------------------------------------------------------------
# The minimal harness, pi-style: a short prompt and four tools.
# ---------------------------------------------------------------------------

MINIMAL_SYSTEM_PROMPT = """You are a capable agent operating a computer through four tools:
read_file, write_file, edit_file, and run_bash.

Work step by step. Use tools to inspect before you act. When writing code,
run it to confirm it works. When the task is complete, reply with a short
summary and no further tool calls."""


@tool
def read_file(path: str) -> str:
    """Read a text file and return its contents (truncated to 8000 chars)."""
    try:
        return Path(path).expanduser().read_text()[:8000]
    except OSError as exc:
        return f"ERROR: {exc}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed."""
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"Wrote {len(content)} chars to {target}"


@tool
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace the first occurrence of old_text with new_text in a file."""
    target = Path(path).expanduser()
    text = target.read_text()
    if old_text not in text:
        return "ERROR: old_text not found"
    target.write_text(text.replace(old_text, new_text, 1))
    return f"Edited {target}"


@tool
def run_bash(command: str) -> str:
    """Run a shell command and return stdout+stderr (120s timeout)."""
    proc = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=120
    )
    return (proc.stdout + proc.stderr)[-8000:] or f"(exit {proc.returncode})"


CORE_TOOLS = [read_file, write_file, edit_file, run_bash]
TOOL_REGISTRY = {t.name: t for t in CORE_TOOLS}


# The harness, not the model, holds the conversation. invoke_with_retry keeps a
# reference to the live message list so Exercise 5 can review the transcript.
LAST_RUN_MESSAGES = []


def invoke_with_retry(model, messages, attempts=3):
    """Harnesses own retries (responsibility #4): survive transient API errors."""
    global LAST_RUN_MESSAGES
    LAST_RUN_MESSAGES = messages
    for attempt in range(attempts):
        try:
            return model.invoke(messages)
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(2 * (attempt + 1))


def build_bare_agent(extra_tools=None, system_prompt=MINIMAL_SYSTEM_PROMPT):
    """Exercise 1: a complete harness in ~20 lines.

    Returns run(task) -> final answer string. The loop: call the model,
    execute any tool calls, feed results back, repeat until a plain reply.
    """
    tools = CORE_TOOLS + list(extra_tools or [])
    registry = {t.name: t for t in tools}
    model = ChatNVIDIA(model=MODEL_NAME, temperature=0.2).bind_tools(tools)

    def run(task: str, max_turns: int = 20) -> str:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=task)]
        for _ in range(max_turns):
            response = invoke_with_retry(model, messages)
            messages.append(response)
            if not response.tool_calls:
                return response.content
            for call in response.tool_calls:
                print(f"  🛠️  {call['name']}({json.dumps(call['args'])[:120]})")
                result = registry[call["name"]].invoke(call["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
        return "ERROR: max turns exceeded"

    return run


# ---------------------------------------------------------------------------
# Exercise 2 — the context tax
# ---------------------------------------------------------------------------

ENCODER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text))


def harness_overhead(system_prompt: str, tools) -> int:
    """Tokens a harness pays on EVERY call: prompt + registered tool schemas."""
    # convert_to_openai_tool() accepts both tool objects and already-converted
    # dict schemas (LangChain tool objects are NOT callable, so don't callable()-check).
    schemas = [convert_to_openai_tool(t) for t in tools]
    return count_tokens(system_prompt) + count_tokens(json.dumps(schemas))


def measure_context_tax() -> dict:
    """Exercise 2a: compare minimal vs maximal per-turn overhead."""
    maximal_prompt = (LAB_DIR / "maximal_system_prompt.txt").read_text()
    maximal_tools = json.loads((LAB_DIR / "maximal_tool_schemas.json").read_text())

    minimal = harness_overhead(MINIMAL_SYSTEM_PROMPT, CORE_TOOLS)
    maximal = harness_overhead(maximal_prompt, maximal_tools)

    print(f"Minimal harness: {minimal:>7,} tokens/turn")
    print(f"Maximal harness: {maximal:>7,} tokens/turn   ({maximal / minimal:.1f}x tax)")
    return {"minimal": minimal, "maximal": maximal}


def parse_frontmatter(skill_md: str) -> dict:
    """Pull name/description out of a SKILL.md YAML frontmatter block."""
    match = re.match(r"^---\n(.*?)\n---\n", skill_md, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md missing frontmatter")
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    if not meta.get("name") or not meta.get("description"):
        raise ValueError("frontmatter needs both name and description")
    return meta


def load_skills_lazily(skills_dir: Path = SKILLS_DIR):
    """Exercise 2b: lazy skills — one line of context each, full body on demand.

    Returns (index_text, load_skill_tool). The index goes in the system
    prompt; the tool lets the model pull in a full skill body when needed.
    """
    bodies, index_lines = {}, []
    for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
        if skill_file.parent.name.startswith("."):
            continue
        text = skill_file.read_text()
        meta = parse_frontmatter(text)
        bodies[meta["name"]] = text
        index_lines.append(f"- {meta['name']}: {meta['description']}")

    index_text = (
        "Installed skills (load one with the load_skill tool when relevant):\n"
        + "\n".join(index_lines)
    )

    @tool
    def load_skill(name: str) -> str:
        """Load the full instructions of an installed skill by name."""
        return bodies.get(name, f"ERROR: no skill named {name!r}")

    eager = sum(count_tokens(b) for b in bodies.values())
    lazy = count_tokens(index_text)
    print(f"{len(bodies)} eager skills: +{eager:,} tokens/turn")
    print(f"{len(bodies)} lazy skills:  +{lazy:,} tokens/turn   ({eager / max(lazy, 1):.0f}x savings)")
    return index_text, load_skill


# ---------------------------------------------------------------------------
# Exercise 3 — author a portable skill
# (answer key: skills/.examples/dataset_profiler/SKILL.md; the exercise is
#  to write your own at skills/dataset_profiler/SKILL.md and load it below)
# ---------------------------------------------------------------------------

def run_with_skills(task: str) -> str:
    """Run the bare agent with the lazy skill index attached."""
    index_text, load_skill = load_skills_lazily()
    run = build_bare_agent(
        extra_tools=[load_skill],
        system_prompt=MINIMAL_SYSTEM_PROMPT + "\n\n" + index_text,
    )
    return run(task)


# ---------------------------------------------------------------------------
# Exercise 4 — verified NVIDIA skill + real GPU
# ---------------------------------------------------------------------------

def run_gpu_task() -> str:
    """Aggregate a 1M-row CSV; the cuDF skill steers the model to the GPU.

    Install + verify the skill first:
      bash scripts/install_nvidia_skill.sh accelerated-computing-cudf
    """
    if not (SKILLS_DIR / "accelerated-computing-cudf" / "SKILL.md").exists():
        return "Skill not installed — run scripts/install_nvidia_skill.sh first."
    ensure_test_data()

    has_gpu = subprocess.run("nvidia-smi", shell=True, capture_output=True).returncode == 0
    has_cudf = subprocess.run(["python", "-c", "import cudf"], capture_output=True).returncode == 0
    if not has_gpu:
        print("⚠️  No GPU detected — the agent will fall back to pandas. "
              "On a GPU machine, watch `nvidia-smi` light up instead.")
    elif not has_cudf:
        print("⚠️  cuDF isn't importable — run `pip install cudf-cu12`, "
              "or the agent will fall back to pandas.")

    return run_with_skills(
        f"Load {TEST_DATA} (about 1M rows) and compute the mean, max, and count "
        "of `reading` per `device_id`, sorted by mean descending. Use GPU "
        "acceleration if the hardware supports it. Save the result to "
        f"{LAB_DIR / 'test_data' / 'aggregates.csv'} and show the top 5 rows."
    )


# ---------------------------------------------------------------------------
# Exercise 5 — the self-evolving harness
# ---------------------------------------------------------------------------

SKILL_AUTHOR_PROMPT = """Review this transcript of an agent completing a task.
Extract the reusable PROCEDURE (not the task-specific values) and write it as
an agent skill in exactly this format — output ONLY the file content:

---
name: <short_snake_case_name>
description: <one line stating when this skill should be used>
---

# <Title>

<numbered procedure the agent should follow next time>

TRANSCRIPT:
{transcript}"""


def format_transcript(messages) -> str:
    """Flatten a run's message list into the TASK/TOOL/RESULT/ANSWER transcript."""
    lines = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            continue
        if isinstance(msg, HumanMessage):
            lines.append(f"TASK: {msg.content}")
        elif isinstance(msg, ToolMessage):
            lines.append(f"RESULT: {str(msg.content)[:300]}")
        elif getattr(msg, "tool_calls", None):
            lines.extend(
                f"TOOL: {call['name']}({json.dumps(call['args'])[:300]})"
                for call in msg.tool_calls
            )
        elif getattr(msg, "content", None):
            lines.append(f"ANSWER: {msg.content}")
    return "\n".join(lines)


def self_evolve_skill(transcript: str, skills_dir: Path = SKILLS_DIR) -> Path:
    """Exercise 5: the agent writes a new skill from its own transcript."""
    model = ChatNVIDIA(model=MODEL_NAME, temperature=0.2)
    skill_md = model.invoke(SKILL_AUTHOR_PROMPT.format(transcript=transcript)).content
    skill_md = skill_md.strip().removeprefix("```markdown").removeprefix("```").removesuffix("```").strip()

    meta = parse_frontmatter(skill_md)  # validate BEFORE saving — a malformed
    target = skills_dir / meta["name"] / "SKILL.md"  # skill breaks the loader
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(skill_md)
    print(f"🌱 Agent wrote itself a new skill: {target}")
    return target


def run_self_evolution_demo():
    task = (
        f"Check whether the CSV at {TEST_DATA} has any nulls or duplicate "
        "rows, and report the verdict in one sentence."
    )
    ensure_test_data()

    run = build_bare_agent()

    print("=== Run 1 (no skill) ===")
    print(run(task))
    # The agent reviews the REAL transcript of run 1 — every tool call and
    # result the harness recorded — and distills the reusable procedure.
    self_evolve_skill(format_transcript(LAST_RUN_MESSAGES))

    print("\n=== Run 2 (with the skill the agent just wrote) ===")
    print(run_with_skills(task))


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exercise", type=int, choices=[1, 2, 3, 4, 5], required=True)
    args = parser.parse_args()

    if args.exercise == 1:
        run = build_bare_agent()
        print(run(
            "Create a file named harness_hello.txt containing the words "
            "'minimal harness', then read it back and confirm its contents."
        ))
    elif args.exercise == 2:
        measure_context_tax()
        load_skills_lazily()
    elif args.exercise == 3:
        ensure_test_data()
        print(run_with_skills(
            f"Profile the dataset at {TEST_DATA} and report your findings."
        ))
    elif args.exercise == 4:
        print(run_gpu_task())
    elif args.exercise == 5:
        run_self_evolution_demo()


if __name__ == "__main__":
    main()
