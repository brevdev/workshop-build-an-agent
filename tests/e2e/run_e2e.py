"""Work through the workshop end to end with its solutions, the way a learner would.

    python tests/e2e/run_e2e.py 1 2 3          # modules to run (default: 1-3, 5-7)
    python tests/e2e/run_e2e.py 4 --gpu        # Module 4 trains on the GPU (about 40 minutes on an A100)
    python tests/e2e/run_e2e.py 6 --live       # also checks a running NemoClaw sandbox

Exercise files are never edited. Notebooks run from their answer keys, or with
the solutions from their own "NEED SOME HELP" cells (Module 1). Answer-key .py
files are loaded under the exercise module's name. Interactive prompts are
answered like a learner would answer them. Requires the saved workshop keys.

Results print per step with timings; the exit code is the number of failed steps.
See tests/e2e/README.md for the installer and local-NIM release checks.
"""

import argparse
import contextlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "code"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kernel import CellError, Kernel  # noqa: E402

RESULTS = []


ONLY = []


def step(name, body, attempts=2):
    """Run one named step; retry once, because hosted APIs and DNS here fail transiently."""
    if ONLY and not any(word.lower() in name.lower() for word in ONLY):
        return None
    print(f"\n▶ {name}", flush=True)
    start = time.monotonic()
    for attempt in range(1, attempts + 1):
        try:
            body()
        except Exception as error:  # report and continue with the next step
            detail = str(error) if isinstance(error, (CellError, AssertionError)) else traceback.format_exc()
            print(f"  attempt {attempt} failed: {detail[-3000:]}", flush=True)
            continue
        seconds = time.monotonic() - start
        note = "" if attempt == 1 else f" (passed on attempt {attempt})"
        RESULTS.append((name + note, True, seconds))
        print(f"  ✓ {name}{note} ({seconds:.0f}s)", flush=True)
        return True
    RESULTS.append((name, False, time.monotonic() - start))
    print(f"  ✗ {name}", flush=True)
    return False


def notebook_cells(path):
    return json.loads(Path(path).read_text())["cells"]


def solved_from_help(path, extra=None):
    """Code cells of an exercise notebook, with each blank cell replaced by the
    solution in the "NEED SOME HELP" cell that follows it (or by `extra`)."""
    cells, sources = notebook_cells(path), []
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        if "..." in source:
            following = "".join(cells[index + 1]["source"]) if index + 1 < len(cells) else ""
            solution = re.findall(r"```python\n(.*?)```", following, re.S)
            if "NEED SOME HELP" in following and solution:
                source = solution[0]
            elif extra and index in extra:
                source = extra[index]
            else:
                raise AssertionError(f"{path.name} cell {index} has a blank but no solution.")
        sources.append(source)
    return sources


def run_cells(sources, cwd, answers=None, setup="", check="", timeout=900, skip=lambda source: False):
    """Run cells in order in a fresh kernel; then run `check` (assertions about the result)."""
    kernel = Kernel(cwd, answers)
    try:
        if setup:
            kernel.run(setup)
        for source in sources:
            if source.strip() and not skip(source):
                kernel.run(source, timeout=timeout)
        if check:
            kernel.run(check)
        return "".join(kernel.transcript)
    finally:
        kernel.close()


def alias_answers(*pairs):
    """Setup code that makes `import exercise` (and importlib.reload) load the answer-key file instead."""
    files = {name: str(path) for name, path in pairs}
    return f"""import importlib.abc, importlib.util, sys
class _AnswerKeys(importlib.abc.MetaPathFinder):
    files = {files!r}
    def find_spec(self, name, path=None, target=None):
        if name in self.files:
            return importlib.util.spec_from_file_location(name, self.files[name])
sys.meta_path.insert(0, _AnswerKeys())
"""


@contextlib.contextmanager
def preserved(*paths):
    """Move a learner's existing files aside for the run; remove what the run creates; put them back."""
    stash = ROOT / "tests/e2e/.stash"
    moved = []
    for index, path in enumerate(paths):
        if path.exists():
            stash.mkdir(parents=True, exist_ok=True)
            target = stash / f"{index}-{path.name}"
            shutil.move(str(path), str(target))
            moved.append((path, target))
    try:
        yield
    finally:
        for path in paths:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
        for path, target in moved:
            shutil.move(str(target), str(path))
        if stash.exists() and not any(stash.iterdir()):
            stash.rmdir()


