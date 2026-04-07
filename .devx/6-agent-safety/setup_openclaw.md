# Set Up Your OpenClaw Agent

<img src="_static/robots/supervisor.png" alt="Setup Robot" style="float:right;max-width:300px;margin:25px;" />

Before you can secure an agent, you need an agent to secure. In this section, you'll set up **OpenClaw** — a config-first autonomous agent framework — and get a personal assistant running that you'll spend the rest of the module hardening.

<!-- fold:break -->

## What is OpenClaw?

OpenClaw is a framework for building always-on autonomous agents. Unlike LangChain graphs or CrewAI crews, OpenClaw takes a **config-first** approach:

1. Write a `SOUL.md` file that defines the agent's identity, goals, and behavior
2. Run the gateway
3. The agent is live

No Python chains. No graph definitions. No orchestration code. The agent's behavior emerges from its SOUL configuration, and it runs continuously — processing messages, monitoring feeds, and writing to its own memory files.

This simplicity is exactly what makes safety critical. There's no explicit code path to audit. The agent's behavior is shaped by a markdown file and whatever it accumulates in memory over time.

<!-- fold:break -->

## OpenClaw Architecture

Under the hood, OpenClaw has four core components:

### Heartbeat Daemon

The agent runs on a configurable heartbeat cycle. Every N minutes (default: 5), the daemon wakes the agent, feeds it new messages and context, and lets it act. Between heartbeats, the agent sleeps. This is how OpenClaw agents run 24/7 without burning compute continuously.

### Markdown Memory

OpenClaw agents maintain state in plain markdown files:

