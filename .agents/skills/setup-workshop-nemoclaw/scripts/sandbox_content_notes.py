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
   restricts (egress, Docker, GPU), pointing at the
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
        "> **🛡️ SANDBOX NOTE:** Tutor CLIs need their own credentials and permitted install "
        "routes. You can also ask the resident workshop tutor for module guidance."
    ),
    "2-agentic-rag/mcp.md": (
        "> **🛡️ SANDBOX NOTE:** Remote MCP uses Python with an Authorization header. The "
        "operator must allow the Python interpreter to reach `mcp.tavily.com`; no Node "
        "subprocess is needed. The optional local MCP server uses `api.tavily.com`."
    ),
    "2-agentic-rag/migrate.md": (
        "> **🛡️ SANDBOX NOTE:** Local NIM needs Docker and a GPU, which this sandbox does "
        "not provide. Run this optional step on a GPU host."
    ),
    "4-agent-customization/grpo_training.md": (
        "> **🛡️ SANDBOX NOTE:** The training and customized-model notebooks need a GPU and "
        "are unavailable here. You can still work through the starter bash agent and "
        "synthetic-data notebook."
    ),
    "4-agent-customization/run_customized.md": (
        "> **🛡️ SANDBOX NOTE:** Local customized inference needs the GPU-trained checkpoint "
        "from the previous lesson. Use a GPU host for this step."
    ),
    "5-deep-agents/build_deep_agents.md": (
        "> **🛡️ SANDBOX NOTE:** Use the already active workshop venv; skip `source "
        ".venv/bin/activate`. Stop the optional Module 2 MCP server before starting this "
        "backend on port 8000."
    ),
    "5-deep-agents/experience_deep_agent.md": (
        "> **🛡️ SANDBOX NOTE:** Dependencies are installed in the active workshop venv. "
        "Start the backend with `cd demo/backend && uvicorn server:app --host 0.0.0.0 --port"
        " 8000`. Docker is unavailable here: choose local execution explicitly, which runs "
        "inside this existing OpenShell sandbox. Requesting Docker must fail instead of "
        "changing execution modes."
    ),
    "6-agent-safety/evaluating_safety.md": (
        "> **🛡️ SANDBOX NOTE:** The Python exercises can use the explicit mock mode here. "
        "Mock screening and text scores do not establish that the live sandbox enforced a "
        "policy."
    ),
    "6-agent-safety/setup_nemoclaw.md": (
        "> **🛡️ SANDBOX NOTE:** NemoClaw onboarding needs Docker on the host. Continue with "
        "the Python evaluation exercises here, and use a host for the live hardening lab."
    ),
    "6-agent-safety/setup_openclaw.md": (
        "> **🛡️ SANDBOX NOTE:** OpenClaw installed here inherits this sandbox’s controls; it"
        " cannot represent the unsandboxed comparison in this lesson. Use a separate host "
        "for that comparison."
    ),
    "7-agent-harnesses/agent_skills.md": (
        "> **🛡️ SANDBOX NOTE:** Bundled skills are available locally. Installing the NVIDIA "
        "skill also needs the operator’s scoped GitHub clone rules."
    ),
    "7-agent-harnesses/gpu_skills.md": (
        "> **🛡️ SANDBOX NOTE:** This sandbox has no GPU. Use the CPU path here; run the cuDF"
        " comparison on a GPU host."
    ),
    "7-agent-harnesses/harness_lab.md": (
        "> **🛡️ SANDBOX NOTE:** Check `hermes --version` before installing another copy. "
        "Pass the workshop Python path if Hermes uses a different runtime. The NVIDIA skill "
        "installer needs the operator’s scoped GitHub clone rules."
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
    if MARKER in text:
        text = re.sub(re.escape(MARKER) + r"\n(?:>[^\n]*(?:\n|$))+",
                      lambda _: MARKER + "\n" + note + "\n", text, count=1)
    else:
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
            "uvicorn server:app --host 0.0.0.0 --port 8000</span>.</li>\n"
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