def wait_for(url, seconds=180):
    """Poll `url` until it answers 200, or fail."""
    import urllib.request
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(2)
    raise AssertionError(f"{url} did not come up within {seconds}s")


class Server:
    """A background server process whose output goes to a log file."""

    def __init__(self, command, cwd, log, env=None):
        import os
        self.log = Path(log)
        self.process = subprocess.Popen(command, cwd=cwd, stdout=self.log.open("w"), stderr=subprocess.STDOUT,
                                        env={**os.environ, **(env or {})}, start_new_session=True)

    def stop(self):
        import os, signal
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
            self.process.wait(timeout=30)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            pass

    def text(self):
        return self.log.read_text(errors="replace")


def module_1():
    lab = CODE / "1-build-an-agent"
    # The second model call repeats the first one's arguments; it has no help cell of its own.
    second_call = """if tool_results:
    llm_response = call_llm(
        model_client=client,
        model_name=MODEL_NAME,
        message_history=memory,
        tool_list=tools,
    )
    memory.append(llm_response)
print(llm_response)
if llm_response.get("tool_calls"):
    print("More tools requested: repeat the routing cells before expecting a final answer.")
"""
    def intro():
        out = run_cells(solved_from_help(lab / "intro_to_agents.ipynb", extra={32: second_call}), lab)
        assert "Requested tools: 1" in out, "The model did not request the add tool."

    def docgen():
        run_cells(solved_from_help(lab / "docgen_client.ipynb"), lab, timeout=600, check="""
searches = [m for m in state["messages"] if getattr(m, "name", None) == "search_tavily"]
assert searches, "The report agent never searched."
assert all(m.status != "error" for m in searches), "A search failed."
assert len(response.content) > 1500 and "http" in response.content, "The report is short or uncited."
print(f"{len(searches)} searches; report {len(response.content)} characters")
""")

    step("M1 intro_to_agents.ipynb: model client, tool, ReAct loop", intro)
    step("M1 docgen_client.ipynb: report agent with web search", docgen)

RAG_CHECK = """
import re
import rag_agent
async def ask(question):
    result = await rag_agent.AGENT.ainvoke({"messages": [{"role": "user", "content": question}]})
    tools = [m.name for m in result["messages"] if m.type == "tool"]
    errors = [m.content for m in result["messages"] if m.type == "tool" and m.status == "error"]
    assert not errors, errors
    return tools, result["messages"][-1].content

tools, answer = await ask("How do I reset my password?")
assert "company_llc_it_knowledge_base" in tools and re.search(r"[[【]KB:", answer), (tools, answer[:500])
tools, answer = await ask("Use web_search to find one recent news headline about NVIDIA. Cite the URL.")
assert "web_search" in tools and "Search failed" not in answer and "http" in answer, (tools, answer[:500])
tools, answer = await ask("List the available skills, load the code-review skill, and summarize it in one sentence.")
assert {"list_available_skills", "get_skill"} <= set(tools), tools
print("KB, web search and skills all used")
"""


def module_2():
    lab = CODE / "2-agentic-rag"
    answers = lab / "rag_agent.answers.py"
    def agent():
        run_cells([], lab, setup=alias_answers(("rag_agent", answers)), check=RAG_CHECK, timeout=600)

    def served():
        import os
        config = lab / ".e2e-langgraph.json"
        config.write_text(json.dumps({"dependencies": ["."], "graphs": {"rag_agent": f"./{answers.name}:AGENT"},
                                      "env": "../../secrets.env"}))
        server = Server(["langgraph", "dev", "--config", str(config), "--port", "2124", "--no-browser"],
                        lab, ROOT / "tests/e2e/.langgraph-dev.log")
        try:
            wait_for("http://127.0.0.1:2124/ok", 240)
            from streamlit.testing.v1 import AppTest
            os.environ["LANGGRAPH_API_URL"] = "http://127.0.0.1:2124"
            sys.path.insert(0, str(lab))  # `streamlit run` puts the script's folder on the path
            app = AppTest.from_file(str(lab / "simple_client.py"), default_timeout=300)
            app.run()
            assert not app.exception, app.exception
            app.chat_input[0].set_value("How do I connect to the VPN?").run()
            assert not app.exception and not app.error, (app.exception, [e.value for e in app.error])
            replies = [m.markdown[0].value for m in app.chat_message if m.markdown]
            assert any(re.search(r"[[【]KB:", reply) for reply in replies), replies[-2:]
        finally:
            server.stop()
            config.unlink(missing_ok=True)

    def local_mcp():
        server = Server([sys.executable, "-m", "uvicorn", "mcp_server:app", "--port", "8765"], lab,
                        ROOT / "tests/e2e/.mcp-server.log")
        try:
            time.sleep(5)
            run_cells([], lab, check="""
from langchain_mcp_adapters.client import MultiServerMCPClient
client = MultiServerMCPClient({"tavily": {"transport": "sse", "url": "http://localhost:8765/sse"}})
async with client.session("tavily") as session:
    result = await session.call_tool("tavily_search", {"query": "NVIDIA Nemotron"})
text = result.content[0].text
assert "URL:" in text and not text.startswith("Error"), text[:300]
""")
            assert "Traceback" not in server.text(), server.text()[-2000:]
        finally:
            server.stop()

    step("M2 rag_agent: knowledge base, web search over MCP, skills", agent)
    with preserved(lab / ".langgraph_api"):  # langgraph dev's local thread store
        step("M2 langgraph dev + Simple Agents Client", served)
    step("M2 optional local MCP server (SSE)", local_mcp)

