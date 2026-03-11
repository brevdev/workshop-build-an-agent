# Deep Agent Builder — NVIDIA GTC 2026 Demo

A full-stack AI agent builder where users pick a foundation model, drag-and-drop tools and skills onto an agent, and chat with it in real-time. Built on [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) with NVIDIA NIM models.

**Sandbox Mode** runs agent tools inside real Docker containers — complete filesystem isolation.

## Quick Start

### Prerequisites

- **Node.js 18+**
- **Python 3.11+** (required by deepagents)
- **Docker** — via [Docker Desktop](https://www.docker.com/products/docker-desktop/) or [Colima](https://github.com/abiosoft/colima) (for sandbox mode)
- **NVIDIA API key** — free from [build.nvidia.com](https://build.nvidia.com)
- **Tavily API key** (optional, for web search) — free from [tavily.com](https://tavily.com)

### 1. Clone

```bash
git clone https://github.com/PicoNVIDIA/DeepAgentsDemo.git
cd DeepAgentsDemo
```

### 2. Backend Setup

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create your `.env` file with API keys:

```bash
cat > .env << 'EOF'
NVIDIA_API_KEY=nvapi-your-key-here
TAVILY_API_KEY=tvly-your-key-here
EOF
```

**For Sandbox Mode** — add your Docker socket path:

```bash
# Colima users:
echo "DOCKER_HOST=unix://$HOME/.colima/default/docker.sock" >> .env

# Docker Desktop users (usually auto-detected):
# echo "DOCKER_HOST=unix:///var/run/docker.sock" >> .env
```

Pull the sandbox image (one-time):

```bash
docker pull python:3.11-slim
```

Start the backend:

```bash
uvicorn server:app --host 127.0.0.1 --port 8000
```

### 3. Frontend Setup (new terminal)

```bash
cd DeepAgentsDemo
npm install
npm run dev
```

### 4. Open

```
http://localhost:5173
```

Pick a model → drag tools onto the agent → click Build → chat!

## Sandbox Mode

Toggle **Sandbox Mode** ON in the Settings panel (right side of the builder). When enabled:

- A real `python:3.11-slim` **Docker container** is created per agent session
- All file I/O (`read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`) runs **inside the container**
- All shell execution (`execute`) runs **inside the container**
- The container has **no host mounts** — the agent cannot see your filesystem
- Container is automatically destroyed when the session ends

### Sandbox vs Local

| | Sandbox OFF | Sandbox ON |
|---|---|---|
| **Where tools run** | Your machine (`/tmp/deepagent_workspace`) | Docker container (`/workspace`) |
| **File access** | Full local filesystem | Isolated container filesystem |
| **Sensitive data** | Visible to agent | Invisible — doesn't exist |
| **Container** | None | `python:3.11-slim` with 512MB RAM, 1 CPU |
| **Cleanup** | Manual | Auto-destroyed on session end |

### Requirements for Sandbox Mode

1. Docker daemon running (`docker ps` should work)
2. `DOCKER_HOST` set in `backend/.env` (see setup above)
3. `python:3.11-slim` image pulled

If Docker isn't available, the backend falls back to local execution with a warning.

## Features

### LLM Picker
Choose your foundation model — each has a brand color that themes the entire UI:
- **Nemotron** (NVIDIA) — `nvidia/nemotron-3-super-120b-a12b` with variant picker (General, Finance, Code, Legal)
- **Llama** (Meta) — `meta/llama-3.3-70b-instruct`
- **DeepSeek** — `deepseek-ai/deepseek-r1-0528`
- **Claude** (Anthropic) — fallback to Llama

### Tools (drag-and-drop)
| Tool | What it does | Sandboxable |
|---|---|---|
| 🌐 **Web Search** | Real-time internet search via Tavily | ✅ |
| 📁 **File I/O** | Read, write, edit files + ls, glob, grep | ✅ |
| 💻 **Shell Execution** | Run shell commands and Python scripts | ✅ |

### Skills (drag-and-drop)
| Skill | What it does |
|---|---|
| ⚡ **Superpowers** | TDD, planning & debugging methodology ([obra/superpowers](https://github.com/obra/superpowers)) |
| 🟩 **cuDF** | GPU-accelerated DataFrames (NVIDIA RAPIDS) |

### Human-in-the-Loop
When the agent wants to write a file, edit code, or run a command, it pauses and asks for your approval before executing.

### Live Tool Traces
See which tools the agent calls in real-time — inline traces in chat + a dedicated tool calls panel.

## Architecture

```
React Frontend (Vite + TypeScript)
  → LLM Picker (model selection + Nemotron variants)
  → Skill Builder (drag & drop)
  → Settings Panel (Sandbox Mode toggle)
  → Build Animation
  → Chat (SSE streaming + Markdown rendering)
  → Tool Calls Panel
  → Human-in-the-loop approval UI

FastAPI Backend (Python)
  → langchain-ai/deepagents (LangGraph agent)
  → NVIDIA NIM models
  → Session management (in-memory)
  → SSE streaming
  → Checkpointer for HITL interrupt/resume
  → DockerSandboxBackend (real Docker containers)
```

### How the Build Flow Works

1. **UI** builds specs: `{ model_id, skill_ids, hitl_enabled, sandbox_map }`
2. **Frontend** sends `POST /api/agent` with the specs
3. **Backend** (`server.py`) calls `create_agent()` in `agent.py`
4. **Agent factory** resolves each spec into real components:
   - `model_id` → NVIDIA NIM model
   - `skill_ids` → tools (Tavily, file ops, shell) + skill files (markdown → system prompt)
   - `hitl_enabled` → interrupt config + checkpointer
   - `sandbox_map` → `DockerSandboxBackend` (Docker container) or `LocalShellBackend` (local)
5. Returns a `session_id` — all chat goes through `POST /api/agent/{id}/chat`

### Backend Files

| File | Purpose |
|---|---|
| `server.py` | FastAPI routes, SSE streaming, session management |
| `agent.py` | Agent factory — builds models, tools, backends, prompts |
| `docker_sandbox.py` | Docker-based sandbox backend (implements `SandboxBackendProtocol`) |
| `skills/` | Markdown skill files injected into system prompts |

## Adding New Skills

Drop a `.md` file in `backend/skills/`, then:

1. Add the mapping in `backend/agent.py` → `_load_skill_content()`:
   ```python
   skill_files = {
       "superpowers": "superpowers.md",
       "cudf": "cudf.md",
       "your_skill": "your_skill.md",  # ← add here
   }
   ```

2. Add the frontend entry in `src/data/skills.ts`:
   ```typescript
   {
     id: 'your_skill',
     name: 'Your Skill',
     description: 'What it does',
     category: 'skills',
     icon: '🎯',
     sandboxable: false,
   },
   ```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/agent` | Create agent session (accepts `sandbox_map`) |
| `DELETE` | `/api/agent/{id}` | Delete session (destroys Docker container if sandboxed) |
| `POST` | `/api/agent/{id}/chat` | Chat (SSE streaming) |
| `POST` | `/api/agent/{id}/approve` | Approve/reject interrupted tool call |

## Tech Stack

- **Frontend**: React 19, Vite, TypeScript, Framer Motion, @dnd-kit, react-markdown
- **Backend**: FastAPI, deepagents, LangGraph, NVIDIA NIM, Tavily, SSE
- **Sandbox**: Docker (`python:3.11-slim` containers via Docker SDK)
- **Styling**: NVIDIA Kaizen Design System tokens, CSS variables for dynamic theming
