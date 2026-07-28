#!/usr/bin/env python3
"""tune_remote_mcp_env.py — make module-2 PART 2A (the shipped remote-MCP
default) work inside the sandbox, for parity with the bare-metal/Brev/AI
Workbench pathways.

Why this is needed even once egress is open:

  The MCP Python SDK's stdio transport does NOT pass the parent environment to
  the child process. It forwards a hardcoded allowlist only —
  `mcp.client.stdio.DEFAULT_INHERITED_ENV_VARS` == HOME, LOGNAME, PATH, SHELL,
  TERM, USER. So `npx -y mcp-remote ...` starts with no proxy configuration,
  attempts a DIRECT connection, and dies at `getaddrinfo EAI_AGAIN
  mcp.tavily.com` — there is no direct DNS in the sandbox. No OCSF line is
  emitted because nothing ever reaches the L7 proxy, which makes this look like
  a policy gap when it is not: verified by running the identical
  `npx -y mcp-remote <url>` from a shell (full env), where it connects fine.

  Node 24 additionally needs BOTH halves before `fetch`/undici honours a proxy:
  measured in-sandbox —
      HTTPS_PROXY alone            -> EAI_AGAIN
      NODE_USE_ENV_PROXY alone     -> EAI_AGAIN
      HTTPS_PROXY + NODE_USE_ENV_PROXY -> 405 (connected)
  NODE_EXTRA_CA_CERTS is required for TLS trust against the sandbox's
  terminating proxy.

Operator prerequisite: the `npm_install` and `mcp_tavily` policy blocks.

What gets tuned (sandbox pathway only — upstream content is untouched on the
bare-metal/Brev/AI Workbench pathways):

  1. code/2-agentic-rag/rag_agent.py          — defines SANDBOX_MCP_ENV + hint
  2. code/2-agentic-rag/rag_agent.answers.py  — defines it AND uses it
  3. .devx/2-agentic-rag/mcp.md               — the "Need some help?" solution
                                                block the learner copy-pastes
  4. {.claude,.agents}/skills/module-2/references/exercises.md
                                              — the snippet the in-sandbox
                                                agent hands out as a hint
  5. {.claude,.agents}/skills/module-2/references/troubleshooting.md
                                              — the TaskGroup symptom, which
                                                upstream misattributes to a
                                                missing npx / bad key

  3-5 matter because nobody types MCP_CONFIG from scratch: they copy it from
  the lesson fold or ask the agent. Patching only the .py files left both of
  those still handing out the version that dies at EAI_AGAIN.

Idempotent (marker-guarded). Usage: tune_remote_mcp_env.py <repo-root>
"""
import os
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "/sandbox/workshop-build-an-agent"
MARKER = "# [sandbox] remote-MCP child env"

ANCHOR = 'TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")'

ENV_BLOCK = f'''
{MARKER} — the MCP stdio transport forwards only
# HOME/LOGNAME/PATH/SHELL/TERM/USER to the child, so `npx mcp-remote` would
# start with no proxy config and fail DNS (EAI_AGAIN) in this sandbox.
# Node 24 needs BOTH the proxy URL and NODE_USE_ENV_PROXY=1 before fetch/undici
# honours it; NODE_EXTRA_CA_CERTS trusts the sandbox's terminating TLS proxy.
from mcp.client.stdio import get_default_environment as _mcp_default_env

SANDBOX_MCP_ENV = {{
    **_mcp_default_env(),
    **{{
        _k: os.environ[_k]
        for _k in (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "NO_PROXY",
            "NODE_USE_ENV_PROXY",
            "NODE_EXTRA_CA_CERTS",
        )
        if os.environ.get(_k)
    }},
}}
'''

# rag_agent.answers.py ships the completed PART 2A dict — add the env key.
ANSWERS_OLD = (
    '        "args": ["-y", "mcp-remote", '
    'f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"]\n'
)
ANSWERS_NEW = (
    '        "args": ["-y", "mcp-remote", '
    'f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"],\n'
    '        "env": SANDBOX_MCP_ENV,  # [sandbox] see SANDBOX_MCP_ENV above\n'
)

# rag_agent.py leaves MCP_CONFIG as an exercise — extend the hint list so the
# learner writes the working version rather than one that dies at DNS.
HINT_OLD = (
    "# Hint: set 'args' to ['-y', 'mcp-remote', "
    "f'https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}']\n"
)
HINT_NEW = HINT_OLD + (
    "# Hint [sandbox]: also set 'env' to SANDBOX_MCP_ENV (defined above) — the MCP\n"
    "#   stdio transport drops the proxy variables otherwise and the child npx\n"
    "#   process fails with 'getaddrinfo EAI_AGAIN mcp.tavily.com'.\n"
)

changed = 0
for rel in ("code/2-agentic-rag/rag_agent.py", "code/2-agentic-rag/rag_agent.answers.py"):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        print(f"skip (missing): {rel}")
        continue
    text = open(path).read()
    if MARKER in text:
        print(f"already tuned: {rel}")
        continue
    if ANCHOR not in text:
        print(f"WARNING: anchor not found, skipping: {rel}")
        continue

    new = text.replace(ANCHOR, ANCHOR + "\n" + ENV_BLOCK, 1)
    if ANSWERS_OLD in new:
        new = new.replace(ANSWERS_OLD, ANSWERS_NEW, 1)
        detail = "env block + MCP_CONFIG env key"
    elif HINT_OLD in new:
        new = new.replace(HINT_OLD, HINT_NEW, 1)
        detail = "env block + exercise hint"
    else:
        detail = "env block only (PART 2A shape unrecognised)"

    open(path, "w").write(new)
    changed += 1
    print(f"tuned: {rel} ({detail})")


