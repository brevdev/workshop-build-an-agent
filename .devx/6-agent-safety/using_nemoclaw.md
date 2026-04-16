# Working with NemoClaw

<img src="_static/robots/supervisor.png" alt="NemoClaw Hands-On Robot" style="float:right;max-width:300px;margin:25px;" />

Your NemoClaw sandbox is running. The agent lives inside four enforcement layers: **Network** (egress policy), **Filesystem** (Landlock), **Process** (seccomp + least privilege), and **Inference** (Privacy Router). Reading about those layers and *feeling* them are very different things. This page walks you through six hands-on exercises that turn each layer into a copy-pasteable experience — and that revisit the four probes you just ran on the [previous page](setup_openclaw) to see NemoClaw shut them down.

<!-- fold:break -->

## The Arc

Every exercise on this page follows the same four-step pattern:

1. **Recall** — the unsecured behavior from `setup_openclaw.md`
2. **Observe** — the same probe against the hardened sandbox
3. **Harden** — extend or write a policy that enforces the boundary
4. **Validate** — a short Python companion that catches the same class of issue programmatically

Here is the full arc at a glance. The layer column maps to the four layers introduced on [Why NemoClaw: Principles and Layers](why_nemoclaw).

| # | Exercise | Layer | Recalls |
|---|---|---|---|
| 1 | Stop the agent from phoning home | Network | Probe 1 |
| 2 | Not all allow-rules are equal | Network (L7 vs L4) | — |
| 3 | Make containment irrevocable | Filesystem + Process | Probe 2 |
| 4 | Remove the keys from the agent | Inference + Network | Probe 3 |
| 5 | Route sensitive queries locally | Inference | — |
| 6 | Continuous safety evaluation | Cross-cutting | Probe 4 |

> Exercises 1–5 establish the four enforcement layers. Exercise 6 is the capstone — it wires together red-team probing, LLM-as-judge scoring, and a full safety evaluation suite in Python. Together they give you an end-to-end agent-safety workflow you can run in CI/CD.

<!-- fold:break -->

```mermaid
---
config:
  theme: 'base'
  themeVariables:
    primaryColor: '#eaf6e0'
    secondaryColor: '#eaf6e0'
    background: white
---
graph LR
    V[Vanilla OpenClaw] -->|Probe 1-4 succeed| U[Unsafe behavior]
    V -->|+OpenShell enforcement| N[NemoClaw]
    N -->|Ex 1-5 close each gap| H[Hardened agent]
    H -->|Ex 6: probe + score| S[Safety suite]
    S -->|CI/CD regression| H

    classDef node fill:#fff,stroke:#444,stroke-width:2px,color:#222;
```

<!-- fold:break -->

## How to Use This Page

- **Recall callouts** (*"Recall: Probe N"*) refer back to the four probes at the end of [Set Up Your OpenClaw Agent](setup_openclaw). Keep that page open in a second tab.
- **Python companions** are called "sidekicks" — short TODO extensions in <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 1');"><i class="fas fa-code"></i> agent_safety.py</button>.
- **Layer tags** at the top of each exercise (*Layer: Network*, etc.) cross-reference the enforcement layers introduced on [Why NemoClaw: Principles and Layers](why_nemoclaw).
- **Static vs dynamic callouts** remind you which policy fields hot-reload and which require sandbox recreation.
- All CLI commands marked for the sandbox shell run inside `nemoclaw my-assistant connect`. All host-side commands run in a separate terminal outside the sandbox.

<!-- fold:break -->

## Section 1 — Layer 1: Network (Egress Policy)

The Network layer controls **where the agent can reach**. NemoClaw's baseline is deny-by-default: every outbound connection is blocked unless a policy entry explicitly allows it. Network policy is the one enforcement layer that hot-reloads without sandbox recreation — a deliberate design so operators can grant (or revoke) access on a running agent.

<!-- fold:break -->

### Exercise 1: Stop the agent from phoning home

> *Layer: **Network** · Recalls: **Probe 1** (Phone Home) · Runs in: host terminal + sandbox terminal*