def all_code(path):
    return ["".join(cell["source"]) for cell in notebook_cells(path) if cell["cell_type"] == "code"]


def module_3():
    lab = CODE / "3-agent-evaluation"
    data = ROOT / "data/evaluation"
    generated = ["synthetic_rag_agent_test_cases.json", "synthetic_rag_agent_candidates.json",
                 "rag_cases_requiring_correction.json", "synthetic_report_agent_test_cases.json",
                 "synthetic_report_agent_candidates.json"]
    runs_before = set((lab / "runs").glob("*")) if (lab / "runs").exists() else set()
    answers = alias_answers(("rag_agent", CODE / "2-agentic-rag/rag_agent.answers.py"),
                            ("evaluation_framework", lab / "evaluation_framework.answers.py"))

    def rag_dataset():
        cells = all_code(lab / "generate_rag_eval_dataset.ipynb")
        save = next(c for c in cells if "synthetic_rag_agent_candidates.json" in c)
        run_cells(cells, lab, timeout=900, check=f"""
import json
candidates = json.loads(candidate_path.read_text())
assert candidates and all("case" in c for c in candidates), "Saved candidates need their CASE number."
reviewed_indices = {{candidates[-1]["case"]}}
{save}
approved = json.loads(output_path.read_text())
assert [c["case"] for c in approved] == [candidates[-1]["case"]], approved
print("Review recorded by CASE number:", approved[0]["case"])
""")

    def report_dataset():
        run_cells(all_code(lab / "generate_report_eval_dataset.ipynb"), lab, timeout=900, check="""
import json
assert json.loads(candidate_path.read_text()), "No report candidates were saved."
""")

    def evaluate_rag():
        run_cells(all_code(lab / "evaluate_rag_agent.answers.ipynb"), lab, setup=answers, timeout=2400, check="""
answered = [r for r in results if r["agent_status"] == "ok"]
assert len(answered) == len(results), [(r["case_id"], r["agent_status"]) for r in results]
assert ragas_record["status"] in ("complete", "partial"), ragas_record
assert summary["fully_graded"] >= len(results) - 1, summary
print({k: v for k, v in summary.items() if k != "metrics"})
""")

    def evaluate_report():
        run_cells(all_code(lab / "evaluate_report_agent.answers.ipynb"), lab, setup=answers, timeout=1800, check="""
assert all(r["agent_status"] == "ok" for r in results), [(r["case_id"], r["agent_status"]) for r in results]
print({k: v for k, v in summary.items() if k != "metrics"})
""")

    learner_data = [data / name for name in generated]
    with preserved(*learner_data, lab / "artifacts"):  # artifacts/: Data Designer run folders
        step("M3 generate_rag_eval_dataset.ipynb + review by CASE number", rag_dataset)
        step("M3 generate_report_eval_dataset.ipynb", report_dataset)
    # Reviewed learner datasets would replace the shipped ones in the evaluations below.
    with preserved(*learner_data):
        try:
            step("M3 evaluate_rag_agent (answer key): agent run, judge, RAGAS", evaluate_rag, attempts=1)
            step("M3 evaluate_report_agent (answer key)", evaluate_report, attempts=1)
        finally:
            for run in set((lab / "runs").glob("*")) - runs_before if (lab / "runs").exists() else []:
                shutil.rmtree(run, ignore_errors=True)


