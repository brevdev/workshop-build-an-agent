# Set Up the Agent Builder

<img src="_static/robots/plumber.png" alt="Setup Robot" style="float:right;max-width:300px;margin:25px;" />

Before we start building, let's get the **Deep Agent Builder UI** running. This is the interactive demo you'll use to test your agent throughout this module — pick a model, drag-and-drop tools, click Build, and chat in real-time.

The demo lives in the `demo/` folder and has two parts: a **React frontend** and a **FastAPI backend**.

<!-- fold:break -->

## Prerequisites

Make sure you have these installed:

| Tool | Version | Check |
|---|---|---|
| **Node.js** | 18+ | `node --version` |
| **Python** | 3.11+ | `python3.11 --version` |
| **Docker** | Any (optional, for sandbox mode) | `docker --version` |

You should also have your API keys ready from the [Secrets](secrets) page:
- **NVIDIA API Key** (`nvapi-...`)
- **Tavily API Key** (`tvly-...`)

<!-- fold:break -->

## Step 1: Backend Setup

Open a terminal and set up the Python backend:

```bash
cd demo/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This installs `deepagents`, `fastapi`, `langchain`, and all other dependencies. It should take about a minute.

<!-- fold:break -->

### Configure API Keys

Create a `.env` file with your keys:

```bash
cp .env.example .env
```

Then edit `.env` and fill in your actual keys:

```
NVIDIA_API_KEY=nvapi-your-key-here
TAVILY_API_KEY=tvly-your-key-here
```

> **Tip**: If you already set up secrets in the Secrets Manager, your keys may already be available as environment variables. You can check with `echo $NVIDIA_API_KEY`.

<!-- fold:break -->

### Start the Backend

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify it's working:

```bash
curl http://localhost:8000/api/health
# → {"status":"ok","service":"deep-agent-backend","sessions":0}
```

Leave this terminal running.

<!-- fold:break -->

## Step 2: Frontend Setup

Open a **second terminal** and set up the React frontend:

```bash
cd demo
npm install
npm run dev
```

You should see:

```
VITE v7.x.x  ready in XXms

➜  Local:   http://localhost:5173/
```

<!-- fold:break -->

## Step 3: Open the UI

<img src="_static/robots/magician.png" alt="UI Robot" style="float:right;max-width:250px;margin:15px;" />

Open your browser to:

**http://localhost:5173**

You'll see the **LLM Picker** — a robot in the center with model cards around it.

<!-- fold:break -->

## UI Walkthrough

The demo has four phases:

### 1. Pick Your Model

Click a model card to select it. **Nemotron** (NVIDIA's flagship) is recommended — it handles deepagents' middleware stack reliably. The model's brand color will theme the entire UI.

### 2. Build Your Agent

After picking a model, you'll see three panels:

| Panel | What It Does |
|---|---|
| **Skill Palette** (left) | Available tools and skills — drag them onto the agent |
| **Agent Builder** (center) | Drop zone — shows what's been added to your agent |
| **Settings** (right) | Sandbox mode toggle and other configuration |

**Drag tools** from the left palette onto the center area:
- 🌐 **Web Search** — Real-time internet search via Tavily
- 📁 **File I/O** — Read, write, edit, search files
- 💻 **Shell Execution** — Run commands and scripts
- ⚡ **Superpowers** — TDD and debugging methodology
- And more...

### 3. Click Build

When you've added at least one tool, the **Build** button lights up. Click it to see the build animation — the frontend sends your configuration to the backend, which assembles the deep agent.

### 4. Chat

Once built, you're in the **chat interface**:
- Type messages and see real-time streaming responses
- **Tool traces** appear inline — see which tools the agent calls, their inputs, outputs, and timing
- The **Tool Calls panel** on the right shows the full execution log
- **Suggested questions** appear based on your enabled tools

Try these to verify everything works:
- *"List all files in the workspace"* — tests File I/O
- *"Write a hello world Python script and run it"* — tests File I/O + Shell
- *"What's in the news today?"* — tests Web Search

<!-- fold:break -->

## Optional: Docker for Sandbox Mode

If you have Docker installed, you can enable **Sandbox Mode** in the Settings panel. This runs the agent's tools inside an isolated Docker container — the agent can't see your host files.

For Colima users, add your Docker socket to `.env`:

```bash
echo "DOCKER_HOST=unix://$HOME/.colima/default/docker.sock" >> demo/backend/.env
```

Pull the sandbox image (one-time):

```bash
docker pull python:3.11-slim
```

Then toggle Sandbox Mode ON in the Settings panel when building your agent.

<!-- fold:break -->

## Troubleshooting

| Problem | Fix |
|---|---|
| Backend won't start | Check `.env` has valid API keys. Run `python -c "from server import app; print('OK')"` to test imports. |
| Frontend shows blank page | Run `npx tsc --noEmit` to check for TypeScript errors. |
| "DEGRADED function" error | NVIDIA NIM API may be temporarily down. Wait a few minutes and retry. |
| Agent times out | The NIM endpoint might be slow. Try again — first calls can take longer. |
| Sandbox mode hangs | Make sure Docker/Colima is running: `docker ps` should work. |

<!-- fold:break -->

## Ready?

With both terminals running, you should have:
- ✅ Backend at `http://localhost:8000`
- ✅ Frontend at `http://localhost:5173`

> Head to [Build a Deep Agent](build_deep_agents) to start the exercises!