Vanilla OpenClaw cheerfully fetched `https://httpbin.org/ip` for you. Let's see what happens inside the NemoClaw sandbox.

<!-- fold:break -->

**Step 1 — Observe the deny.** From inside the sandbox:

```bash
nemoclaw my-assistant connect
curl -s https://httpbin.org/ip
```

Expected output:

```text
curl: (56) Received HTTP code 403 from proxy after CONNECT
```

The proxy intercepted your request, checked the policy, found no matching `network_policies` entry for `httpbin.org:443`, and returned a 403. **This is the same probe from Probe 1 — the behavior has changed because the infrastructure has.**

<!-- fold:break -->

**Step 2 — Read the baseline policy.** From a host terminal (outside the sandbox):

```bash
openshell policy get my-assistant
```

Scroll through the output. You'll see three sections:

- `filesystem_policy` — paths the agent can read/write (static)
- `process` — the `sandbox` user the agent runs as (static)
- `network_policies` — named blocks, each listing endpoints + binaries (dynamic)

`httpbin.org` is nowhere in `network_policies`, so the proxy denied it. Let's add an entry.

<!-- fold:break -->

**Step 3 — Write a policy.** On the host, create a file called `httpbin-readonly.yaml`:

```yaml
network_policies:
  httpbin_access:
    name: httpbin-readonly
    endpoints:
      - host: httpbin.org
        port: 443
        protocol: rest
        enforcement: enforce
        access: read-only
    binaries:
      - { path: /usr/bin/curl }
```

Apply it to the live sandbox:

```bash
openshell policy set my-assistant --policy httpbin-readonly.yaml --wait
```

The `--wait` flag blocks until the proxy picks up the new rule. No sandbox restart required — this is the dynamic enforcement layer in action.

<!-- fold:break -->

**Step 4 — Confirm the change.** Back inside the sandbox:

```bash
curl -s https://httpbin.org/ip
```

Expected:

```json
{
  "origin": "10.x.x.x"
}
```

The agent can now reach `httpbin.org`. Dynamic policy hot-reload is one of NemoClaw's core operational affordances: grant a new endpoint without downtime, revoke one the same way.

> Remember this for Exercise 3 — **filesystem** policy is *static*. You cannot change it on a running sandbox. Different layers, different tradeoffs.

<!-- fold:break -->

**Step 5 — Python sidekick: validate the policy before you ship it.** Open <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 1');"><i class="fas fa-code"></i> # TODO: Exercise 1</button> and complete `load_and_validate_policy()`. The validator checks three classes of violation:

| Check | Severity | Why |
|---|---|---|
| `run_as_user == "root"` | critical | Root agents own the entire system on compromise |
| Broad `read_write` path (`/`, `/etc`, `/usr`, `/var`) | critical | Makes Landlock pointless |
| No `network_policies` AND `default_network_action != "deny"` | warning | Agent can reach anything |

Test against the two fixtures in `policies/`:

- `baseline_permissive.yaml` — deliberately weak. Your validator should flag all three.
- `research_assistant.yaml` — hardened. Zero violations.

<details>
<summary><strong>🆘 Need some help?</strong></summary>

