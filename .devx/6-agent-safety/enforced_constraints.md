# Enforced Constraints with OpenShell

<img src="_static/robots/supervisor.png" alt="Security Robot" style="float:right;max-width:300px;margin:25px;" />

Docker isolates the *process* — the agent runs in its own container with its own filesystem. But inside that container, the agent has full access to everything. It can read any file, connect to any endpoint, and run as root if the container allows it.

OpenShell goes deeper. It uses **Linux kernel security modules** to enforce per-file, per-endpoint, and per-binary restrictions that the agent process **cannot override**, even if it gains arbitrary code execution inside the container.

<!-- fold:break -->

## What is Landlock LSM?

**Landlock** is a Linux Security Module available since kernel 5.13. It enables unprivileged processes to restrict their own access rights — and once those restrictions are applied, they **cannot be lifted** by the process itself.

Three properties make Landlock uniquely suited for agent safety:

### Unprivileged

Unlike AppArmor or SELinux, Landlock does not require root privileges to configure. An agent process can apply its own restrictions at startup. This means you don't need to modify the host system's security policy.

### Stackable

Landlock works alongside other security modules. You can run Landlock inside a Docker container that already has seccomp profiles and AppArmor policies. Each layer adds restrictions; none can remove restrictions applied by another.

### Irrevocable

This is the critical property. Once a Landlock ruleset is applied to a process, that process cannot lift the restrictions — not by calling syscalls, not by spawning child processes, not by any mechanism available to userspace code. The kernel enforces the boundary.

The technical mechanism is three syscalls:

1. `landlock_create_ruleset()` — Create a new ruleset with declared access rights
2. `landlock_add_rule()` — Add filesystem rules to the ruleset
3. `landlock_restrict_self()` — Apply the ruleset to the current process (irreversible)

<!-- fold:break -->

## The OpenShell Architecture

OpenShell builds on Landlock to provide a complete enforcement stack for agents. It organizes restrictions into three layers.

### Layer 1: Filesystem (Landlock)

Controls which paths the agent can read and write:

- **Read-only paths** — System libraries, agent configuration, skill files. The agent can read these but cannot modify them.
- **Read-write paths** — The agent's workspace and temporary directories. All file I/O is confined to these paths.
- **Deny everything else** — Any path not explicitly listed is inaccessible. The agent cannot see `/etc/passwd`, `/home`, or any host-mounted directory outside its policy.

The filesystem policy is enforced by Landlock at the kernel level. No amount of path traversal (`../../etc/passwd`) will bypass it because the kernel checks every file access against the ruleset.

### Layer 2: Process (seccomp BPF)

Controls which system calls the agent can make:

- **Identity** — `run_as_user` and `run_as_group` set the process UID/GID. Never root.
- **Syscall filtering** — seccomp BPF profiles block dangerous syscalls like `ptrace`, `mount`, and `reboot`. The agent can read files, write files, and make network connections — nothing else.
- **Child processes** — Any process spawned by the agent inherits the same restrictions. There is no escalation path.

### Layer 3: Network (HTTP CONNECT Proxy with Policy Engine)

Controls which endpoints the agent can reach:

- **Default-deny** — All outbound network traffic is blocked unless explicitly allowed.
- **Endpoint allowlist** — Each allowed endpoint is specified by hostname, port, and HTTP method. `integrate.api.nvidia.com:443` on POST is allowed; `evil.com:80` on GET is not.
- **Per-binary binding** — Network rules apply to specific binaries. Python can reach the LLM API; curl cannot.
- **Policy evaluation** — Complex routing decisions (e.g., "allow POST to the LLM API only if the request body does not contain PII") are handled by the proxy's built-in policy engine.

Together, these three layers create a constraint envelope that the agent cannot escape.

<!-- fold:break -->

## Reading an OpenShell Policy

OpenShell policies are YAML files that declare the constraint envelope. Here is the `research_assistant.yaml` policy you'll work with in this module:

