"""Run the lesson navigation regression tests without a browser or extra npm packages."""

from pathlib import Path
import shutil
import subprocess

import pytest


def test_jupyter_navigation():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is needed for the Jupyter navigation tests")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [node, "--test", "tests/jupyter_link.test.cjs"],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