- **MEMORY.md** — Long-term facts, preferences, and context the agent accumulates
- **diary/** — Timestamped entries the agent writes after each heartbeat cycle
- **SOUL.md** — The agent's identity, goals, and behavioral rules (you write this; the agent reads it)

This memory persists across restarts. Over days and weeks, the agent builds a rich context from its own experience — which is why drift is a real concern.

### Messaging Integrations

OpenClaw connects to external channels for input and output:

- Slack, Telegram, Discord, email
- RSS feeds and webhooks
- Local CLI for testing

Messages arrive asynchronously and queue until the next heartbeat.

### SOUL.md Configuration

The SOUL file is the single source of truth for agent behavior. It defines:

- **Identity** — Who the agent is and how it communicates
- **Goals** — What the agent should accomplish
- **Rules** — Hard constraints on behavior (e.g., "never share user data")
- **Tools** — Which integrations and capabilities are enabled

<!-- fold:break -->

## Quickstart: Get Your Agent Running

Follow these steps to install OpenClaw and launch a research assistant agent.

### Step 1: Install OpenClaw and Run the Setup Wizard

OpenClaw is a Node.js application. Open a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button> and install it with the official install script — this will also launch the interactive setup wizard:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

> **Requires Node.js 22.14+** (Node 24 recommended). The script installs the `openclaw` CLI via npm. See the [official install docs](https://docs.openclaw.ai/install) for alternative methods.

<!-- fold:break -->

### Step 2: Complete the Setup Wizard

The install script automatically starts the setup wizard. If you need to re-run it later: `openclaw onboard`. Walk through the prompts as follows:

1. **Security warning** — Read the notice and confirm: **Yes**
2. **Setup mode** — Select **QuickStart** (uses default gateway settings: port 18789, loopback bind, token auth)
3. **Model/auth provider** — Select **Custom Provider**, then enter:
   - **API Base URL**: `https://integrate.api.nvidia.com/v1`
   - **API Key**: Paste your NVIDIA API key (the same one from the Secrets Manager)
   - **Endpoint compatibility**: **OpenAI-compatible**
   - **Model ID**: `nvidia/nemotron-3-super-120b-a12b`
   - **Endpoint ID**: Accept the default (`custom-integrate-api-nvidia-com`)
   - **Model alias**: Leave blank
4. **Channel** — Select **Skip for now** (we'll use the CLI and NemoClaw Client for this module)
5. **Web search** — Select **Tavily Search** (uses your `TAVILY_API_KEY` environment variable if set, otherwise skip)
6. **Skills** — Select **No** (not needed for this module)
7. **Hooks** — Select **Skip for now**

The wizard writes your configuration to `~/.openclaw/openclaw.json` and creates the agent workspace at `~/.openclaw/workspace/`.

After the wizard completes, **approve the CLI device pairing** so the agent can receive messages. OpenClaw requires each CLI "device" to be explicitly approved before it can talk to the gateway:

```bash
openclaw devices approve --latest
```

> If you see "pairing required" errors later (e.g., after restarting the gateway), re-run `openclaw devices approve --latest` to approve the latest pending device.

<!-- fold:break -->

### Step 3: Create Your SOUL.md

The wizard created a default workspace. Now give your agent its identity by editing `~/.openclaw/workspace/SOUL.md`:

```markdown
# Research Assistant

## Identity
You are a research assistant that monitors technical feeds, summarizes papers, and creates daily briefings.

## Goals
- Monitor RSS feeds for new papers and articles on AI safety and agent architectures
- Summarize key findings in clear, concise language
- Maintain a running log of research themes in MEMORY.md
- Create daily briefing documents in /workspace/

## Rules
- Never share user data or credentials
- Never execute commands outside your workspace directory
- Never modify your own SOUL.md
- Always cite sources when summarizing research
- When uncertain, say so rather than fabricating information

## Tools
- rss: Monitor RSS feeds
- file: Read and write files in /workspace/
- search: Web search for follow-up research
```

<!-- fold:break -->

### Step 4: Configure the Heartbeat

Create a `HEARTBEAT.md` file at `~/.openclaw/workspace/HEARTBEAT.md`. The heartbeat file uses **plain English** — the gateway reads it as natural language instructions for what to do on each cycle:

```markdown
# Heartbeat

Every 5 minutes, check RSS feeds for new papers on AI safety and agent architectures.
Summarize any new findings and append them to MEMORY.md.
Create a daily briefing document in /workspace/ at the end of each day.
```

By default, the heartbeat runs every 30 minutes. You can adjust the interval in `~/.openclaw/openclaw.json`.

### Step 5: Start the Gateway

In this workshop environment, systemd user services aren't available, so the gateway won't auto-start as a daemon. Start it manually in a terminal:

```bash
export PATH="$HOME/.npm-global/bin:$PATH" && openclaw gateway run
```

Open a new <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button> and verify it's running:

```bash
openclaw gateway status
```

> Check for any configuration issues with ``openclaw doctor``. OpenClaw also provides a built-in UI with ``openclaw dashboard``, but we will use the NemoClaw Client app built for this workshop. 

<!-- fold:break -->

### Step 6: Test With a Message

With the gateway running in a separate terminal, open an interactive chat session:

```bash
openclaw tui
```

This opens a terminal UI where you can chat with your agent directly. Try asking:

> Hi, how are you?

The agent should respond based on its SOUL configuration, mentioning it's role as an assistant and it's ability to learn and self-evolve. It should also begin writing to MEMORY.md.

For a single non-interactive message (useful for scripting, testing, etc.), you may also use:

```bash
openclaw agent --agent main -m "Hi, how are you?"
```

You can also use the <button onclick="launch('NemoClaw Client');"><i class="fa-solid fa-rocket"></i> NemoClaw Client</button> for a browser-based chat interface. The client connects to your running gateway automatically, or falls back to a mock agent for testing.

<!-- fold:break -->

## Meet Your Agent

With the agent running, open the <button onclick="launch('NemoClaw Client');"><i class="fa-solid fa-rocket"></i> NemoClaw Client</button> or continue using the CLI. Take a moment to observe how the agent operates:

1. **Check memory** — Look at the `MEMORY.md` file in your workspace. After the first heartbeat, the agent will have written its initial context.

2. **Check the diary** — Look in the `diary/` directory. Each heartbeat cycle produces a timestamped entry describing what the agent did.

3. **Send a few messages** — Ask the agent to summarize a topic or check its feeds. Watch how it incorporates information into memory over successive heartbeats.

4. **Watch for drift** — After 3-4 heartbeat cycles, compare the current MEMORY.md to the initial version. The agent's context is already evolving.

> The agent works. It responds to messages, writes to memory, and operates autonomously on its heartbeat cycle. But it has no guardrails beyond the soft rules in SOUL.md. A prompt injection in an RSS feed, a PII-laden email, or a malicious message could all compromise it.

<!-- fold:break -->

<details>
<summary><strong>Troubleshooting</strong></summary>

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `openclaw: command not found` | Not installed or not in PATH | Re-run the install script: `curl -fsSL https://openclaw.ai/install.sh \| bash` |
| `Node.js version error` | Node.js too old | Install Node.js 22.14+ (Node 24 recommended) |
| `Gateway not starting` | Port conflict or config issue | Run `openclaw doctor` for diagnostics |
| `Model error: 401` | API key not set or invalid | Re-run `openclaw onboard` to reconfigure your API key |
| `No messages received` | No integrations configured | Use `openclaw tui` or `openclaw agent --agent main -m "message"` for local testing |

</details>

<details>
<summary><strong>Can't install OpenClaw? Use the mock agent instead.</strong></summary>

If you're unable to install OpenClaw in your environment (e.g., Node.js not available, network restrictions), the exercise code includes a **mock agent** that simulates the same interface. The mock agent is deliberately leaky — it responds to some adversarial prompts in unsafe ways so that the safety evaluation exercises can detect and report violations.

The mock agent is loaded automatically when OpenClaw is not available:

```python
from openclaw_wrapper import create_openclaw_agent_fn

agent_fn = create_openclaw_agent_fn()
# If OpenClaw is installed and running, connects to the live agent
# Otherwise, falls back to the mock agent

response = agent_fn("What can you help me with?")
```

All exercises work identically with both the live agent and the mock. The mock simply makes the safety gaps more visible.

</details>

<!-- fold:break -->

## What's Next

Your agent works. But right now, the only thing standing between it and unsafe behavior is a markdown file with soft rules.

In the next section, you'll learn how to enforce constraints at the **kernel level** — restrictions the agent cannot override, even with arbitrary code execution.

> Head to [Enforced Constraints with OpenShell](enforced_constraints) to lock it down.
