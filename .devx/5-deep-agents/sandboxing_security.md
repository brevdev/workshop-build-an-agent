# Sandboxing and Security

<img src="_static/robots/spyglass.png" alt="Security Robot" style="float:right;max-width:300px;margin:25px;" />

Your deep agent can read files, write code, and execute shell commands. That's incredibly powerful — and incredibly dangerous. In this section, we'll see exactly *why* sandboxing matters, explore different approaches, and understand the security principles that make agents production-ready.

<!-- fold:break -->

## Why Security Matters More for Deep Agents

Three characteristics of deep agents amplify security concerns compared to the shallow agents you built in earlier modules:

1. **Extended autonomy** — Deep agents run for minutes to hours without human oversight. A shallow agent completes in seconds, giving you time to catch mistakes. A deep agent might execute dozens of steps before you see any output.

2. **Code execution** — Deep agents run shell commands, write files, install packages, and spawn sub-processes. A hallucinated `rm -rf /` or a fabricated `pip install malicious-package` isn't a hypothetical — it's a well-documented risk.

3. **Cascading effects** — In a multi-agent system, a single sub-agent error can propagate through the entire hierarchy. A researcher sub-agent that follows a malicious link could compromise the orchestrator's entire workspace.

The key insight: **once an agent passes control to a subprocess, only OS-level enforcement can ensure containment**. Application-level controls — prompt instructions like "don't delete files" — are insufficient because the model can hallucinate past them, and subprocess execution bypasses them entirely.

<details>
<summary><strong>Concrete risk examples</strong></summary>

- **Hallucinated destructive commands** — The agent generates and executes `rm -rf /important/data` while trying to "clean up"
- **Supply chain attacks** — The agent fabricates package names that happen to match malicious packages on public registries
- **Data exfiltration** — A compromised sub-agent leaks sensitive data via DNS tunneling or encoded HTTP requests
- **Resource exhaustion** — An agent in a retry loop spawns thousands of sub-processes, consuming all available compute

</details>

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

## The Security Spectrum

Not all isolation is equal. Approaches range from trusting the model entirely to full hardware virtualization. Understanding this spectrum helps you choose the right level for your use case.

| Tier | Approach | Isolation Level | Use Case |
|------|----------|----------------|----------|
| Weakest | Prompt-only controls | None (trust the model) | Development and testing only |
| | Permission-gated runtimes (Deno) | Capability grants | Lightweight scripting tasks |
| | OS-level sandboxing (Bubblewrap/Seatbelt) | Filesystem and network boundaries | Desktop agents (e.g., Claude Code) |
| | Container hardening (Docker + seccomp) | Process-level, shared kernel | Most production workloads |
| | User-space kernel (gVisor) | Syscall emulation | High-security workloads |
| Strongest | Hardware virtualization (Firecracker) | Full VM, separate kernel | Maximum isolation |

As you move down the table, isolation increases but so does complexity and overhead. The right choice depends on your **threat model**: who is running the agent, what data it can access, and what the consequences of a breach would be.

> Our demo uses **Docker (tier 4)**, which covers most production workloads.

<details>
<summary><strong>How to choose your isolation level</strong></summary>

Ask these questions:

1. **Who controls the agent's inputs?** If only trusted developers, you can use lighter isolation. If end users can influence prompts, you need stronger boundaries.
2. **What data can the agent access?** PII, credentials, or financial data demands stronger isolation than public information.
3. **Does the agent execute code?** Any code execution — even "just" shell commands — requires at minimum container-level isolation.
4. **What are the consequences of a breach?** A leaked API key is bad. A deleted production database is catastrophic. Match isolation to impact.

</details>

<!-- fold:break -->

## How Our Sandbox Works

Our implementation uses **Docker containers** as the isolation boundary — the agent runs locally and delegates code execution to an isolated container.

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

## Two Patterns for Connecting Agents to Sandboxes

Before choosing a sandbox **technology**, you need to choose a sandbox **pattern**. This architectural decision affects security, latency, and how quickly you can iterate.

### Pattern 1 — Agent IN Sandbox

The **agent itself** runs inside the sandbox. It communicates with external systems — the LLM API, databases, user interfaces — over HTTP or WebSocket connections.

