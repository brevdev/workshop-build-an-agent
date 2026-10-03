# Deep Agent Builder

Module 5's interactive builder uses React, FastAPI, and [deepagents](https://github.com/langchain-ai/deepagents). Pick a model, add tools and instructions, then chat with your agent and review its tool calls.

## Start in the workshop

Save your NVIDIA key in **Workshop Utilities → Secrets Manager**. Add a Tavily key if you want Web Search. The backend reads the project's `secrets.env`.

From the project root, start the backend:

```bash
cd demo/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

In another terminal, starting at the project root:

```bash
cd demo
npm install
```

Open **Deep Agents Client** from the JupyterLab launcher. For standalone frontend development, run `npm run dev` and open the URL it prints.

The backend uses the reference implementation while Module 5's exercises have blanks. After completing them, restart the backend to load your implementation. It prints which file it loaded.

## Models, tools, and approvals

The picker offers Nemotron Super and Nemotron Lightning, configured in [`models.json`](../code/workshop_support/models.json). Add tools with their **Add** button or drag them onto the agent.

| Selection | What it enables |
|---|---|
| File I/O | Read, write, edit, list, and search workspace files |
| Shell Execution | Run commands; local mode runs as the backend's user |
| Web Search | Search through Tavily from the application |
| RAG | Retrieve and rerank the supplied IT knowledge base |
| Skills | Add the selected methodology to the system prompt |

Planning and delegation are built in. File access remains disabled unless selected, including for delegated work. Shell access can also read and write files through commands. The client asks for approval before writes, edits, and execution. After building, expand **Session capabilities** to inspect the actual tool set and execution mode.

## Sandbox Mode

Docker must be available; the backend creates a `python:3.11-slim` container per sandboxed session. If it cannot start the container, agent creation fails.

| | Local mode | Sandbox Mode |
|---|---|---|
| File tools | File-only: virtual `/`; with Shell Execution: real paths under `/tmp/deepagent_workspace` (or `DEEPAGENT_WORKSPACE`) | Paths under `/workspace` in the container |
| Shell tools | Backend user; the working directory is not a jail | Nonroot container process |
| Container limits | Not applicable | 512 MiB memory, 1 CPU, 64 processes, 60-second commands |
| Host mounts / container network | Host permissions apply | No host mounts or network |
| Cleanup | Local workspace remains | Resetting the session removes its container |

Web Search and RAG run in the application, outside the execution container. Tool outputs can enter the hosted model's context. Docker shares the host kernel; it is not a separate machine.

## Backend files

| File | Purpose |
|---|---|
| `backend/server.py` | Session API and streamed responses |
| `backend/agent.py` | Loads the learner or reference factory |
| `../code/5-deep-agents/deep_agent.py` | Module 5 exercises and agent factory |
| `backend/capabilities.py` | Tool and backend permission checks |
| `backend/docker_sandbox.py` | Container lifecycle, file transfer, and execution |
| `backend/skills/` | Instruction presets added to the system prompt |

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Backend readiness |
| GET | `/api/models` | Configured model choices |
| POST | `/api/agent` | Create a session and return its capabilities |
| DELETE | `/api/agent/{id}` | Delete the session and its container |
| POST | `/api/agent/{id}/chat` | Stream a response |
| POST | `/api/agent/{id}/approve` | Approve or reject a pending tool call |