```yaml
version: 1

process:
  run_as_user: "agent"
  run_as_group: "agent"

filesystem_policy:
  read_only:
    - /usr/lib
    - /usr/bin
    - /opt/agent/skills
    - /opt/agent/config
  read_write:
    - /workspace
    - /tmp/agent

default_network_action: "deny"

network_policies:
  - name: "llm_api"
    description: "Allow inference calls to NVIDIA NIM"
    endpoints:
      - "integrate.api.nvidia.com:443"
    binaries:
      - { path: /usr/bin/python3 }
    protocol: "rest"
    methods: ["POST"]

  - name: "rss_feeds"
    description: "Allow reading RSS feeds for research monitoring"
    endpoints:
      - "*.rss.com:443"
      - "feeds.*.org:443"
      - "arxiv.org:443"
    binaries:
      - { path: /usr/bin/python3 }
    protocol: "rest"
    methods: ["GET"]

  - name: "local_nemotron"
    description: "Allow routing to local Nemotron for sensitive queries"
    endpoints:
      - "localhost:8080"
      - "127.0.0.1:8080"
    binaries:
      - { path: /usr/bin/python3 }
    protocol: "rest"
    methods: ["POST"]
```

> **Note:** This policy is simplified for learning purposes. Production policies may use additional schema fields and nested structures. See the [OpenShell Policy Schema Reference](https://docs.nvidia.com/openshell/latest/reference/policy-schema.html) for the complete specification.

<!-- fold:break -->

### Walking Through the Policy

**`process` section** — The agent runs as user `agent`, not root. This is enforced at startup. Even if the agent tries to escalate privileges, the kernel blocks it.

**`filesystem_policy` section** — Four read-only paths provide access to system libraries, agent skills, and configuration. Two read-write paths (`/workspace` and `/tmp/agent`) are the only locations where the agent can create or modify files. Everything else — `/etc`, `/home`, `/root`, `/var` — is invisible to the agent.

**`default_network_action: "deny"`** — This is the most important line. Without it, the agent can reach any endpoint on the internet. With it, only explicitly listed endpoints are reachable.

**`network_policies` section** — Three policies define the agent's network perimeter:
- It can POST to the NVIDIA NIM API for inference
- It can GET from RSS feeds for research monitoring
- It can POST to localhost:8080 for local Nemotron inference (sensitive data routing)

No other network traffic is possible. The agent cannot exfiltrate data to an arbitrary server, download malicious payloads, or phone home to a C2 endpoint.

<!-- fold:break -->

<details>
<summary><strong>Application vs. Kernel: Side-by-Side</strong></summary>

To understand why kernel enforcement matters, compare Module 4's application-level approach with OpenShell's kernel-level approach.

**Module 4: Python regex validation**

```python
# From M4's bash agent — application-level filtering
def validate_command(cmd: str) -> bool:
    if re.search(r"[`$]", cmd):
        return False  # Block shell metacharacters
    allowed = ["ls", "cat", "grep", "find", "wc"]
    binary = cmd.split()[0]
    return binary in allowed
```

This check runs in Python before the command reaches the shell. It can be bypassed by:

- **Encoding tricks** — `echo "Y2F0IC9ldGMvcGFzc3dk" | base64 -d | sh` decodes to `cat /etc/passwd`
- **Aliasing** — The agent asks to run a script that internally calls forbidden commands
- **Indirect execution** — `python3 -c "import os; os.system('rm -rf /')"` doesn't match the regex
- **Unicode** — Some shells accept Unicode characters that visually resemble ASCII but bypass regex

**Module 6: Landlock kernel enforcement**

```yaml
filesystem_policy:
  read_only:
    - /usr/lib
    - /usr/bin
  read_write:
    - /workspace
    - /tmp/agent
