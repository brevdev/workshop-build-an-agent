# Module 5 Troubleshooting — tutor reference

**Triage first.** Environment/runtime (give direct fixes), exercise blank (guide — see
`exercises.md`), or security reasoning (teaching moment — see `concepts.md`)? Runtime fixes
below are fair to give directly. **Don't run the agent/backend for the learner** —
diagnose, then let them act.

## The demo backend (`.venv` + uvicorn)
`deep_agent.py` is tested/run from the demo app, which has its **own virtualenv**:
- Dry-run: `cd demo/backend && source .venv/bin/activate && python ../../code/5-deep-agents/deep_agent.py`.
- Backend server: `cd demo/backend && source .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8000`.
- `ModuleNotFoundError: deepagents` (or `langchain_nvidia_ai_endpoints`) → the demo `.venv`
  isn't activated, or deps aren't installed there. Activate it first.
- The **Deep Agents Client** tile (launcher) is the frontend; "can't connect" → the backend
  isn't running on :8000, or wasn't restarted after copying `deep_agent.py` → `demo/backend/agent.py`.

## Using your code in the Client
The Client runs `demo/backend/agent.py`, **not** `code/5-deep-agents/deep_agent.py`. To use
your completed version in the UI you must **copy your file's contents into
`demo/backend/agent.py`** and restart the backend. (The dry-run, however, runs your file
directly.)

## Docker sandbox
- Sandbox mode uses `DockerSandboxBackend` (from the `docker_sandbox` module) → a
  `python:3.11-slim` container, no host mounts, 512 MB / 1 CPU, auto-cleanup. It needs a
  working **Docker** (the workshop provides the host docker socket via the `/var/host-run/`
  mount; see the `setup-workshop` skill).
- `_build_backend` **falls back to local** if the Docker sandbox fails to start (prints a
  WARNING). So "sandbox didn't isolate" can mean Docker was unavailable and it silently fell
  back — check the log for the fallback message and that Docker works (`docker ps`).
- First sandbox start pulls `python:3.11-slim` (one-time). Slow first run is normal.

## Models
- `MODEL_MAP`: `nemotron`→`nvidia/nemotron-3-super-120b-a12b`, `llama`→`meta/llama-3.3-70b-instruct`,
  `deepseek`→`deepseek-ai/deepseek-r1-0528`, `claude`→llama fallback. All via `ChatNVIDIA` (NIM).
- **401/auth** → `NVIDIA_API_KEY` missing/invalid in `secrets.env` (repo root).
- **404 / model-not-found** → that catalog id changed; confirm on build.nvidia.com. Deep
  agents need a **tool-calling** model — don't swap in one that can't emit tool calls.

## HITL interrupts
- `interrupt_on=INTERRUPT_TOOLS` (`write_file`/`edit_file`/`execute`) pauses those tools for
  human approve/edit/reject. In the Client the user is prompted; programmatically the graph
  raises an interrupt that must be resumed. "Agent hangs after proposing a write/exec" → it's
  *waiting for approval*, by design — approve/reject in the UI.

## Web search / Tavily
- `_build_extra_tools` only adds Tavily when `"websearch"` is selected **and**
  `TAVILY_API_KEY` is set — otherwise it's silently skipped (and the agent has no web tool).
  Missing search results → check the key and that the tool was selected.

## Workspace & file paths
- File tools require **absolute** paths. Local workspace: `/tmp/deepagent_workspace`
  (seeded with fake demo files). Inside a sandbox: `/workspace`. "File not found" / writes
  in the wrong place → relative path, or wrong workspace for the sandbox mode in use.

## The fake demo files (not an incident)
`/tmp/deepagent_workspace/{passwords.txt, ssn_records.txt}` are **seeded by `postBuild` on
purpose** for the no-sandbox security demo — they are fabricated props, not real secrets. If
a learner is alarmed the agent "leaked passwords," explain: that's the *point* of the
un-sandboxed demo; switching to the Docker sandbox makes them invisible. Don't gratuitously
print them.

## deepagents library
- Imports: `from deepagents import create_deep_agent`; backends `from deepagents.backends
  import FilesystemBackend, LocalShellBackend, CompositeBackend`. Import errors → wrong
  venv / version (`deepagents>=0.3.11` in `requirements.txt`).
- It returns a compiled **LangGraph** graph; `.ainvoke({"messages": [...]}, config={"configurable": {"thread_id": ...}})`. A `thread_id` is needed for the checkpointer/memory.

## Recursion / runaway
- A deep agent can loop (plan→act→observe many times). If it spins, that's a rate-limiting/
  recursion concern from the security lesson — set recursion limits/timeouts; don't just let
  it run unbounded.
