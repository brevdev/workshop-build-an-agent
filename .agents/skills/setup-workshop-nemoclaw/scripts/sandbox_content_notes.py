#!/usr/bin/env python3
"""sandbox_content_notes.py — adapt .devx lesson content for the OpenShell
sandbox pathway (same spirit as neutralize_pip_cells.py for notebooks).

Two adjustments, both idempotent and sandbox-copy-local (never committed):

1. Rewrite `/project/...` inside ```bash fenced blocks to the sandbox repo
   path. The AI Workbench pathway mounts the repo at /project; here learners
   copy-paste those commands into the Terminal tile and hit
   "No such file or directory". Prose/log-output mentions outside bash fences
   are left untouched.

2. Inject a short "SANDBOX NOTE" admonition (marker-guarded) at the top of
   lessons whose primary flow depends on egress/hardware this sandbox
   deliberately lacks (npm/remote-MCP, Docker, GPU), pointing at the
   sandbox-supported alternative documented in the same lesson.

Usage: python sandbox_content_notes.py /sandbox/workshop-build-an-agent
"""
import os
import re
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "/sandbox/workshop-build-an-agent"
MARKER = "<!-- [sandbox-note] -->"

NOTES = {
    "2-agentic-rag/mcp.md": (
        "> **🛡️ SANDBOX NOTE:** In this OpenShell sandbox the remote-MCP path "
        "(PART 2A — `npx`/`mcp.tavily.com`) is egress-blocked by policy: each "
        "`web_search` call fails after an npm retry delay. Use the *Optional* "
        "local-server exercise instead (PART 2B in `rag_agent.py` + "
        "`uvicorn mcp_server:app --port 8000`) — its dependencies are "
        "pre-installed and only `api.tavily.com` egress is needed."
    ),
    "2-agentic-rag/migrate.md": (
        "> **🛡️ SANDBOX NOTE:** Local NIM deployment needs Docker and a GPU — "
        "neither exists in this sandbox. Treat this lesson as a read-through "
        "here and run it on a GPU host pathway (Brev / AI Workbench)."
    ),
    "4-agent-customization/grpo_training.md": (
        "> **🛡️ SANDBOX NOTE:** The training notebooks (`02_grpo_training`, "
        "`03_run_agent`) require a GPU and torch/unsloth, which are "
        "intentionally not installed in this sandbox — their first import "
        "cell fails fast. `bash_agent.ipynb` and "
        "`01_synthetic_data_generation.ipynb` run fully here."
    ),
    "4-agent-customization/run_customized.md": (
        "> **🛡️ SANDBOX NOTE:** Running the customized model locally requires "
        "the GPU-trained checkpoint from the previous lesson — not available "
        "in this sandbox pathway."
    ),
    "5-deep-agents/experience_deep_agent.md": (
        "> **🛡️ SANDBOX NOTE:** Skip the `python3.12 -m venv` + `pip install` "
        "step — the backend's dependencies are pre-installed in the workshop "
        "venv (and `python3.12` does not exist here). Start the backend "
        "directly: `cd demo/backend && uvicorn server:app --host 0.0.0.0 "
        "--port 8000` (pick another port if module-2's MCP server holds 8000). "
        "Keep the default **Llama** model — the streaming backend garbles "
        "Nemotron's reasoning output (same streaming/tool-calling caveat the "
        "module-2 client documents). The client build (`npm install`) and "
        "Docker sandboxing are unavailable: the Deep Agents Client tile "
        "serves its setup page, and sandbox-mode falls back to local "
        "execution with a loud warning — that warning IS this module's "
        "security lesson."
    ),
    "7-agent-harnesses/harness_lab.md": (
        "> **🛡️ SANDBOX NOTE:** The Hermes installer host "
        "(`hermes-agent.nousresearch.com`) is egress-blocked — but this "
        "sandbox already ships `hermes` (check `hermes --version`), so the "
        "Hermes exercises can use the preinstalled CLI. "
        "`scripts/install_nvidia_skill.sh` needs a `git clone` of "
        "github.com/NVIDIA/skills, which the policy scopes out by default — "
        "the operator can enable it with the 4 extra rules documented in the "
        "operator skill's policy-blocks.md."
    ),
    "6-agent-safety/setup_nemoclaw.md": (
        "> **🛡️ SANDBOX NOTE:** The NemoClaw installer needs Docker (gateway "
        "container) — unavailable in this sandbox. The safety-evaluation "
        "pipeline in [Evaluating Safety](evaluating_safety.md) still runs: "
        "it uses the built-in mock agent and skips CLI-backed agents "
        "gracefully."
    ),
    "6-agent-safety/setup_openclaw.md": (
        "> **🛡️ SANDBOX NOTE:** The OpenClaw CLI install needs npm egress — "
        "blocked in this sandbox. Continue to "
        "[Evaluating Safety](evaluating_safety.md); the evaluation pipeline "
        "runs with the mock agent and skips CLI-backed agents gracefully."
    ),
}

BASH_FENCE = re.compile(r"```bash\n(.*?)```", re.S)


def rewrite_project_paths(text: str) -> tuple[str, int]:
    count = 0

    def fix(m):
        nonlocal count
        body = m.group(1)
        new = body.replace("/project/", f"{REPO}/")
        if new != body:
            count += body.count("/project/")
        return f"```bash\n{new}```"

    return BASH_FENCE.sub(fix, text), count


changed = 0
for rel, note in sorted(NOTES.items()):
    path = os.path.join(REPO, ".devx", rel)
    if not os.path.exists(path):
        print(f"skip (missing): {rel}")
        continue
    text = open(path).read()
    orig = text
    if MARKER not in text:
        lines = text.split("\n")
        insert_at = 1 if lines and lines[0].startswith("<div class=\"dx-hero\"") else 0
        lines.insert(insert_at, f"\n{MARKER}\n{note}")
        text = "\n".join(lines)
    text, n = rewrite_project_paths(text)
    if text != orig:
        open(path, "w").write(text)
        changed += 1
        print(f"adapted: {rel}" + (f" (+{n} /project path fixes)" if n else ""))

# /project path fixes in lessons that need no note
for rel in ("6-agent-safety/evaluating_safety.md", "6-agent-safety/using_nemoclaw.md"):
    path = os.path.join(REPO, ".devx", rel)
    if not os.path.exists(path):
        continue
    text = open(path).read()
    new, n = rewrite_project_paths(text)
    if new != text:
        open(path, "w").write(new)
        changed += 1
        print(f"adapted: {rel} (+{n} /project path fixes)")

print(f"done: {changed} lesson file(s) adapted")
