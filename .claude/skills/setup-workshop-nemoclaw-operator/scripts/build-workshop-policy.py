#!/usr/bin/env python3

"""Compose the workshop policy: live sandbox policy + the workshop additions.

Usage:  build-workshop-policy.py <live.yaml> <apply.yaml>

Reads the captured live policy (metadata header already stripped), adds the
workshop blocks from references/policy-blocks.md, and writes the apply file.
Idempotent: blocks already present are left untouched. Self-verifies that the
result equals the input plus exactly the intended additions and nothing else;
exits non-zero on any structural surprise. Human-readable rationale for every
block: references/policy-blocks.md.
"""

from __future__ import annotations

import copy
import sys

import yaml

PY_BINARIES = [
    {"path": "/usr/bin/python3"},
    {"path": "/usr/bin/python3.13"},
    {"path": "/opt/hermes/.venv/bin/python"},
    {"path": "/usr/bin/curl"},
]

def _ep(host: str, rules: list) -> dict:
    return {"host": host, "port": 443, "protocol": "rest",
            "enforcement": "enforce", "rules": rules}

def _allow(method: str, path: str) -> dict:
    return {"allow": {"method": method, "path": path}}

WORKSHOP_BLOCKS: dict = {
    "github_git_clone": {
        "name": "github-git-clone",
        "endpoints": [_ep("github.com", [
            _allow("GET", "/brevdev/workshop-build-an-agent/info/refs"),
            _allow("POST", "/brevdev/workshop-build-an-agent/git-upload-pack"),
            _allow("GET", "/brevdev/workshop-build-an-agent.git/info/refs"),
            _allow("POST", "/brevdev/workshop-build-an-agent.git/git-upload-pack"),
        ])],
        "binaries": [
            {"path": "/usr/bin/git"},
            {"path": "/usr/lib/git-core/git-remote-https"},
            {"path": "/usr/lib/git-core/git-remote-http"},
            {"path": "/usr/bin/curl"},
        ],
    },
    "pypi_install": {
        "name": "pypi-install",
        "endpoints": [
            _ep("pypi.org", [_allow("GET", "/**")]),
            _ep("files.pythonhosted.org", [_allow("GET", "/**")]),
        ],
        "binaries": [{"path": "/usr/local/bin/uv"}] + copy.deepcopy(PY_BINARIES),
    },
    "tavily_search": {
        "name": "tavily-search",
        "endpoints": [_ep("api.tavily.com",
                          [_allow("POST", "/search"), _allow("POST", "/extract")])],
        "binaries": copy.deepcopy(PY_BINARIES),
    },
    "langsmith_api": {
        "name": "langsmith-api",
        "endpoints": [_ep("api.smith.langchain.com", [
            _allow(m, "/**") for m in ("GET", "POST", "PATCH", "PUT", "DELETE")
        ])],
        "binaries": copy.deepcopy(PY_BINARIES),
    },
    "nvidia_retrieval": {
        "name": "nvidia-retrieval",
        "endpoints": [_ep("ai.api.nvidia.com", [_allow("POST", "/v1/retrieval/**")])],
        "binaries": copy.deepcopy(PY_BINARIES),
    },
    "npm_install": {
        "name": "npm-install",
        "endpoints": [_ep("registry.npmjs.org", [_allow("GET", "/**")])],
        "binaries": [{"path": "/usr/local/bin/node"}],
    },
    "mcp_tavily": {
        "name": "mcp-tavily",
        "endpoints": [_ep("mcp.tavily.com", [
            _allow("GET", "/**"), _allow("POST", "/**"), _allow("DELETE", "/**")
        ])],
        "binaries": [{"path": "/usr/local/bin/node"}],
    },
    "tiktoken_encodings": {
        "name": "tiktoken-encodings",
        "endpoints": [_ep("openaipublic.blob.core.windows.net",
                          [_allow("GET", "/encodings/**")])],
        "binaries": copy.deepcopy(PY_BINARIES),
    },
}

RANKING_RULE = _allow("POST", "/v1/ranking")
FS_READ_ONLY = "/sys/fs/cgroup"
FS_READ_WRITE = "/dev/pts"

def compose(live: dict) -> dict:
    """Return live + workshop additions (idempotent, input untouched)."""
    doc = copy.deepcopy(live)
    np = doc["network_policies"]
    for key, block in WORKSHOP_BLOCKS.items():
        np.setdefault(key, copy.deepcopy(block))
    for ep in np.get("nvidia", {}).get("endpoints", []):
        if RANKING_RULE not in ep["rules"]:
            ep["rules"].append(copy.deepcopy(RANKING_RULE))
    fs = doc["filesystem_policy"]
    if FS_READ_ONLY not in fs["read_only"]:
        fs["read_only"].append(FS_READ_ONLY)
    if FS_READ_WRITE not in fs["read_write"]:
        fs["read_write"].append(FS_READ_WRITE)
    return doc

def verify(live: dict, doc: dict) -> list[str]:
    """Structural check: doc == live + exactly the intended additions."""
    errs = []
    lnp, dnp = live["network_policies"], doc["network_policies"]
    if set(lnp) - set(dnp):
        errs.append(f"blocks removed: {sorted(set(lnp) - set(dnp))}")
    if set(dnp) - set(lnp) - set(WORKSHOP_BLOCKS):
        errs.append(f"unexpected new blocks: {sorted(set(dnp) - set(lnp) - set(WORKSHOP_BLOCKS))}")
    for k in lnp:
        if k == "nvidia":
            expect = copy.deepcopy(lnp[k])
            for ep in expect["endpoints"]:
                if RANKING_RULE not in ep["rules"]:
                    ep["rules"].append(copy.deepcopy(RANKING_RULE))
            if dnp.get(k) != expect:
                errs.append("nvidia block differs beyond the /v1/ranking rules")
        elif dnp.get(k) != lnp[k]:
            errs.append(f"pre-existing block modified: {k}")
    fse = copy.deepcopy(live["filesystem_policy"])
    if FS_READ_ONLY not in fse["read_only"]:
        fse["read_only"].append(FS_READ_ONLY)
    if FS_READ_WRITE not in fse["read_write"]:
        fse["read_write"].append(FS_READ_WRITE)
    if doc["filesystem_policy"] != fse:
        errs.append("filesystem_policy differs beyond the pts/cgroup grants")
    for key in set(live) | set(doc):
        if key not in ("network_policies", "filesystem_policy") and live.get(key) != doc.get(key):
            errs.append(f"top-level key differs: {key}")
    return errs

def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    live = yaml.safe_load(open(sys.argv[1]))
    doc = compose(live)
    errs = verify(live, doc)
    if errs:
        for e in errs:
            print("FAIL:", e, file=sys.stderr)
        return 1
    yaml.safe_dump(doc, open(sys.argv[2], "w"), sort_keys=False, default_flow_style=False)
    added = sorted(set(doc["network_policies"]) - set(live["network_policies"]))
    hosts = sorted({ep["host"] for k in added for ep in doc["network_policies"][k]["endpoints"]})
    print(f"wrote {sys.argv[2]}: +{len(added)} blocks ({', '.join(added) or 'none — already present'})")
    if hosts:
        print("opens exactly:", ", ".join(hosts))
    return 0

if __name__ == "__main__":
    sys.exit(main())