def deep_agent_chat(base, config, messages, approvals=()):
    """Drive the Deep Agents backend like its web client: SSE chat, approving HITL pauses."""
    import httpx
    approvals, events = list(approvals), []

    def stream(client, url, payload):
        interrupt, name = None, None
        with client.stream("POST", url, json=payload, timeout=600) as response:
            for line in response.iter_lines():
                if line.startswith("event:"):
                    name = line[6:].strip()
                elif line.startswith("data:") and line[5:].strip():
                    data = json.loads(line[5:])
                    events.append((name, data))
                    if name == "interrupt":
                        interrupt = approvals.pop(0) if approvals else "approve"
        return interrupt

    with httpx.Client() as client:
        created = client.post(f"{base}/api/agent", json=config, timeout=300)
        assert created.status_code == 200, created.text
        session = created.json()
        try:
            for message in messages:
                decision = stream(client, f"{base}/api/agent/{session['session_id']}/chat", {"message": message})
                while decision:
                    decision = stream(client, f"{base}/api/agent/{session['session_id']}/approve",
                                      {"decision": decision})
        finally:
            client.delete(f"{base}/api/agent/{session['session_id']}")
    errors = [data for name, data in events if name == "error"]
    assert not errors, errors
    return session, events


def module_5():
    backend = ROOT / "demo/backend"
    python = backend / ".venv/bin/python"
    base = "http://127.0.0.1:8000"

    def tests():
        assert python.exists(), "Create the backend venv first, as the lesson does (see demo/backend/requirements.txt)."
        result = subprocess.run([str(python), "-m", "pytest", "-q", "-p", "no:cacheprovider", "../../code/5-deep-agents/tests"],
                                cwd=backend, capture_output=True, text=True, timeout=600)
        assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]

    def tool_outputs(events, tool):
        return [str(data.get("output")) for name, data in events if name == "tool_end" and data.get("name") == tool]

    server = None

    def start():
        nonlocal server
        server = Server([str(python), "-m", "uvicorn", "server:app", "--port", "8000"], backend,
                        ROOT / "tests/e2e/.deep-agents.log")
        wait_for(f"{base}/api/health", 120)

    def host_tools_with_approval():
        session, events = deep_agent_chat(base, {"model_id": "nemotron", "skill_ids": ["fileio", "execute"],
                                                 "hitl_enabled": True},
                                          ["Write /tmp/deepagent_workspace/e2e_hello.py that prints 'hello from e2e', "
                                           "then run it with python3 and tell me the output."],
                                          approvals=["approve", "approve", "approve"])
        assert any(name == "interrupt" for name, _ in events), "HITL never asked for approval."
        assert any("hello from e2e" in out for out in tool_outputs(events, "execute")), events[-5:]
        Path("/tmp/deepagent_workspace/e2e_hello.py").unlink(missing_ok=True)

    def sandboxed_execution():
        session, events = deep_agent_chat(base, {"model_id": "nemotron", "skill_ids": ["fileio", "execute"],
                                                 "sandbox_map": {"execute": True}},
                                          ["Run `cat /etc/hostname && ls /workspace` and show me the output."])
        assert session["sandbox_active"], session
        outputs = tool_outputs(events, "execute")
        assert outputs and "project-build-an-agent" not in " ".join(outputs), outputs

    def web_and_rag():
        _, events = deep_agent_chat(base, {"model_id": "nemotron", "skill_ids": ["websearch", "rag"]},
                                    ["Use the IT knowledge base: how do I reset my password?",
                                     "Search the web for one recent NVIDIA news headline."])
        tools = {data.get("name") for name, data in events if name == "tool_end"}
        assert "it_knowledge_base" in tools and tools & {"tavily_search_results_json", "tavily_search_results", "web_search"}, tools

    def frontend():
        demo = ROOT / "demo"
        for command in (["npm", "install", "--no-audit", "--no-fund"], ["npm", "run", "build"]):
            result = subprocess.run(command, cwd=demo, capture_output=True, text=True, timeout=900)
            assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]

    step("M5 tests in the demo backend venv", tests, attempts=1)
    try:
        step("M5 Deep Agents backend starts (answer key)", start, attempts=1)
        if server:
            step("M5 host file + execute tools with HITL approval", host_tools_with_approval)
            step("M5 Docker sandbox execution", sandboxed_execution)
            step("M5 web search and RAG tools", web_and_rag)
    finally:
        if server:
            server.stop()
    step("M5 frontend build", frontend, attempts=1)


