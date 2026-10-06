"""The shared helpers learners touch: retries, the blank finder and module reset."""

import asyncio
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_support import blanks, reset  # noqa: E402
from workshop_support.resilience import is_transient, resilient_tool  # noqa: E402


class ConnectError(Exception):
    """Stands in for httpx.ConnectError."""


@pytest.mark.parametrize("error,expected", [
    (ConnectionError("reset by peer"), True),
    (ConnectError("boom"), True),
    (Exception("[429] Too Many Requests"), True),
    (OSError("Temporary failure in name resolution"), True),
    (TimeoutError(), True),
    (Exception("[401] Unauthorized"), False),
    (AttributeError("'ellipsis' object has no attribute 'invoke'"), False),
    (ValueError("bad request"), False),
])
def test_only_transient_failures_are_retried(error, expected):
    assert is_transient(error) is expected


def flaky_tool(failures):
    from langchain_core.tools import tool
    calls = {"n": 0}

    @tool
    def lookup(query: str) -> str:
        """Look something up."""
        calls["n"] += 1
        if calls["n"] <= len(failures):
            raise failures[calls["n"] - 1]
        return f"answer for {query}"
    return lookup, calls


def call(tool_, mode="sync"):
    request = {"name": tool_.name, "args": {"query": "vpn"}, "id": "1", "type": "tool_call"}
    return tool_.invoke(request) if mode == "sync" else asyncio.run(tool_.ainvoke(request))


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_transient_failures_are_retried_until_success(mode, monkeypatch):
    monkeypatch.setattr("workshop_support.resilience.time.sleep", lambda seconds: None)
    monkeypatch.setattr("workshop_support.resilience.asyncio.sleep", lambda seconds: asyncio.sleep(0))
    lookup, calls = flaky_tool([ConnectionError("dns"), Exception("[503] busy")])
    message = call(resilient_tool(lookup), mode)
    assert message.status == "success" and message.content == "answer for vpn" and calls["n"] == 3


def test_persistent_transient_failure_becomes_an_error_result(monkeypatch):
    monkeypatch.setattr("workshop_support.resilience.time.sleep", lambda seconds: None)
    lookup, calls = flaky_tool([ConnectionError("dns")] * 5)
    message = call(resilient_tool(lookup, attempts=2))
    assert message.status == "error" and "temporary network" in message.content and calls["n"] == 2


def test_code_errors_fail_fast_with_their_cause():
    lookup, calls = flaky_tool([AttributeError("'ellipsis' object has no attribute 'invoke'")])
    message = call(resilient_tool(lookup))
    assert message.status == "error" and calls["n"] == 1
    assert "AttributeError" in message.content and "temporary" not in message.content


def test_blank_finder_recognizes_every_placeholder_style(tmp_path):
    exercise = tmp_path / "exercise.py"
    exercise.write_text('\n'.join([
        "from pydantic import Field",
        "from typing import Callable, Tuple",
        "model = ...",                                        # blank
        'query = " ... "',                                   # blank
        'note = "..."',                                      # ordinary text
        "name: str = Field(..., description='required')",    # pydantic marker
        "pair: Tuple[int, ...] = (1, 2)",                    # type hint
        "hook: Callable[..., str] = str",                    # type hint
        "prompt = f'Workspace: {...}'",                      # blank inside an f-string
        "TEMPLATE = '''",
        "TODO: ...",                                         # blank inside a template
        "'''",
        "def later():",
        "    raise NotImplementedError('Complete Exercise 2')",  # blank
    ]))
    assert [line for _, line, _ in blanks.find_blanks(exercise)] == [3, 4, 9, 11, 14]
    notebook = tmp_path / "exercise.ipynb"
    notebook.write_text(json.dumps({"cells": [
        {"cell_type": "markdown", "source": ["model = ..."]},
        {"cell_type": "code", "source": ["%pip install x\n", "answer = await agent.ainvoke( ... )"]},
    ]}))
    assert blanks.find_blanks(notebook) == [("code cell 1", 2, "answer = await agent.ainvoke( ... )")]


def test_reset_backs_up_and_restores_exercise_files(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "code").mkdir(parents=True)
    exercise = repo / "code/exercise.py"
    exercise.write_text("model = ...\n")
    for command in (["init", "-q"], ["add", "."], ["-c", "user.email=e2e@example.com", "-c", "user.name=e2e",
                                                    "commit", "-qm", "start"]):
        subprocess.run(["git", "-C", str(repo), *command], check=True)
    exercise.write_text("model = ChatNVIDIA(model='learner work')\n")
    monkeypatch.setattr(reset, "ROOT", repo)
    monkeypatch.setattr(reset, "EXERCISES", {9: ["code/exercise.py"]})
    monkeypatch.setattr(reset.Path, "home", staticmethod(lambda: tmp_path / "home"))
    with patch.object(reset, "matching_processes", return_value=[]), \
         patch.object(reset.subprocess, "run", wraps=subprocess.run):
        assert reset.main(["9", "--yes"]) == 0
    assert exercise.read_text() == "model = ...\n"
    backups = list((tmp_path / "home/workshop-backups").glob("*-module-9/code/exercise.py"))
    assert backups and "learner work" in backups[0].read_text()
