# Set Up the Agent Builder

<img src="_static/robots/plumber.png" alt="Setup Robot" style="float:right;max-width:300px;margin:25px;" />

Before we start building, let's get the **Deep Agent Builder UI** running. This is the interactive demo you'll use to test your agent throughout this module — pick a model, drag-and-drop tools, click Build, and chat in real-time.

The demo lives in the `demo/` folder and has two parts: a **React frontend** and a **FastAPI backend**.

<!-- fold:break -->

## Step 1: Backend Setup

Open a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> and set up the Python backend:

```bash
cd demo/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This installs `deepagents`, `fastapi`, `langchain`, and all other dependencies. It should take about a minute.

<!-- fold:break -->

### Start the Backend

> **Important:** If you already set up secrets in the Secrets Manager, your API keys may already be available as environment variables. You can check with `echo $NVIDIA_API_KEY`.

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Leave this server running and verify it's working from another <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button>:

```bash
curl http://localhost:8000/api/health
# → {"status":"ok","service":"deep-agent-backend","sessions":0}
```

<!-- fold:break -->

## Step 2: Frontend Setup

In a different <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button>, set up the React frontend:

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

The demo has four phases. Click on each to learn more.

<details>
<summary><strong>1. Pick Your Model</strong></summary>

Click a model card to select it. **Nemotron** (NVIDIA's flagship) is recommended — it handles deepagents' middleware stack reliably. The model's brand color will theme the entire UI.

</details>

<details>
<summary><strong>2. Build Your Agent</strong></summary>

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

</details>

<details>
<summary><strong>3. Click Build</strong></summary>

When you've added at least one tool, the **Build** button lights up. Click it to see the build animation — the frontend sends your configuration to the backend, which assembles the deep agent.

</details>

<details>
<summary><strong>4. Chat with the Agent</strong></summary>

Once built, you're in the **chat interface**:
- Type messages and see real-time streaming responses
- **Tool traces** appear inline — see which tools the agent calls, their inputs, outputs, and timing
- The **Tool Calls panel** on the right shows the full execution log
- **Suggested questions** appear based on your enabled tools

Try these to verify everything works:
- *"List all files in the workspace"* — tests File I/O
- *"Write a hello world Python script and run it"* — tests File I/O + Shell
- *"What's in the news today?"* — tests Web Search

</details>

<!-- fold:break -->

<details>
<summary><strong>5. (Optional) Docker for Sandbox Mode</strong></summary>

If you have Docker installed, you can enable **Sandbox Mode** in the Settings panel. This runs the agent's tools inside an isolated Docker container — the agent can't see your host files. 

For Colima users, add your Docker socket to `.env`:

```bash
echo "DOCKER_HOST=unix://$HOME/.colima/default/docker.sock" >> demo/backend/.env
```

Pull the sandbox image (one-time):

```bash
docker pull python:3.11-slim
```

Then toggle Sandbox Mode ON in the Settings panel when building your agent. We'll talk about why this mode is important shortly. 

</details>

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
