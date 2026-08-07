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
    "1-build-an-agent/secrets.md": (
        "> **🛡️ SANDBOX NOTE:** The `claude`/`codex` CLIs mentioned in the "
        "AI-tutor callout below are **not** preinstalled in this sandbox and "
        "cannot be installed here. `registry.npmjs.org` IS reachable (the "
        "`npm_install` policy block opens it, which is how the module-5 client "
        "is built), but **scoped** packages like `@anthropic-ai/claude-code` "
        "are refused: npm requests scoped metadata as `/@scope%2Fname` and the "
        "L7 proxy rejects request-targets containing an encoded `/`. The "
        "sandbox's resident NemoClaw agent carries the same workshop tutor skills "
        "(`workshop`, `module-1` … `module-7`) — ask it for module guidance "
        "through its normal messaging channel instead."
    ),
    "5-deep-agents/build_deep_agents.md": (
        "> **🛡️ SANDBOX NOTE:** Skip `source .venv/bin/activate` in the "
        "commands below — `demo/backend/.venv` does not exist here and the "
        "workshop venv is already active in every terminal. Run the "
        "`python`/`uvicorn` commands directly, and pick another port if "
        "module-2's MCP server holds 8000."
    ),
    "6-agent-safety/evaluating_safety.md": (
        "> **🛡️ SANDBOX NOTE:** The collapsed Step-1/Step-2 memory-poisoning "
        "walkthrough edits the OpenClaw workspace (`/sandbox/.openclaw/…`) "
        "created on the earlier setup pages — OpenClaw cannot be installed in "
        "this sandbox (npm egress), so treat those steps as a read-through. "
        "The evaluation pipeline below runs fully here: it uses the built-in "
        "mock agent and skips CLI-backed agents gracefully."
    ),
    "7-agent-harnesses/agent_skills.md": (
        "> **🛡️ SANDBOX NOTE:** `npx skills add …` needs the npm registry, "
        "which is egress-blocked here (the command fails fast rather than "
        "hanging). The catalog skill it installs is GPU-oriented (cuDF) — see "
        "the Harness Lab's note for the policy-gated "
        "`install_nvidia_skill.sh` alternative, and the repo-shipped "
        "`skills/` and `code/7-agent-harnesses/skills/` folders for local "
        "skill examples you can open right now."
    ),
    "7-agent-harnesses/gpu_skills.md": (
        "> **🛡️ SANDBOX NOTE:** This page's proof-of-GPU flow (`nvidia-smi`, "
        "the cuDF skill) needs a GPU host — not available in this sandbox; "
        "treat it as a read-through. The skill anatomy and harness-integration "
        "mechanics it teaches are exercised hands-on (CPU-only) in the "
        "Harness Lab."
    ),
    "2-agentic-rag/mcp.md": (
        "> **🛡️ SANDBOX NOTE:** The remote-MCP path (PART 2A — "
        "`npx`/`mcp.tavily.com`) **works here**, same as the bare-metal and AI "
        "Workbench pathways: the operator's `npm_install` + `mcp_tavily` policy "
        "blocks open it, and setup.sh injects `SANDBOX_MCP_ENV` into "
        "`rag_agent.py`. That last part matters — the MCP stdio transport only "
        "forwards HOME/LOGNAME/PATH/SHELL/TERM/USER to the child process, so "
        "without it `npx mcp-remote` starts with no proxy config and dies at "
        "`getaddrinfo EAI_AGAIN mcp.tavily.com`. Pass `'env': SANDBOX_MCP_ENV` "
        "in your `MCP_CONFIG`. PART 2B (the local server) still works and is "
        "worth doing as a contrast: the local server exposes one tool, the "
        "remote MCP exposes five (search, extract, crawl, map, research)."
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
        "module-2 client documents). Model ids are remapped in this sandbox "
        "(Llama → 3.1-70b, DeepSeek → V4-Pro): `deepseek-r1-0528` is "
        "retired from the NIM catalog, `deepseek-v4-flash` is listed but no "
        "longer answers (every probe times out), and `llama-3.3-70b` answers "
        "slower than the client's 60s timeout. **The Deep Agents Client tile "
        "works on first click** — `setup.sh` pre-runs `npm install` + "
        "`npm run build` in `demo/`, so the tile serves the real Deep Agent "
        "Builder UI (if that pre-build ever fails, setup.sh logs a WARNING and "
        "the tile falls back to a 'setup required' page instead of hanging). "
        "Docker sandboxing is still unavailable: sandbox-mode falls "
        "back to local execution with a loud warning — that warning IS this "
        "module's security lesson."
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
        "> **🛡️ SANDBOX NOTE:** **Skip the `install.sh` command below** — "
        "`openclaw.ai` is not in the egress policy. Install straight from npm "
        "instead, which IS allowed (`openclaw` is an unscoped package, and the "
        "sandbox already ships Node v24):\n"
        ">\n"
        "> ```bash\n"
        "> npm config set prefix /sandbox/.npm-global\n"
        "> npm install -g --no-audit --no-fund openclaw@latest\n"
        "> export PATH=\"/sandbox/.npm-global/bin:$PATH\"\n"
        "> openclaw --version\n"
        "> ```\n"
        ">\n"
        "> Then run `openclaw onboard` for the Step-2 wizard (the install "
        "script normally launches it for you). Everything else on this page "
        "applies as written.\n"
        ">\n"
        "> ⚠️ **Whether the agent can then talk to a model depends on your "
        "operator.** The wizard points OpenClaw at "
        "`https://integrate.api.nvidia.com/v1`, but OpenClaw is a Node process "
        "and the default `nvidia` policy block only permits the hermes/python "
        "binaries — so inference fails with `ERR_PROXY_TUNNEL` unless the "
        "operator applied the optional `openclaw_inference` block (see the "
        "operator skill's policy-blocks.md). Without it, continue to "
        "[Evaluating Safety](evaluating_safety.md): the evaluation pipeline "
        "runs with the mock agent and skips CLI-backed agents gracefully.\n"
        ">\n"
        "> Note that OpenClaw running *here* is inside the sandbox, so it is "
        "**not** the \"unsandboxed host agent\" this module contrasts against — "
        "it inherits the same Landlock/seccomp/proxy enforcement as NemoClaw."
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

# Deep Agents Client tile setup page (demo/start_client.sh serve_setup_page):
# written for the AI-Workbench layout (/project paths). The npm registry IS
# reachable in this sandbox now (operator policy block `npm_install`, GET-only
# on registry.npmjs.org), and setup.sh pre-installs + pre-builds the frontend —
# so this page should normally never be seen. Keep it as an accurate fallback
# instead of the old "this sandbox can't build the demo client" text, which is
# no longer true. Marker-guarded; sandbox-copy-local like everything else.
SC = os.path.join(REPO, "demo", "start_client.sh")
SC_MARKER = "<!-- [sandbox-note] -->"
if os.path.exists(SC):
    text = open(SC).read()
    start, end = text.find("  <ol>"), text.find("</ol>")
    if SC_MARKER not in text and start != -1 and end != -1:
        replacement = (
            f"  {SC_MARKER}\n"
            "  <ol>\n"
            "    <li><strong>The frontend isn't built yet.</strong> setup.sh normally does this for\n"
            "      you; if you are seeing this page, the install/build step was skipped or failed.</li>\n"
            "    <li><strong>Build it from a JupyterLab terminal:</strong>\n"
            "      <span class=\"term\">cd " + REPO + "/demo &amp;&amp; npm install --no-audit --no-fund\n"
            "npm run build</span> then reopen this tile. The npm registry is allowed by the\n"
            "      sandbox egress policy (read-only), so this works here.</li>\n"
            "    <li><strong>Backend:</strong> start it per the module-5 lesson SANDBOX NOTE —\n"
            "      <span class=\"term\">cd " + REPO + "/demo/backend\n"
            "uvicorn server:app --host 0.0.0.0 --port 8010</span>.</li>\n"
            "  " )
        text = text[:start] + replacement + text[end:]
        # rewrite_project_paths() only touches ```bash fences (markdown lessons);
        # this is a shell script, so fix the two serve_setup_page reason strings
        # ("run 'npm install' in /project/demo") with a plain replacement.
        n_paths = text.count("/project/")
        text = text.replace("/project/", f"{REPO}/")
        open(SC, "w").write(text)
        changed += 1
        print(f"adapted: demo/start_client.sh (setup page sandbox guidance, +{n_paths} /project path fixes)")

# Dead in-lesson links. docsify resolves an extension-less target `foo` to
# `foo.md`; when no such file exists the content pane just goes blank, with no
# 404 and nothing in the console — so these are easy to ship unnoticed.
# Verified 2026-07-27 by resolving every markdown link across all 7 .devx
# modules (docsify-aware): this was the only genuinely dead target.
LINK_FIXES = {
    # `setup_agent_builder.md` does not exist and is absent from module 5's
    # _sidebar.md; the Agent-Builder setup material lives in experience_deep_agent.
    "5-deep-agents/intro_deep_agents.md": [
        ("](setup_agent_builder)", "](experience_deep_agent)"),
    ],
}
for rel, pairs in LINK_FIXES.items():
    path = os.path.join(REPO, ".devx", rel)
    if not os.path.exists(path):
        continue
    text = open(path).read()
    orig = text
    for old, new in pairs:
        text = text.replace(old, new)
    if text != orig:
        open(path, "w").write(text)
        changed += 1
        print(f"adapted: {rel} (dead link retargeted)")

# /project path fixes in lessons that need no note
# (evaluating_safety.md moved to NOTES above — the NOTES loop also rewrites paths)
for rel in ("6-agent-safety/using_nemoclaw.md",):
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