```python
def load_and_validate_policy(policy_path: str) -> PolicyValidationResult:
    with open(policy_path, "r") as f:
        policy_data = yaml.safe_load(f)

    violations = []

    # Check: root
    process_config = policy_data.get("process", {})
    run_as_user = process_config.get("run_as_user", "")
    if run_as_user in ("root", "0"):
        violations.append(PolicyViolation(
            rule="runs_as_root",
            severity="critical",
            description="Agent runs as root — a compromised agent with root access owns the entire system",
        ))

    # Check: broad writes
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

    # Check: network controls
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

Run it:

```bash
cd /project/code/6-agent-safety
python -c "from agent_safety import load_and_validate_policy; r = load_and_validate_policy('policies/baseline_permissive.yaml'); print(r.is_safe, len(r.violations))"
```

Expected: `False 3` — three violations, not safe. The same validator wired into CI/CD would block a weak policy from ever reaching a sandbox.

> **What you just learned:** deny-by-default is the posture, hot-reload is the operational affordance, and programmatic validation is the safety net that catches policy regressions before they hit production.

<!-- fold:break -->

### Exercise 2: Not all allow-rules are equal

> *Layer: **Network** (L7 vs L4) · Continues from Exercise 1*

You wrote `access: read-only` in Exercise 1. Let's find out what that actually enforces — and what it doesn't.

<!-- fold:break -->

**Step 1 — Try a POST against a read-only endpoint.** From inside the sandbox:

```bash
curl -s -X POST https://httpbin.org/post -H "Content-Type: application/json" -d '{"test": true}'
```

Expected: the request is blocked at the L7 layer. Check the deny from a host terminal:

```bash
openshell logs my-assistant --since 2m | grep "OCSF HTTP"
```

Look for a line like:

```text
OCSF HTTP:POST [MED] DENIED POST https://httpbin.org/post [policy:httpbin_access engine:opa]
```

The proxy terminated TLS, inspected the HTTP request, saw a POST method, and denied it because the policy said `access: read-only`. This is L7 — layer 7 — enforcement.

<!-- fold:break -->

**Step 2 — Remove the L7 hint.** Modify your `httpbin-readonly.yaml`: change `protocol: rest` to `protocol: tcp` (or omit the `protocol:` line entirely). Reapply:

```bash
openshell policy set my-assistant --policy httpbin-readonly.yaml --wait
```

Retry the POST:

```bash
curl -s -X POST https://httpbin.org/post -H "Content-Type: application/json" -d '{"test": true}'
```

This time it succeeds. **Why?** Without `protocol: rest`, the proxy treats the rule as plain TCP — binary/host/port match pass, then *any* payload tunnels through. `access: read-only` is irrelevant at the TCP layer because the proxy isn't inspecting the HTTP method.

<!-- fold:break -->

**Step 3 — Restore the L7 hint.** Change `protocol` back to `rest`. Reapply. POST is blocked again.

> **The gotcha:** `access: read-only` only means something if `protocol: rest` is set. A policy that looks restrictive can be coarse in practice.

<!-- fold:break -->

<details>
<summary><strong>When to use `protocol: tcp` intentionally</strong></summary>

Not every protocol is HTTP. Database connections (PostgreSQL, Redis), gRPC, SSH, raw socket APIs — all need TCP-level rules because the proxy can't parse the payload. For those, you write allow-rules at the host+port level and accept that any client-side code with permission to open the socket can do whatever the protocol supports.

The rule is: use `protocol: rest` whenever the agent is making HTTP/S calls (which is most of the time for LLM-era agents), because it gives you per-method control. Fall back to `protocol: tcp` only for non-HTTP protocols.

</details>

<!-- fold:break -->

**Step 4 — Per-binary scoping.** One more subtlety. Add another binary to your policy and observe that a rule for `/usr/bin/curl` does **not** cover `/usr/bin/python3`:

```yaml
network_policies:
  httpbin_access:
    name: httpbin-readonly
    endpoints:
      - host: httpbin.org
        port: 443
        protocol: rest
        enforcement: enforce
        access: read-only
    binaries:
      - { path: /usr/bin/curl }
      # /usr/bin/python3 is NOT listed