```
┌─────────────────────────────┐
│         Sandbox             │
│  ┌─────────────────────┐   │
│  │   Agent Process      │   │
│  │   + Tools            │   │
│  │   + File System      │   │
│  │   + API Keys         │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
         ↕ HTTP/WS
    External Services
```

**Pros:** Mirrors local development; simple architecture — everything runs in one place.

**Cons:** API keys live inside the sandbox (security risk); container rebuilds needed for every agent update; all tools inherit the sandbox's full permissions.

**Best for:** Prototyping and tight coupling between agent and execution environment.

### Pattern 2 — Sandbox as Tool

The **agent runs locally** (or on your server), and code execution is **delegated** to remote sandboxes via API calls. The sandbox is just another tool the agent can call.

```
┌──────────────────┐     ┌─────────────────┐
│   Agent Process   │────→│   Sandbox API    │
│   + API Keys     │     │   (Code exec)   │
│   + Orchestration │←────│   (Isolated)    │
└──────────────────┘     └─────────────────┘
    Your server              Remote sandbox
```

**Pros:** API keys stay outside the sandbox; instant agent updates without container rebuilds; clean separation of agent state and execution; enables parallel sandbox execution; sandbox failures don't crash the agent.

**Cons:** Network latency per execution call; more moving parts to manage.

**Best for:** Most production deployments. This is the pattern used by the deepagents library.

| Dimension | Agent IN Sandbox | Sandbox as Tool |
|-----------|-----------------|-----------------|
| **Credential security** | Keys inside sandbox | Keys stay external |
| **Update speed** | Requires rebuild | Instant |
| **Failure isolation** | Agent + sandbox coupled | Independent |
| **Parallel execution** | Complex | Natural |

> Our demo uses **Pattern 2** — the agent runs locally and delegates execution to a Docker container.

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

<details>
<summary><strong>Docker Containers — how they isolate</strong></summary>

Docker is the most common approach for production agent sandboxing. It provides:

- **Namespace isolation** — Each container has its own filesystem, process tree, and network stack
- **Seccomp profiles** — Restrict which system calls the container can make
- **Read-only filesystems** — Prevent the agent from modifying the container image
- **Resource limits** — Cap CPU, memory, and network bandwidth

**Strengths:** Fast startup (~1s), massive ecosystem, familiar to most developers.

**Limitations:** Shared kernel — container escape vulnerabilities, while rare, do exist. Not suitable for truly untrusted code without additional hardening.

</details>

<details>
<summary><strong>Firecracker MicroVMs (E2B)</strong></summary>

Full hardware virtualization with ~150ms startup time. **E2B** is a leading agent sandboxing platform built on Firecracker.

- Each agent gets its own **kernel** — the strongest isolation available
- MicroVMs are lightweight (as little as 5MB memory overhead)
- Startup time rivals containers, not traditional VMs
- Full Linux environment with arbitrary package installation

**When to use:** Untrusted code execution, maximum security requirements, or any scenario where you can't trust the code your agent generates.

</details>

<details>
<summary><strong>OS-Level Sandboxing (Bubblewrap / Seatbelt)</strong></summary>

Lightweight sandboxing built into the operating system:

- **Bubblewrap** (Linux) — Creates unprivileged containers using Linux namespaces
- **Seatbelt** (macOS) — Apple's sandbox framework restricting filesystem, network, and IPC access

These are used by **Claude Code** for local execution — restricting which filesystem paths the agent can access, blocking network connections to unauthorized hosts, and limiting system call access.

**When to use:** Local and desktop agent deployments where you need lightweight isolation without full containerization.

</details>

<!-- fold:break -->

## Defense in Depth

<img src="_static/robots/supervisor.png" alt="Defense in Depth" style="float:right;max-width:250px;margin:15px;" />

No single layer of security is sufficient. Effective security for deep agents requires **multiple overlapping controls**, so that a failure in any one layer is caught by another. This principle — **defense in depth** — is the foundation of secure agent deployment.

Here are the layers, from closest to the user to closest to the hardware:

