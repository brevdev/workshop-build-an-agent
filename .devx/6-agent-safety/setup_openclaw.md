# Set Up Your OpenClaw Agent

<img src="_static/robots/supervisor.png" alt="Setup Robot" style="float:right;max-width:300px;margin:25px;" />

Before you can secure an agent, you need an agent to secure. In this section, you'll set up **OpenClaw** — a config-first autonomous agent framework — and get a research assistant running that you'll spend the rest of the module hardening.

<!-- fold:break -->

## What is OpenClaw?

OpenClaw is a framework for building always-on autonomous agents. Unlike LangChain graphs or CrewAI crews, OpenClaw takes a **config-first** approach:

1. Write a `SOUL.md` file that defines the agent's identity, goals, and behavior
2. Run `openclaw start`
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

### Step 1: Install OpenClaw

```bash
pip install openclaw
```

This installs the OpenClaw CLI and Python SDK.

### Step 2: Create Your SOUL.md

Create a file called `SOUL.md` in your workspace with the following content:

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

### Step 3: Configure the Heartbeat

Create a `HEARTBEAT.md` file to set the agent's cycle frequency:

```markdown
# Heartbeat Configuration

interval: 5m
max_tokens_per_cycle: 4096
model: nvidia/nemotron-3-super-120b-a12b
```

This tells OpenClaw to wake the agent every 5 minutes, cap each cycle at 4096 tokens, and use Nemotron for reasoning.

### Step 4: Start the Agent

```bash
openclaw start
```

You should see output similar to:

```
[OpenClaw] Agent "research-assistant" starting...
[OpenClaw] SOUL loaded: Research Assistant
[OpenClaw] Heartbeat interval: 5m
[OpenClaw] Listening for messages...
[OpenClaw] Agent is live.
```

### Step 5: Verify the Agent is Running

```bash
openclaw status
```

Expected output:

```
Agent: research-assistant
Status: running
Uptime: 0m 12s
Heartbeats: 1
Memory size: 0.2 KB
```

<!-- fold:break -->

### Step 6: Test With a Message

Send a test message through the CLI:

```bash
openclaw send "What topics are you currently monitoring?"
```

The agent should respond based on its SOUL configuration, mentioning AI safety and agent architectures. It should also begin writing to MEMORY.md.

You can also use the <button onclick="launch('NemoClaw Client');"><i class="fa-solid fa-rocket"></i> NemoClaw Client</button> for a chat interface instead of the CLI. The client connects to your running agent automatically, or falls back to a mock agent for testing.

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
| `openclaw: command not found` | Not installed or not in PATH | Run `pip install openclaw` and restart your terminal |
| `Agent failed to start` | Missing SOUL.md | Ensure SOUL.md is in the current directory |
| `Model error: 401` | NVIDIA API key not set | Check your API key in the Secrets Manager |
| `Heartbeat timeout` | Model latency too high | Increase `max_tokens_per_cycle` or switch to a faster model |
| `No messages received` | No integrations configured | Use `openclaw send` for local testing |

</details>

<details>
<summary><strong>Can't install OpenClaw? Use the mock agent instead.</strong></summary>

If you're unable to install OpenClaw in your environment, the exercise code includes a **mock agent** that simulates the same interface. The mock agent is deliberately leaky — it responds to some adversarial prompts in unsafe ways so that the safety evaluation exercises can detect and report violations.

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