```

Apply, then from the sandbox:

```bash
python3 -c "import urllib.request; print(urllib.request.urlopen('https://httpbin.org/ip').read())"
```

Expected: a `urllib.error.URLError` — the proxy denied Python because Python isn't in the binary list, even though curl is allowed to reach the same endpoint.

Add `- { path: /usr/bin/python3 }` to `binaries`, reapply, re-run. Python now succeeds.

> **Per-binary scoping is how you give one tool access to an endpoint without giving every tool access.** It turns "can reach httpbin.org" into "curl can reach httpbin.org" — a real least-privilege boundary.

<!-- fold:break -->

> **What you just learned:** three things make a network allow-rule precise — (1) the host+port, (2) the HTTP method constraint via `protocol: rest` + `access`, and (3) which binary is invoking the rule. Leave any one coarse and you've left room for unexpected behavior.

<!-- fold:break -->

## Section 2 — Layers 2 & 3: Filesystem + Process (kernel-level containment)

Layers 2 and 3 share an exercise because they're both **kernel-level, static containment**. They're set once when the sandbox is created, locked in by the kernel, and unchangeable from inside the agent process by design. That tradeoff — stronger guarantee for less flexibility — is the core teaching point.

<!-- fold:break -->

### Exercise 3: Make containment irrevocable

> *Layers: **Filesystem** (Landlock) + **Process** (seccomp, non-root, dropped capabilities) · Recalls: **Probe 2** (Read the Diary)*

Vanilla OpenClaw let the agent read `/etc/passwd` without complaint. Let's see what the sandbox lets it do.

<!-- fold:break -->

#### Part A: Filesystem (Landlock LSM)

**Step 1 — Reads often still work.** From inside the sandbox:

```bash
cat /etc/passwd | head -3
```

Expected: prints the first three entries. Landlock baselines `/etc` as *read-only* because agents often legitimately need to read config-like files. Reads through pre-approved paths still succeed — the goal is containment, not starvation.

<!-- fold:break -->

**Step 2 — Writes are where the kernel stops you.** Still in the sandbox:

```bash
echo "malicious" > /etc/passwd
echo "also malicious" > /usr/bin/evil
echo "unreachable at all" > /opt/foo
```

Expected: all three fail with `Permission denied`. Compare the error type — this is not a filesystem permission error in the POSIX sense. It's Landlock refusing, at the kernel level, to allow the syscall to reach the path.

<!-- fold:break -->

**Step 3 — Try to bypass.** Landlock makes strong claims ("irrevocable by design"). Let's stress-test them:

```bash
# Symlink trick
ln -s /etc/passwd /sandbox/fake_passwd
echo "oops" > /sandbox/fake_passwd
# Path traversal
echo "oops" > /sandbox/../etc/passwd
# Subprocess spawn
bash -c "echo oops > /etc/passwd"
# Ask the kernel nicely
python3 -c "open('/etc/passwd', 'w').write('oops')"
```

Expected: all fail. Landlock resolves paths at the kernel before the syscall, so symlinks and traversal strings don't trick it. Subprocesses inherit the restriction because `PR_SET_NO_NEW_PRIVS` is set. Python's `open()` is the same `openat()` syscall. There's no path out from inside the process.

> This is what *"irrevocable by design"* means. The kernel enforces the policy, not userspace. A compromised agent cannot ask politely to be let out.

<!-- fold:break -->

**Step 4 — Static vs dynamic.** Recall that in Exercise 1 you added a new network rule with `openshell policy set --wait` and it applied instantly. Try that for filesystem:

```bash
# (Host terminal)
cat > fs-widen.yaml <<'EOF'
filesystem_policy:
  read_write:
    - /sandbox
    - /tmp
    - /dev/null
    - /etc
