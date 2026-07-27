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

print(f"done: {changed} file(s) tuned")