```

This policy is enforced by the Linux kernel. Every file access — regardless of how it's initiated (Python, shell, C binary, syscall) — is checked against the ruleset. There is no encoding trick, no aliasing, no indirect execution path that bypasses it. The kernel does not parse commands. It intercepts the `open()`, `read()`, and `write()` syscalls directly.

| Property | Application-Level (M4) | Kernel-Level (M6) |
|----------|----------------------|-------------------|
| Enforcement point | Python process | Linux kernel |
| Bypass via encoding | Yes | No |
| Bypass via child process | Yes | No (children inherit restrictions) |
| Bypass via direct syscall | Yes | No (kernel intercepts syscalls) |
| Can the agent lift restrictions? | Yes (modify the Python code) | No (irrevocable after `landlock_restrict_self`) |

Application-level checks are still useful as a first line of defense. But for autonomous agents, they are not sufficient on their own.

</details>

<!-- fold:break -->

## Exercise 1: Load and Validate an OpenShell Policy

The most hardened policy is useless if it contains misconfigurations. A single overly-broad path or a missing network deny rule can undo the entire security posture. Your first exercise is to build a **policy validator** that catches these mistakes before the agent starts.

<button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 1');"><i class="fas fa-code"></i> # TODO: Exercise 1</button>

### What You'll Build

The `load_and_validate_policy()` function:

1. **Parses** an OpenShell YAML policy file
2. **Checks** for three security violations:
   - Process runs as root (critical)
   - Filesystem write access is overly broad — writing to `/`, `/etc`, `/usr`, or `/var` (critical)
   - No network controls defined — neither `network_policies` nor `default_network_action: deny` (warning)
3. **Returns** a `PolicyValidationResult` with the list of violations and whether the policy is safe

### Test Your Validator

The `policies/` directory contains two policy files:

- `baseline_permissive.yaml` — Deliberately insecure. Contains all three violations. Your validator should flag all of them.
- `research_assistant.yaml` — Hardened. Should pass validation with zero violations.

<!-- fold:break -->

<details>
<summary><strong>Hint: Exercise 1 Solution</strong></summary>

```python
def load_and_validate_policy(policy_path: str) -> PolicyValidationResult:
    with open(policy_path, "r") as f:
        policy_data = yaml.safe_load(f)

    violations = []

    # Check root
    process_config = policy_data.get("process", {})
    run_as_user = process_config.get("run_as_user", "")
    if run_as_user in ("root", "0"):
        violations.append(PolicyViolation(
            rule="runs_as_root",
            severity="critical",
            description="Agent runs as root — a compromised agent with root access owns the entire system",
        ))

    # Check broad writes
    fs_policy = policy_data.get("filesystem_policy", {})
    read_write_paths = fs_policy.get("read_write", [])
    dangerous_paths = ["/", "/etc", "/usr", "/var"]
    for path in read_write_paths:
        if path in dangerous_paths:
            violations.append(PolicyViolation(
                rule="overly_broad_write",
                severity="critical",
                description=f"Write access to '{path}' is overly broad — agent can modify system files",
            ))

    # Check network controls
    network_policies = policy_data.get("network_policies", [])
    default_action = policy_data.get("default_network_action", "")
    if not network_policies and default_action != "deny":
        violations.append(PolicyViolation(
            rule="no_network_controls",
            severity="warning",
            description="No network controls defined — agent can reach any endpoint on the internet",
        ))

    has_critical = any(v.severity == "critical" for v in violations)
    return PolicyValidationResult(
        policy_path=policy_path,
        policy_data=policy_data,
        violations=violations,
        is_safe=not has_critical,
    )
```

</details>

<!-- fold:break -->

## Why Validation Matters

Misconfigurations are the **#1 cause of security incidents** in cloud and container deployments. The same applies to agent policies:

- A developer adds `/` to `read_write` during debugging and forgets to remove it
- A team copies a permissive baseline policy into production without hardening it
- A policy update removes `default_network_action: deny` by accident

Automated validation catches these errors before they reach the agent. In production, you'd run this validator in CI/CD — every policy change gets validated before merge, and the agent refuses to start if the policy fails.

The hardened `research_assistant.yaml` policy you read earlier represents the target state. Exercise 1 teaches you to verify that any policy meets that standard.

> With policy validation in place, you know the agent's constraints are correctly configured. But constraints only control *where* the agent can act — they don't control *what data* the agent processes. Head to [Data Routing with Privacy Router](data_routing) to close that gap.