EOF
openshell policy set my-assistant --policy fs-widen.yaml --wait
```

Expected: the command either rejects the filesystem field as immutable, or silently accepts it but the restriction doesn't apply. **Filesystem policy is creation-time only.** To change it, you destroy and recreate the sandbox with `nemoclaw my-assistant destroy` + re-onboard. This is intentional: the strongest containment boundary shouldn't be reachable from operational-speed workflows.

<!-- fold:break -->

**Step 5 — Python sidekick: extend the validator.** Re-open <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 1');"><i class="fas fa-code"></i> load_and_validate_policy</button>. Your policy validator already flags broad `read_write` paths — confirm it catches `baseline_permissive.yaml`, which writes to `/`:

```bash
python -c "from agent_safety import load_and_validate_policy; r = load_and_validate_policy('policies/baseline_permissive.yaml'); [print(v.rule, '->', v.description) for v in r.violations]"
```

Expected output includes:

```text
overly_broad_write -> Write access to '/' is overly broad — agent can modify system files
```

This is why static validation is important: the policy that *ships* dictates the policy that *protects*. A mistake here isn't recoverable without a sandbox rebuild.

<!-- fold:break -->

#### Part B: Process hardening (seccomp + non-root + dropped capabilities)

Filesystem containment keeps the agent out of places it shouldn't be. Process hardening keeps the agent from *becoming something it shouldn't be*.

**Step 1 — Confirm non-root identity.** Inside the sandbox:

```bash
whoami
id
```

Expected: `sandbox` user, `sandbox` group, no sudoer status. This is the `process.user` field you saw in Exercise 1's policy.

<!-- fold:break -->

**Step 2 — Try to escalate.** Still inside:

```bash
sudo -n whoami 2>&1 | head -1
```

Expected: `sudo: a password is required` or similar — sudo is refused because capabilities are dropped and no-new-privileges is set.

<!-- fold:break -->

**Step 3 — Try dangerous syscalls (seccomp BPF).** Try mount, ptrace, and unshare:

```bash
mount -t tmpfs tmpfs /mnt 2>&1 | head -1
unshare -U bash -c whoami 2>&1 | head -1
python3 -c "import ctypes; ctypes.CDLL('libc.so.6').ptrace(0, 0, 0, 0)"
```

Expected: the first two fail with `Operation not permitted`. The ptrace call returns `-1` with `errno=EPERM` or triggers `Bad system call` — seccomp BPF filters these syscalls before they reach the kernel's main dispatch.

> **seccomp BPF** is the mechanism. It maintains a list of allowed syscalls and rejects the rest. `mount()`, `ptrace()`, `reboot()`, `kexec_load()`, `unshare()` with CLONE_NEWUSER — all in the rejection list.

<!-- fold:break -->

**Step 4 — Confirm toolchain is absent.** A compromised agent with full shell access still can't compile an exploit:

```bash
which gcc g++ make netcat nc 2>&1 | head -5
```

Expected: all report `not found`. The sandbox image is minimized — development tools are removed at build time, so an attacker who achieves code execution still has to bring their own toolchain.

<!-- fold:break -->

<details>
<summary><strong>What process hardening adds up to</strong></summary>

Put together, Layer 3's defenses are:

| Mechanism | What it blocks |
|---|---|
| `run_as_user: sandbox` | Ambient privilege — the process was never root |
| Dropped capabilities (`CAP_NET_RAW`, `CAP_DAC_OVERRIDE`, `CAP_SYS_CHROOT`, etc.) | Fine-grained root-equivalent operations |
| `PR_SET_NO_NEW_PRIVS` | Privilege escalation via `execve()` of a setuid binary |
| seccomp BPF filter | Dangerous syscalls (`mount`, `ptrace`, `reboot`, `kexec_load`, `unshare(CLONE_NEWUSER)`) |
| Toolchain removal | Compiling new payloads in place |
| `ulimit -u 512` | Fork-bomb resource exhaustion |

Even if the agent is compromised, the blast radius is bounded — not zero, but well below what vanilla OpenClaw would have offered.

</details>

<!-- fold:break -->

> **What you just learned:** kernel-level containment gives you guarantees you cannot get from userspace controls. The tradeoff is rigidity — you cannot change these at operational speed. That's the price of irrevocability, and it is usually the right price to pay for the strongest boundary in your defense-in-depth stack.

<!-- fold:break -->

## Section 3 — Layer 4: Inference

The Inference layer controls **what AI model the agent uses and how credentials are handled**. Two complementary pieces live here: **credential isolation** (the agent should never hold API keys in-process) and the **Privacy Router** (which backend — local or cloud — is active). Exercises 4 and 5 cover each piece in turn.

<!-- fold:break -->

### Exercise 4: Remove the keys from the agent

> *Layers: **Inference** (credential isolation) + cross-reference to **Network** · Recalls: **Probe 3** (Spill the Keys)*

Vanilla OpenClaw dumped your `NVIDIA_API_KEY` when asked. Let's see what the sandbox has to offer.

<!-- fold:break -->

**Step 1 — Check the agent's environment.** Inside the sandbox:

```bash
env | grep -iE 'api_key|token|secret'
```

Expected: empty. The sandbox process does not inherit host-side credentials. The NVIDIA API key that vanilla OpenClaw exposed lives only on the host, in the OpenShell Gateway's provider record.

<!-- fold:break -->

**Step 2 — Make an inference call anyway.** The agent can still reach NVIDIA's inference API — through `inference.local`:

```bash
curl -s -X POST https://inference.local/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-super-120b-a12b","messages":[{"role":"user","content":"hello"}]}' \
  | head -40