def run_script(args, cwd, timeout=900, env=None):
    import os
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                            env={**os.environ, **(env or {})})
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]
    return result.stdout


def module_6(live=False):
    lab = CODE / "6-agent-safety"
    answers = lab / "agent_safety.answers.py"

    def offline():
        out = run_script([sys.executable, str(answers)], lab, timeout=300)
        # By design: the weak policy fails its checks and the leaky mock fails the probes.
        assert "baseline_permissive.yaml: FAILED" in out and "research_assistant.yaml: FAILED" in out, out
        assert "Classification matches: 100%" in out, out

    def judged():
        out = run_script([sys.executable, str(answers), "--judge"], lab, timeout=1200)
        reviews = re.search(r"Judge reviews completed: (\d+)/(\d+)", out)
        assert reviews and reviews.group(1) == reviews.group(2), out

    def sandbox():
        import os
        env = {"PATH": f"{Path.home()}/.local/bin:{Path.home()}/.npm-global/bin:" + os.environ["PATH"]}
        out = run_script(["bash", "scripts/nemoclaw-health.sh"], lab, timeout=180, env=env)
        assert "[FAIL]" not in out, out
        out = run_script([sys.executable, "scripts/check-nemoclaw-agent.py"], lab, timeout=900, env=env)
        assert "READY" in out, out

    step("M6 agent_safety (answer key) with the mock agent", offline)
    step("M6 agent_safety --judge (hosted judge)", judged)
    if live:
        step("M6 live NemoClaw sandbox: health and agent check", sandbox)


def module_7(gpu=False):
    lab = CODE / "7-agent-harnesses"
    answers = [sys.executable, "harness_lab.answers.py", "--exercise"]
    profiler = lab / "skills/dataset-profiler"

    def minimal_harness():
        out = run_script(answers + ["1"], lab, timeout=600)
        assert (lab / "harness_hello.txt").read_text().strip().lower().startswith("minimal harness"), out

    def context_tax():
        out = run_script(answers + ["2"], lab, timeout=300)
        for number in ("390", "3,922", "515", "58"):
            assert number in out, f"{number} missing from:\n{out}"

    def portable_skill():
        shutil.copytree(lab / "skills/.examples/dataset-profiler", profiler, dirs_exist_ok=True)
        out = run_script(answers + ["3"], lab, timeout=900)
        assert "dataset-profiler" in out or "rows" in out.lower(), out[-2000:]

    def verified_gpu_skill():
        run_script(["bash", "scripts/install_nvidia_skill.sh", "accelerated-computing-cudf"], lab, timeout=600)
        out = run_script(answers + ["4"], lab, timeout=1200)
        assert "Receipt" in out and (lab / "test_data/aggregates.csv").exists(), out[-2000:]

    def self_evolving():
        before = {p.name for p in (lab / "skills").iterdir()}
        out = run_script(answers + ["5"], lab, timeout=1200)
        created = {p.name for p in (lab / "skills").iterdir()} - before
        assert created, "No skill was written.\n" + out[-2000:]

    before = {p.name for p in (lab / "skills").iterdir()}
    had_test_data = (lab / "test_data").exists()

    def untracked():  # files the agents write into the lab folder
        out = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "."], cwd=lab,
                             capture_output=True, text=True).stdout
        return set(out.split())
    untracked_before = untracked()
    with preserved(lab / "harness_hello.txt"):
        step("M7 Exercise 1: minimal harness", minimal_harness)
    try:
        step("M7 Exercise 2: context tax numbers match the lesson", context_tax)
        step("M7 Exercise 3: portable skill (shipped example)", portable_skill)
        if gpu:
            step("M7 Exercise 4: verified cuDF skill on the GPU", verified_gpu_skill)
        step("M7 Exercise 5: self-evolving harness", self_evolving)
    finally:
        for name in {p.name for p in (lab / "skills").iterdir()} - before:
            shutil.rmtree(lab / "skills" / name, ignore_errors=True)
        if not had_test_data:
            shutil.rmtree(lab / "test_data", ignore_errors=True)
            shutil.rmtree(lab / ".nvidia-skills-cache", ignore_errors=True)
        for name in untracked() - untracked_before:
            (lab / name).unlink(missing_ok=True)


def learner(messages, approvals="y"):
    """Answer input() prompts like a learner: approve commands, then type the next message."""
    queue = list(messages)

    def answer(prompt):
        if "[y/N]" in prompt:
            return approvals
        return queue.pop(0) if queue else "quit"
    return answer


