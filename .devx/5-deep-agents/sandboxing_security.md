# Sandboxing and Security

<img src="_static/robots/spyglass.png" alt="Security Robot" style="float:right;max-width:300px;margin:25px;" />

Your deep agent can read files, write code, and execute shell commands. That's incredibly powerful — and incredibly dangerous. In this section, we'll see exactly *why* sandboxing matters, explore different approaches, and understand the security principles that make agents production-ready.

<!-- fold:break -->

## The Problem: Agents See Everything

Without sandboxing, your agent operates directly on the host system. It has the same access as the process running it. Let's see what that means.

### Demo: No Sandbox

In the Deep Agent Builder UI, make sure **Sandbox Mode is OFF** (you'll see "⚠️ No Sandbox" in the header). Then ask:

> *"What files are in my workspace?"*

The agent will respond with something like:

```
/tmp/deepagent_workspace/passwords.txt
/tmp/deepagent_workspace/api_keys.env
/tmp/deepagent_workspace/bank_accounts.csv
/tmp/deepagent_workspace/ssn_records.txt
```

Now ask it to read one:

> *"Read the contents of passwords.txt"*

The agent will happily return:

```
admin:SuperSecret123!
root:P@ssw0rd_2026
db_user:mysql_prod_xK9#mN2
```

**This is the problem.** The agent can see — and exfiltrate — every file on the host system that the process has access to.

<!-- fold:break -->

## The Solution: Sandboxing

<img src="_static/robots/operator.png" alt="Sandbox" style="float:right;max-width:250px;margin:15px;" />

**Sandboxing** isolates the agent's execution environment from the host system. The agent operates inside a container or VM that has no access to the host's files, network, or credentials.

### Demo: With Sandbox

Now toggle **Sandbox Mode ON** in the Settings panel (you'll see "🔒 Sandboxed" in the header). Build a new agent and ask the same question:

> *"What files are in my workspace?"*

The agent responds:

```
The workspace is empty.
```

**The sensitive files don't exist inside the sandbox.** The agent runs in a fresh Docker container with no host mounts. It literally cannot see your files.

<!-- fold:break -->

## How Our Sandbox Works

Our implementation uses **Docker containers** as the isolation boundary:

```python
class DockerSandboxBackend(SandboxBackendProtocol):
    def __init__(self):
        self._container = docker_client.containers.run(
            "python:3.11-slim",
            command="sleep infinity",
            detach=True,
            working_dir="/workspace",
            mem_limit="512m",
            nano_cpus=1_000_000_000,  # 1 CPU
            # No host mounts — fully isolated
        )
```

Key properties:
- **No host mounts** — The container has its own filesystem
- **Resource limits** — 512MB RAM, 1 CPU
- **Auto-cleanup** — Container is destroyed when the session ends
- **Full protocol compliance** — Implements `SandboxBackendProtocol` so all deepagents tools work transparently

When the agent calls `ls`, `read_file`, `write_file`, or `execute`, those operations happen *inside the container*, not on your machine.

<!-- fold:break -->

## Types of Sandboxes

There are several approaches to sandboxing, each with different tradeoffs:

| Approach | Isolation Level | Startup Time | Cost | Best For |
|---|---|---|---|---|
| **Local Docker** | Container-level | ~1 second | Free | Development, demos |
| **Daytona** (OSS) | Container + orchestration | ~2-5 seconds | Self-hosted | Teams, CI/CD |
| **Modal** | Serverless container | ~3-10 seconds | Pay-per-use | Cloud production |
| **Runloop** | Full VM | ~5-15 seconds | Pay-per-use | Maximum isolation |
| **No sandbox** | None | 0 | Free | Trusted environments only |

For production, the choice depends on your security requirements:

- **Development/demos**: Local Docker is fast and free
- **Team environments**: Daytona provides orchestration and multi-user support
- **Cloud production**: Modal or Runloop for serverless, managed isolation
- **Air-gapped/regulated**: Self-hosted Daytona with custom network policies

<!-- fold:break -->

## Defense in Depth: HITL + Sandbox

<img src="_static/robots/supervisor.png" alt="Defense in Depth" style="float:right;max-width:250px;margin:15px;" />

The strongest security posture combines **Human-in-the-Loop (HITL)** from Module 4 with sandboxing:

| Layer | What It Does | Protects Against |
|---|---|---|
| **HITL** | Human reviews tool calls before execution | Hallucinated commands, unintended actions |
| **Sandbox** | Agent runs in isolated container | Data exfiltration, system damage |

Together, they provide **defense in depth**:
1. The agent proposes an action (e.g., `execute: rm -rf /`)
2. HITL pauses and asks the human to approve or reject
3. Even if approved, the sandbox limits the blast radius to the container

Neither alone is sufficient:
- HITL without sandbox → human might approve something dangerous by accident
- Sandbox without HITL → agent might do expensive operations (API calls, infinite loops) without oversight

<!-- fold:break -->

## Agent Security Principles

Beyond sandboxing, here are the fundamental security principles for production agents:

### 1. Trust the Sandbox, Not the Model

From the [deepagents security docs](https://github.com/langchain-ai/deepagents):

> *"Deep Agents follows a 'trust the LLM' model. The agent can do anything its tools allow. Enforce boundaries at the tool/sandbox level, not by expecting the model to self-police."*

Never rely on the model to avoid dangerous actions. It *will* hallucinate. Enforce limits at the infrastructure level.

### 2. Principle of Least Privilege

Give the agent only the tools it needs. If it doesn't need shell access, don't enable it. If it doesn't need file write, use read-only mode.

### 3. Credential Isolation

API keys, database passwords, and tokens should **never** be accessible to the agent. Use environment variables outside the sandbox, and don't mount credential files into containers.

### 4. Audit Everything

Every tool call, every file write, every command execution should be logged. LangSmith provides tracing and monitoring for this — you can review every action the agent took after the fact.

### 5. Rate Limiting

Prevent runaway agents from making thousands of API calls or running infinite loops. Set recursion limits on the graph and timeouts on tool execution.

<!-- fold:break -->

## Enterprise Production Considerations

Taking your deep agent to production requires more than just sandboxing:

### Monitoring with LangSmith Studio

[LangSmith Studio](https://docs.langchain.com/langsmith/studio) provides a graph-mode debugger for your agent. You can:
- Visualize the middleware pipeline
- Step through each node's input/output
- Time-travel to replay and debug issues
- Monitor token usage and costs

```bash
# Run locally
pip install "langgraph-cli[inmem]"
langgraph dev  # Opens Studio at http://localhost:2024
```

### Deployment Options

| Option | When to Use |
|---|---|
| **LangSmith Cloud** | Managed hosting, team access via workspace |
| **Docker Compose** | Self-hosted, full control |
| **LangGraph CLI** | Local development and testing |
| **Kubernetes** | Enterprise scale, custom orchestration |

### State Persistence

For production, replace `MemorySaver()` (in-memory, lost on restart) with a persistent checkpointer backed by PostgreSQL or Redis. This enables:
- Conversation resume after server restart
- Multi-server deployments with shared state
- Audit trails of agent decisions

<!-- fold:break -->

## The "Now What?"

<img src="_static/robots/magician.png" alt="Next Steps" style="float:right;max-width:250px;margin:15px;" />

You've built a deep agent that can plan, code, execute, delegate, and self-manage. You've secured it with sandboxing and HITL. Here's where to go next:

1. **Deploy** — Use `langgraph deploy` or Docker Compose to run your agent in production
2. **Evaluate** — Apply the Module 3 evaluation techniques to measure your deep agent's quality
3. **Customize** — Use Module 4's training techniques to fine-tune the model for your specific domain
4. **Scale** — Add more tools, skills, and sub-agents as your use cases grow
5. **Monitor** — Set up LangSmith tracing for production observability

The deep agent pattern isn't just a toy — it's the architecture behind production AI coding assistants, research agents, and autonomous systems. You now have the knowledge to build, secure, and deploy them.

> **Congratulations!** You've completed Module 5: Deep Agents. 🎉