```

Expected: a JSON response from the model. No auth header was set. The gateway stripped any credentials the agent might have attached and injected its own from the configured provider. **The agent proved it can perform inference without ever holding a credential.**

<!-- fold:break -->

**Step 3 — Trace the hop.** From a host terminal:

```bash
openshell logs my-assistant --since 2m | grep -iE 'inference|provider' | head -5
```

Expected: audit entries showing the request originating at `inference.local` and being forwarded upstream to the real provider (`integrate.api.nvidia.com`). The agent's side of the conversation never references the upstream host; the gateway's side never exposes it back to the agent.

<!-- fold:break -->

> **How the Privacy Router handles credentials** — per NVIDIA's OpenShell docs, the gateway resolves placeholder tokens in provider configs at request time. Placeholders are substituted in header values, Basic auth strings, query params, and URL path segments — but *never* in request bodies, cookies, or response content. If a placeholder can't be resolved, the gateway fails closed with HTTP 500 rather than passing through an unauthenticated request.

<!-- fold:break -->

#### The "both layers required" lesson

Credential isolation eliminates one attack class — *in-process secret dumps*. But it does not prevent the agent from **routing around `inference.local`** if the network policy permits direct access to a provider host. Let's try.

<!-- fold:break -->

**Step 4 — Bypass attempt.** Check the baseline. NemoClaw's default policy allows `integrate.api.nvidia.com` for `/usr/local/bin/claude` and `/usr/local/bin/openclaw`. Add `/usr/bin/curl` temporarily (host terminal):

```bash
cat > nvidia-curl.yaml <<'EOF'
network_policies:
  nvidia_curl:
    name: nvidia-curl
    endpoints:
      - host: integrate.api.nvidia.com
        port: 443
        protocol: rest
        enforcement: enforce
        access: read-write
    binaries:
      - { path: /usr/bin/curl }
EOF
openshell policy set my-assistant --policy nvidia-curl.yaml --wait
```

From the sandbox, try to call the upstream directly without a key:

```bash
curl -s -X POST https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-super-120b-a12b","messages":[{"role":"user","content":"hi"}]}'
```

Expected: a 401 Unauthorized from NVIDIA's API — the agent reached the endpoint because the network policy allowed it, but couldn't authenticate because the gateway wasn't in the loop to inject credentials.

<!-- fold:break -->

**Step 5 — Close the gap.** Remove the `nvidia_curl` block from your policy. Reapply. Confirm that `curl` can no longer reach `integrate.api.nvidia.com`. The agent is back to using only `inference.local`.

> **The lesson:** credential isolation (Layer 4) alone does not guarantee privacy. A hijacked agent could still attempt to POST sensitive data to an endpoint that *doesn't need* the gateway's credentials. Only **Network layer deny-by-default + Inference layer credential isolation** together provide the guarantee. This is defense-in-depth in action — each layer closes a gap the others leave.

<!-- fold:break -->

> **What you just learned:** credential isolation removes the agent from the credential path entirely, but the guarantee depends on network policy also blocking direct access to upstream providers. Neither layer alone is sufficient. Both together give you the property that a compromised agent cannot exfiltrate to a hardcoded URL *and* cannot use your keys to do so.

<!-- fold:break -->

### Exercise 5: Route sensitive queries locally

> *Layer: **Inference** (Privacy Router + your content classifier)*

The Privacy Router's marketing line — *"keep sensitive data private"* — is often misread as "the router inspects content and routes sensitive queries to a local model automatically." That's not what it does. The Privacy Router is an **operator-chosen, credential-isolating HTTP forwarder**: you decide which backend is active; the router enforces that choice. Content-aware routing is something you build *on top*.

<!-- fold:break -->

**Step 1 — See what's active.** From the host:

```bash
openshell inference get
```

Expected: a provider name (e.g. `nvidia-prod`) and a model name (e.g. `nvidia/nemotron-3-super-120b-a12b`). One provider + one model per gateway is the design — every sandbox attached to this gateway sees the same `inference.local` backend.

<!-- fold:break -->

**Step 2 — Register a local provider.** Three paths depending on your environment:

<details>
<summary><strong>Path A: DGX Spark (recommended by NVIDIA)</strong></summary>

Follow the Ollama setup from [NVIDIA's NemoClaw Spark instructions](https://build.nvidia.com/spark/nemoclaw/instructions) Step 2:

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama
ollama pull nemotron-3-super:120b
```