def module_4(gpu=False):
    lab = CODE / "4-agent-customization"
    keys = lab / "answer_key"

    def base_agent():
        out = run_cells(all_code(keys / "bash_agent.answers.ipynb"), lab, timeout=600,
                        answers=learner(["List the files in this directory.", "quit"]))
        assert "Execute 'ls" in out, out[-2000:]

    def synthetic_data():
        generated = lab / "data/langgraph_cli/generated"
        with preserved(generated, lab / "artifacts"):
            run_cells(all_code(keys / "01_synthetic_data_generation.answers.ipynb"), lab, timeout=1200)
            assert (generated / "train.jsonl").exists(), "No generated training data was saved."

    def grpo():
        server = Server([sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8001"],
                        lab / "nemo_gym_resources/langgraph_cli", ROOT / "tests/e2e/.reward-server.log")
        try:
            wait_for("http://127.0.0.1:8001/health", 60)
            run_cells(all_code(keys / "02_grpo_training.answers.ipynb"), lab, timeout=3600)
        finally:
            server.stop()
        comparison = json.loads((lab / "outputs/grpo_langgraph_cli/held_out_comparison.json").read_text())
        before, after = comparison["baseline"]["exact_match_rate"], comparison["trained"]["exact_match_rate"]
        print(f"  held-out exact match {before:.0%} -> {after:.0%}; "
              f"{comparison['improved']} improved, {comparison['regressed']} regressed")
        assert after >= before + 0.10 and comparison["improved"] > comparison["regressed"], comparison

    def customized_agent():
        app = lab / "bash_agent/e2e-app"
        try:
            out = run_cells(all_code(keys / "03_run_agent.answers.ipynb"), lab, timeout=900, answers=learner([
                "List the files in this directory.",
                "Create a new project at ./e2e-app using the react-agent-python template.",
                "quit"]), check="""
state = agent.get_state({"configurable": {"thread_id": "combined-0"}})
tools = [m.name for m in state.values["messages"] if m.type == "tool"]
assert "langgraph_cli" in tools and "exec_bash_command" in tools, tools
print("tools used:", tools)
""")
            assert "Execute 'ls" in out and "Execute 'langgraph new" in out, out[-3000:]
            assert app.exists(), "langgraph new did not create the project."
        finally:
            shutil.rmtree(app, ignore_errors=True)

    def command_line():
        out = subprocess.run([sys.executable, "-m", "bash_agent.main_hf", "--cli-only"], cwd=lab, text=True,
                             input="Build a Docker image and tag it as myapp:v2\nn\nquit\n",
                             capture_output=True, timeout=900).stdout
        assert "langgraph build" in out and "myapp:v2" in out, out[-2000:]

    step("M4 bash_agent (answer key): hosted agent with HITL", base_agent)
    step("M4 01_synthetic_data_generation (answer key)", synthetic_data)
    if gpu:
        # A learner's trained model is set aside, then restored after these steps.
        with preserved(lab / "outputs/grpo_langgraph_cli"):
            if step("M4 02_grpo_training (answer key): train and compare on held-out data", grpo, attempts=1):
                step("M4 03_run_agent (answer key): bash + fine-tuned LangGraph tool", customized_agent)
                step("M4 main_hf --cli-only from the command line", command_line)


MODULES = {1: module_1, 2: module_2, 3: module_3, 4: module_4, 5: module_5, 6: module_6, 7: module_7}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("modules", nargs="*", type=int, default=[1, 2, 3, 5, 6, 7])
    parser.add_argument("--gpu", action="store_true", help="run GPU steps (Module 4 training)")
    parser.add_argument("--live", action="store_true", help="check a running NemoClaw sandbox (Module 6)")
    parser.add_argument("--only", action="append", default=[], help="run only steps whose name contains this text")
    args = parser.parse_args()
    ONLY.extend(args.only)
    for number in args.modules:
        if number not in MODULES:
            print(f"No end-to-end steps for module {number}.")
            continue
        options = {k: v for k, v in vars(args).items() if k in ("gpu", "live")}
        MODULES[number](**{k: v for k, v in options.items() if k in MODULES[number].__code__.co_varnames})
    failed = [name for name, ok, _ in RESULTS if not ok]
    print("\n" + "=" * 70)
    for name, ok, seconds in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {seconds:6.0f}s  {name}")
    print(f"{len(RESULTS) - len(failed)} passed, {len(failed)} failed")
    return len(failed)


if __name__ == "__main__":
    raise SystemExit(main())