| Layer | Control | Example |
|-------|---------|---------|
| 1 | **Human-in-the-loop** | Approval gates for critical operations (Module 4 HITL) |
| 2 | **Permission systems** | Allowlists for tools, commands, and file paths |
| 3 | **Application sandboxing** | Restrict agent capabilities at the framework level |
| 4 | **Container/VM isolation** | OS-level containment (Docker, Firecracker) |
| 5 | **Network controls** | Default-deny egress, DNS monitoring |
| 6 | **Audit logging** | Record all agent actions for post-hoc review |

The key principle: assume any single layer can fail. HITL can be bypassed by batch operations. Permission systems can have gaps. Containers can have escape vulnerabilities. But all six failing simultaneously is extraordinarily unlikely.

<details>
<summary><strong>A real-world defense in depth example</strong></summary>

Consider a deep research agent deployed in production:

1. **HITL** — Users must approve the research plan before execution begins
2. **Permissions** — The agent can only use `web_search` and `file_write` tools; no shell access
3. **Application sandbox** — The LangChain framework restricts file writes to `/workspace/output/`
4. **Container** — The agent runs in a Docker container with read-only root filesystem
5. **Network** — Egress is limited to the LLM API and approved search domains; all other traffic is blocked
6. **Audit** — Every tool call, API request, and file write is logged with timestamps

If the agent is tricked by a prompt injection attack into trying to exfiltrate data, it would need to bypass the application file path restriction, escape the container's filesystem boundary, evade network egress controls, and avoid detection in the audit logs — all simultaneously.

</details>

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

### 6. Adversarial Testing

Before deploying, probe your agent with inputs designed to trigger unsafe behavior — prompt injection, harmful instructions, and edge cases. If you haven't tried to break it, you don't know it's safe.

### 7. Environment Separation

Use distinct configurations for development, staging, and production. Never test with production credentials or data.

<!-- fold:break -->

## Enterprise Production Considerations

<details>
<summary><strong>LangSmith Studio, deployment options, and state persistence</strong></summary>

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

</details>

<!-- fold:break -->

<details>
<summary><strong>How security evolved across all 5 modules</strong></summary>

| Module | Agent Capability | Security Consideration |
|--------|-----------------|----------------------|
| Module 1 | Tool calling (search, APIs) | Tool selection validation |
| Module 2 | RAG + document retrieval | Data access boundaries |
| Module 3 | Evaluation and testing | Adversarial test cases |
| Module 4 | Customized behavior + HITL | Human approval gates |
| **Module 5** | **Autonomous execution** | **OS-level sandboxing + defense in depth** |

Each level of capability demands a corresponding level of security. Deep agents sit at the far end of this spectrum — the most capable and the most in need of containment.

</details>

<!-- fold:break -->

## Module Wrap-Up

<img src="_static/robots/magician.png" alt="Next Steps" style="float:right;max-width:250px;margin:15px;" />

### What You Learned

| Topic | Key Takeaway |
|-------|-------------|
| **What Deep Agents Are** | Same LLM loop + planning, delegation, memory, skills |
| **Shallow vs. Deep** | Shallow for focused tasks; deep for complex, long-horizon work |
| **Real-World Applications** | Deep research, coding agents, analysis pipelines |
| **Security and Sandboxing** | OS-level isolation is essential; defense in depth |

### The Full Workshop Arc

| Module | What You Learned | Key Capability |
|--------|-----------------|----------------|
| Module 1 | Build agents with ReAct | Agent fundamentals |
| Module 2 | Extend with RAG and tools | Agent capabilities |
| Module 3 | Measure and evaluate | Agent quality |
| Module 4 | Customize through training | Agent expertise |
| **Module 5** | **Deep agents + sandboxing** | **Agent autonomy** |

### Where to Go Next

1. **Deploy** — Use `langgraph deploy` or Docker Compose to run your agent in production
2. **Evaluate** — Apply the Module 3 evaluation techniques to measure your deep agent's quality
3. **Customize** — Use Module 4's training techniques to fine-tune the model for your specific domain
4. **Scale** — Add more tools, skills, and sub-agents as your use cases grow
5. **Monitor** — Set up LangSmith tracing for production observability

You now have the complete toolkit — from building your first agent to deploying autonomous deep agents safely in production.

> **Congratulations!** You've completed Module 5: Deep Agents.