Register the provider with OpenShell:

```bash
openshell provider create --name local-nemotron --type openai \
    --config OPENAI_BASE_URL=http://host.docker.internal:11434/v1
```

</details>

<details>
<summary><strong>Path B: Any Linux host with modest resources</strong></summary>

Use a smaller Ollama model that fits on the workshop's available memory:

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama
ollama pull llama3.2:3b
```

Register:

```bash
openshell provider create --name local-ollama --type openai \
    --config OPENAI_BASE_URL=http://host.docker.internal:11434/v1
```

If `host.docker.internal` doesn't resolve in your environment (common on some Linux Docker installs), substitute the Docker-host IP:

```bash
DOCKER_HOST_IP=$(cat /proc/net/route | awk 'NR==2{printf "%d.%d.%d.%d\n", "0x"substr($3,7,2), "0x"substr($3,5,2), "0x"substr($3,3,2), "0x"substr($3,1,2)}')
openshell provider create --name local-ollama --type openai \
    --config OPENAI_BASE_URL=http://${DOCKER_HOST_IP}:11434/v1
```

</details>

<details>
<summary><strong>Path C: No Ollama available</strong></summary>

Register a second NVIDIA-endpoint provider with a different model, and treat it as *"the pretend local model."* The swap mechanic is identical; only the upstream destination differs.

```bash
openshell provider create --name nvidia-nano --type nvidia --from-existing
```

</details>

<!-- fold:break -->

**Step 3 — Swap the active backend.** From the host:

```bash
openshell inference set --provider local-nemotron --model nemotron-3-super:120b
# or: --provider local-ollama --model llama3.2:3b
# or: --provider nvidia-nano --model nvidia/nemotron-nano-4b-instruct
```

Within about 5 seconds, the change propagates to every sandbox on this gateway. No sandbox restart needed. Verify from inside the sandbox:

```bash
curl -s https://inference.local/v1/models | head -20
```

Expected: the advertised model matches what you just selected. **Agent code hasn't changed — the agent still POSTs to `inference.local`.** Only the operator-side routing target changed.

<!-- fold:break -->

> This is Privacy Router in action: a policy-driven routing decision, where the "policy" is the operator's choice of active backend. It keeps sensitive context on local compute when the operator points it at a local model, and releases to the frontier when the operator allows that. There is no per-request content inspection — that's a feature the operator builds in front.

<!-- fold:break -->

#### Building the classifier in front

**Step 4 — Python sidekick: build a content classifier.** Open <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 2');"><i class="fas fa-code"></i> # TODO: Exercise 2</button> and complete `classify_sensitivity()`. This is *your* classifier — the piece that decides whether a piece of text should go to the local model or the cloud model *before* the inference call is made. Three classes of signal:

| Class | Pattern | Routing decision |
|---|---|---|
| PII (SSN, email, credit card) | regex patterns | **local** — do not leave the machine |
| Proprietary ("confidential", "internal only", "trade secret") | keyword match | **local** — stays on trusted infra |
| Public (none of the above) | — | **cloud** — fine for frontier models |

<details>
<summary><strong>🆘 Need some help?</strong></summary>

```python
def classify_sensitivity(text: str) -> SensitivityClassification:
    detected_patterns = []
    pii_patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    }
    for pattern_name, regex in pii_patterns.items():
        if re.search(regex, text):
            detected_patterns.append(pattern_name)

    proprietary_keywords = ["confidential", "proprietary", "internal only", "trade secret"]
    text_lower = text.lower()
    for keyword in proprietary_keywords:
        if keyword in text_lower:
            detected_patterns.append(f"proprietary:{keyword}")

    if any(p in detected_patterns for p in ["ssn", "email", "credit_card"]):
        level = SensitivityLevel.RESTRICTED
        route_to = "local"
        reasoning = f"PII detected ({', '.join(p for p in detected_patterns if not p.startswith('proprietary:'))}) — must stay on local infrastructure"
    elif any(p.startswith("proprietary:") for p in detected_patterns):
        level = SensitivityLevel.CONFIDENTIAL
        route_to = "local"
        reasoning = f"Proprietary markers detected — route to local inference"
    else:
        level = SensitivityLevel.PUBLIC
        route_to = "cloud"
        reasoning = "No sensitive patterns detected — safe for cloud routing"

    return SensitivityClassification(
        text_preview=text[:100],
        level=level,
        detected_patterns=detected_patterns,
        route_to=route_to,
        reasoning=reasoning,
    )