# -----------------------------------------------------------------------------
# The copy-paste surfaces. Injecting SANDBOX_MCP_ENV into rag_agent.py is only
# half the job: the learner never types MCP_CONFIG from scratch, they copy it
# from the lesson's "Need some help?" block — and an agent asked for a hint
# reads it out of the module-2 skill. Both shipped the un-tuned dict, so the
# prose SANDBOX NOTE further up mcp.md got skipped straight past and PART 2A
# still died at EAI_AGAIN. Fix the snippets themselves, not just the note.
# -----------------------------------------------------------------------------

MD_MARKER = "[sandbox] required here"

# The solution block inside the <details class="dx-peek is-solution"> fold.
MD_OLD = (
    '        "args": ["-y", "mcp-remote", '
    'f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"]\n'
    "    }\n}\n```\n"
)
MD_NEW = (
    '        "args": ["-y", "mcp-remote", '
    'f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"],\n'
    f'        "env": SANDBOX_MCP_ENV,  # {MD_MARKER} — see the sandbox note above\n'
    "    }\n}\n```\n"
)
MD_PROSE_OLD = (
    "This configuration connects to Tavily's hosted MCP server URL. No local "
    "server installation required — just provide your API key in the URL.\n"
)
MD_PROSE_NEW = MD_PROSE_OLD + (
    "\n`SANDBOX_MCP_ENV` is already defined near the top of `rag_agent.py` "
    "(setup.sh put it there). It is needed **only in this sandbox**: the MCP "
    "stdio transport forwards just HOME/LOGNAME/PATH/SHELL/TERM/USER to the "
    "child process, so without it `npx mcp-remote` starts with no proxy "
    "configuration and fails with `getaddrinfo EAI_AGAIN mcp.tavily.com` — "
    "surfacing as `Search failed: unhandled errors in a TaskGroup "
    "(1 sub-exception)`. On the bare-metal/Brev/AI Workbench pathways you omit "
    "the `env` key.\n"
)

md_rel = os.path.join(".devx", "2-agentic-rag", "mcp.md")
md_path = os.path.join(REPO, md_rel)
if not os.path.exists(md_path):
    print(f"skip (missing): {md_rel}")
elif MD_MARKER in open(md_path).read():
    print(f"already tuned: {md_rel}")
else:
    text = open(md_path).read()
    if MD_OLD not in text:
        print(f"WARNING: solution block not found, skipping: {md_rel}")
    else:
        new = text.replace(MD_OLD, MD_NEW, 1)
        if MD_PROSE_OLD in new:
            new = new.replace(MD_PROSE_OLD, MD_PROSE_NEW, 1)
            detail = "solution block + why-note"
        else:
            detail = "solution block only"
        open(md_path, "w").write(new)
        changed += 1
        print(f"tuned: {md_rel} ({detail})")

# module-2 agent skill: what Hermes reads out when a learner asks for a hint.
# setup.sh step 7 copies .claude/skills/* into the agent library, so this must
# be patched here (before propagation) to reach the resident agent.
SKILL_MARKER = "[sandbox]"

EX_TARGET_OLD = (
    '- **Target:** `{"tavily": {"transport": "stdio", "command": "npx", '
    '"args": ["-y", "mcp-remote", '
    'f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"]}}`\n'
)
EX_TARGET_NEW = (
    '- **Target:** `{"tavily": {"transport": "stdio", "command": "npx", '
    '"args": ["-y", "mcp-remote", '
    'f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"], '
    '"env": SANDBOX_MCP_ENV}}`\n'
    "- **[sandbox] Also required here:** the `\"env\": SANDBOX_MCP_ENV` key "
    "(already defined near the top of `rag_agent.py`). Without it the MCP stdio "
    "transport drops the proxy vars, `npx mcp-remote` fails DNS, and the learner "
    "sees `Search failed: unhandled errors in a TaskGroup (1 sub-exception)`. "
    "Do NOT diagnose that as a missing key or a policy block — no OCSF line is "
    "emitted, because nothing ever reaches the L7 proxy.\n"
)

TS_OLD = (
    "- **Remote (default):** uses `npx -y mcp-remote …`, so **Node/`npx` must be "
    "available**\n"
)
TS_NEW = (
    "- **[sandbox] `Search failed: unhandled errors in a TaskGroup "
    "(1 sub-exception)`** → the most likely cause in the OpenShell sandbox is a "
    "missing `\"env\": SANDBOX_MCP_ENV` in `MCP_CONFIG`, NOT a bad key or a "
    "policy gap. The MCP stdio transport forwards only "
    "HOME/LOGNAME/PATH/SHELL/TERM/USER, so the `npx` child gets no proxy config "
    "and dies at `getaddrinfo EAI_AGAIN mcp.tavily.com`. Tell-tale: the audit "
    "log has **no** `mcp.tavily.com` line at all, allowed or denied.\n"
) + TS_OLD

for tree in (".claude", ".agents"):
    for rel, old, new_text in (
        (f"{tree}/skills/module-2/references/exercises.md", EX_TARGET_OLD, EX_TARGET_NEW),
        (f"{tree}/skills/module-2/references/troubleshooting.md", TS_OLD, TS_NEW),
    ):
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            print(f"skip (missing): {rel}")
            continue
        text = open(path).read()
        if SKILL_MARKER in text:
            print(f"already tuned: {rel}")
            continue
        if old not in text:
            print(f"WARNING: anchor not found, skipping: {rel}")
            continue
        open(path, "w").write(text.replace(old, new_text, 1))
        changed += 1
        print(f"tuned: {rel}")

print(f"done: {changed} file(s) tuned")