```

</details>

<!-- fold:break -->

Test against the fixture:

```bash
cd /project/code/6-agent-safety
python -c "
import json
from agent_safety import classify_sensitivity
for doc in json.load(open('test_data/mixed_sensitivity_corpus.json'))[:5]:
    r = classify_sensitivity(doc['text'])
    print(f'{doc[\"id\"]} → {r.level} → {r.route_to}')
"
```

Expected: PII docs → `restricted` → `local`; proprietary → `confidential` → `local`; public → `public` → `cloud`.

<!-- fold:break -->

**Step 5 — Wire it to a routing decision (sketch).** Your classifier returns a route target; your agent code consults it before calling `inference.local`. In pseudocode:

```python
classification = classify_sensitivity(user_prompt)
if classification.route_to == "local":
    subprocess.run(["openshell", "inference", "set", "--provider", "local-ollama", ...])
response = call_inference_local(user_prompt)
```

In practice you'd do this at the gateway layer, not by swapping providers per-request (the swap is gateway-wide). Architectures we've seen in the wild:

- **Inside agent code**: agent consults classifier before deciding which endpoint / provider to use. Simple but agent-trusted.
- **Agent-side proxy**: a sidecar process inspects outbound `/v1/chat/completions` requests and decides routing. Untrusted to the agent.
- **External DLP service**: a full data-loss-prevention gateway in front of `inference.local`. Highest assurance, most operational cost.

OpenShell does not ship any of these out of the box today — the base product stops at operator-chosen routing + credential isolation. Classification is yours to build. The test fixture + classifier you just wrote is the starting point.

<!-- fold:break -->

<details>
<summary><strong>Limitations of regex-based classification</strong></summary>

| Approach | Speed | Precision | Recall | Handles context |
|---|---|---|---|---|
| **Regex patterns** | Sub-ms | Medium — false positives on number sequences | Medium — misses redacted or formatted PII | No |
| **NER models** (spaCy, Presidio) | ~10ms | High | High for trained entity types | Partially |
| **LLM-based classification** | ~500ms | Very high | Very high | Yes — understands context |
| **Hybrid** (regex + NER + LLM) | ~50ms | Very high | Very high | Yes |

Common failure modes: the SSN regex matches any 9-digit number in XXX-XX-XXXX format (product codes, serial numbers). A redacted SSN like `***-**-6789` won't match. "My phone number is 555-12-3456" triggers a false positive. For production, cascade regex (fast, cheap) with NER (accurate) and LLM classification (contextual) — escalate to slower models only when the fast check is ambiguous.

</details>

<!-- fold:break -->

> **What you just learned:** Privacy Router is operator-chosen routing + credential isolation. That mechanic is solid and useful. Content-aware routing — the behavior often implied by the marketing — is a pattern you build on top of it, and the design space has tradeoffs across speed, precision, and trust boundary.

<!-- fold:break -->
