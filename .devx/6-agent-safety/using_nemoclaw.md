# Working with NemoClaw

<img src="_static/robots/supervisor.png" alt="NemoClaw Hands-On Robot" style="float:right;max-width:300px;margin:25px;" />

Your NemoClaw sandbox is running. The agent lives inside four enforcement layers: **Network** (egress policy), **Filesystem** (Landlock), **Process** (seccomp + least privilege), and **Inference** (Privacy Router). Reading about those layers and *feeling* them are very different things. This page walks you through five hands-on exercises that turn each layer into a copy-pasteable experience — and revisit the four probes from the [previous page](setup_openclaw) to see NemoClaw shut them down.

| # | Exercise | Layer | Recalls |
|---|---|---|---|
| 1 | Stop the agent from phoning home | Network | Probe 1 |
| 2 | Not all allow-rules are equal | Network (L7 vs L4) | — |
| 3 | Make containment irrevocable | Filesystem + Process | Probe 2 |
| 4 | Remove the keys from the agent | Inference + Network | Probe 3 |
| 5 | Route sensitive queries locally | Inference | — |

> Each exercise follows a simple pattern: **recall** the vanilla behavior, **observe** it against the sandbox, **harden** with a policy, and **validate** the outcome. Python sidekicks — short TODOs in <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 1');"><i class="fas fa-code"></i> agent_safety.py</button> — let you automate the same checks for CI/CD. Once you've finished this page, head to [Evaluating Agent Safety](evaluating_safety) for the red-team + continuous-evaluation capstone.

<!-- fold:break -->

## Section 1 — Layer 1: Network (Egress Policy)

The Network layer controls **where the agent can reach**. NemoClaw's baseline is deny-by-default: every outbound connection is blocked unless a policy entry explicitly allows it. Network policy is the one enforcement layer that hot-reloads without sandbox recreation — operators can grant (or revoke) access on a running agent.

<!-- fold:break -->

### Exercise 1: Stop the agent from phoning home

> *Layer: **Network** · Recalls: **Probe 1** (Phone Home)*

Vanilla OpenClaw fetched `https://httpbin.org/ip` for you on the previous page. Let's see what happens inside the NemoClaw sandbox — then write a policy that grants access on purpose.

<details>
<summary><strong>Step 1 — Observe the deny</strong></summary>

From inside the sandbox:

```bash
nemoclaw my-assistant connect
curl -s https://httpbin.org/ip
```

Expected output:

```text
curl: (56) Received HTTP code 403 from proxy after CONNECT
```

The proxy intercepted your request, checked the policy, found no matching `network_policies` entry for `httpbin.org:443`, and returned a 403. This is the same probe from vanilla OpenClaw — the behavior has changed because the infrastructure has.

</details>

<details>
<summary><strong>Step 2 — Read the baseline policy</strong></summary>

From a host terminal (outside the sandbox):

```bash
openshell policy get my-assistant
```

You'll see three sections: `filesystem_policy` and `process` (both static — locked at creation) and `network_policies` (dynamic — hot-reloadable). `httpbin.org` is nowhere in `network_policies`, so the proxy denied it.

</details>

<details>
<summary><strong>Step 3 — Write and apply a policy</strong></summary>

On the host, create `httpbin-readonly.yaml`:

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

Apply to the live sandbox:

```bash
openshell policy set my-assistant --policy httpbin-readonly.yaml --wait
```

The `--wait` flag blocks until the proxy picks up the new rule. **No sandbox restart required** — this is dynamic enforcement in action.

</details>

<details>
<summary><strong>Step 4 — Confirm the change</strong></summary>

Back inside the sandbox:

```bash
curl -s https://httpbin.org/ip
```

Expected: a JSON response with your origin IP. The agent can now reach `httpbin.org`.

> Remember this for Exercise 3 — **filesystem** policy is *static*. You cannot change it on a running sandbox. Different layers, different tradeoffs.

</details>

<details>
<summary><strong>Step 5 — Python sidekick: validate the policy</strong></summary>

Open <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 1');"><i class="fas fa-code"></i> # TODO: Exercise 1</button> and complete `load_and_validate_policy()`. It checks three classes of violation: root process identity (critical), overly-broad writable paths like `/`, `/etc`, `/usr`, `/var` (critical), and missing network controls (warning).

Test against the two fixtures in `policies/`:

```bash
cd /project/code/6-agent-safety
python -c "from agent_safety import load_and_validate_policy; r = load_and_validate_policy('policies/baseline_permissive.yaml'); print(r.is_safe, len(r.violations))"
```

Expected: `False 3`. Wire this into CI and weak policies never reach a sandbox.

<details>
<summary>🆘 Need some help?</summary>

```python
def load_and_validate_policy(policy_path: str) -> PolicyValidationResult:
    with open(policy_path, "r") as f:
        policy_data = yaml.safe_load(f)

    violations = []
    process_config = policy_data.get("process", {})
    if process_config.get("run_as_user", "") in ("root", "0"):
        violations.append(PolicyViolation(
            rule="runs_as_root", severity="critical",
            description="Agent runs as root — a compromised agent with root access owns the entire system",
        ))

    fs_policy = policy_data.get("filesystem_policy", {})
    for path in fs_policy.get("read_write", []):
        if path in ["/", "/etc", "/usr", "/var"]:
            violations.append(PolicyViolation(
                rule="overly_broad_write", severity="critical",
                description=f"Write access to '{path}' is overly broad — agent can modify system files",
            ))

    if not policy_data.get("network_policies") and policy_data.get("default_network_action", "") != "deny":
        violations.append(PolicyViolation(
            rule="no_network_controls", severity="warning",
            description="No network controls defined — agent can reach any endpoint on the internet",
        ))

    has_critical = any(v.severity == "critical" for v in violations)
    return PolicyValidationResult(
        policy_path=policy_path, policy_data=policy_data,
        violations=violations, is_safe=not has_critical,
    )
```

</details>

</details>

> **What you just learned:** deny-by-default is the posture, hot-reload is the operational affordance, and programmatic validation is the safety net that catches policy regressions before they hit production.

<!-- fold:break -->

### Exercise 2: Not all allow-rules are equal

> *Layer: **Network** (L7 vs L4) · Continues from Exercise 1*

You wrote `access: read-only` in Exercise 1. Let's find out what that actually enforces — and what it doesn't.

<details>
<summary><strong>Step 1 — Try a POST against the read-only endpoint</strong></summary>

From inside the sandbox:

```bash
curl -s -X POST https://httpbin.org/post -H "Content-Type: application/json" -d '{"test": true}'
```

Expected: blocked at the L7 layer. Check the deny from a host terminal:

```bash
openshell logs my-assistant --since 2m | grep "OCSF HTTP"
```

Look for: `OCSF HTTP:POST [MED] DENIED POST https://httpbin.org/post [policy:httpbin_access engine:opa]`. The proxy terminated TLS, inspected the HTTP request, and denied the POST because `access: read-only`. That's L7 — layer 7 — enforcement.

</details>

<details>
<summary><strong>Step 2 — Remove the L7 hint and watch the POST slip through</strong></summary>

Edit `httpbin-readonly.yaml`: change `protocol: rest` to `protocol: tcp` (or omit the `protocol:` line). Reapply with `openshell policy set --wait`. Retry the POST — it succeeds.

**Why?** Without `protocol: rest`, the proxy treats the rule as plain TCP — binary/host/port match pass, then *any* payload tunnels through. `access: read-only` is meaningless at the TCP layer.

Restore `protocol: rest` and reapply. POST is blocked again.

</details>

<details>
<summary><strong>Step 3 — Scope rules by binary</strong></summary>

A rule for `/usr/bin/curl` does **not** cover `/usr/bin/python3`. From the sandbox, try Python against the same endpoint your policy allows for curl:

```bash
python3 -c "import urllib.request; print(urllib.request.urlopen('https://httpbin.org/ip').read())"
```

Expected: `urllib.error.URLError` — the proxy denied Python because it isn't in the binary list. Add `- { path: /usr/bin/python3 }` to the policy's `binaries`, reapply, re-run. Python now succeeds.

</details>

> **What you just learned:** three things make a network allow-rule precise — host+port, L7 method constraint via `protocol: rest` + `access`, and binary identity. Leave any one coarse and you've left room for unexpected behavior.

<!-- fold:break -->

## Section 2 — Layers 2 & 3: Filesystem + Process (kernel-level containment)

Layers 2 and 3 share an exercise because they're both **kernel-level, static containment**. They're set once when the sandbox is created, locked in by the kernel, and unchangeable from inside the agent process by design. That tradeoff — stronger guarantee for less flexibility — is the core teaching point.

<!-- fold:break -->

### Exercise 3: Make containment irrevocable

> *Layers: **Filesystem** (Landlock) + **Process** (seccomp, non-root, dropped capabilities) · Recalls: **Probe 2** (Read the Diary)*

Vanilla OpenClaw let the agent read `/etc/passwd` without complaint. Let's see what the sandbox allows.

#### Part A — Filesystem (Landlock LSM)

<details>
<summary><strong>Step 1 — Reads often still work</strong></summary>

```bash
cat /etc/passwd | head -3
```

Expected: the first three entries print. Landlock baselines `/etc` as read-only because agents often legitimately need to read config-like files. Reads through pre-approved paths still succeed — the goal is containment, not starvation.

</details>

<details>
<summary><strong>Step 2 — Writes are where the kernel stops you</strong></summary>

```bash
echo "malicious" > /etc/passwd
echo "also malicious" > /usr/bin/evil
echo "unreachable at all" > /opt/foo
```

Expected: all three fail with `Permission denied`. This isn't a POSIX permission error — it's Landlock refusing the syscall at the kernel level before it reaches the path.

</details>

<details>
<summary><strong>Step 3 — Try two bypasses, watch both fail</strong></summary>

Landlock claims irrevocability. Let's stress-test:

```bash
# Symlink trick
ln -s /etc/passwd /sandbox/fake_passwd && echo "oops" > /sandbox/fake_passwd

# Subprocess spawn
bash -c "echo oops > /etc/passwd"
```

Both fail. Landlock resolves paths at the kernel before the syscall, so symlinks don't trick it. Subprocesses inherit the restriction because `PR_SET_NO_NEW_PRIVS` is set.

> This is what *"irrevocable by design"* means. A compromised agent cannot ask politely to be let out — the kernel enforces, not userspace.

</details>

<details>
<summary><strong>Step 4 — Static vs dynamic: try to hot-reload filesystem policy</strong></summary>

From a host terminal:

```bash
cat > fs-widen.yaml <<'EOF'
filesystem_policy:
  read_write: [/sandbox, /tmp, /dev/null, /etc]
EOF
openshell policy set my-assistant --policy fs-widen.yaml --wait
```

Expected: either the `filesystem_policy` field is rejected outright, or silently accepted but not applied. **Filesystem policy is creation-time only.** To change it, `nemoclaw my-assistant destroy` + re-onboard. This rigidity is intentional — the strongest containment boundary shouldn't be reachable at operational speed.

</details>

#### Part B — Process hardening (seccomp + non-root + dropped capabilities)

Filesystem containment keeps the agent *out of places*. Process hardening keeps the agent from *becoming something it shouldn't be*.

<details>
<summary><strong>Step 1 — Confirm non-root identity</strong></summary>

```bash
whoami; id
```

Expected: `sandbox` user, `sandbox` group, no sudoer status.

</details>

<details>
<summary><strong>Step 2 — Try to escalate</strong></summary>

```bash
sudo -n whoami 2>&1 | head -1
mount -t tmpfs tmpfs /mnt 2>&1 | head -1
unshare -U bash -c whoami 2>&1 | head -1
```

Expected: all three fail with `Operation not permitted`. Capabilities are dropped, `no-new-privileges` is set, and seccomp BPF rejects dangerous syscalls (`mount`, `unshare(CLONE_NEWUSER)`, `ptrace`, `reboot`, `kexec_load`) before they reach the kernel's main dispatch.

</details>

<details>
<summary><strong>Step 3 — Confirm toolchain is absent</strong></summary>

```bash
which gcc g++ make netcat nc 2>&1 | head -5
```

Expected: all report `not found`. An attacker who achieves code execution still has to bring their own compiler.

</details>

<details>
<summary><strong>What process hardening adds up to</strong></summary>

| Mechanism | What it blocks |
|---|---|
| `run_as_user: sandbox` | Ambient privilege — the process was never root |
| Dropped capabilities (`CAP_NET_RAW`, `CAP_DAC_OVERRIDE`, `CAP_SYS_CHROOT`, etc.) | Fine-grained root-equivalent operations |
| `PR_SET_NO_NEW_PRIVS` | Privilege escalation via `execve()` of a setuid binary |
| seccomp BPF filter | Dangerous syscalls (mount, ptrace, reboot, kexec_load, unshare-user) |
| Toolchain removal | Compiling new payloads in place |
| `ulimit -u 512` | Fork-bomb resource exhaustion |

Even if the agent is compromised, the blast radius is bounded.

</details>

> **What you just learned:** kernel-level containment gives guarantees userspace controls cannot. The tradeoff is rigidity — you cannot change these at operational speed, and that's usually the right price for the strongest boundary in your defense-in-depth stack.

<!-- fold:break -->

## Section 3 — Layer 4: Inference

The Inference layer controls **what AI model the agent uses and how credentials are handled**. Two complementary pieces live here: **credential isolation** (the agent should never hold API keys in-process) and the **Privacy Router** (which backend — local or cloud — is active). Exercises 4 and 5 cover each piece.

<!-- fold:break -->

### Exercise 4: Remove the keys from the agent

> *Layers: **Inference** (credential isolation) + cross-reference to **Network** · Recalls: **Probe 3** (Spill the Keys)*

Vanilla OpenClaw dumped your `NVIDIA_API_KEY` when asked. Let's see what the sandbox has to offer.

<details>
<summary><strong>Step 1 — Check the agent's environment</strong></summary>

Inside the sandbox:

```bash
env | grep -iE 'api_key|token|secret'
```

Expected: empty. The sandbox process does not inherit host-side credentials. The NVIDIA API key lives only on the host, in the OpenShell Gateway's provider record.

</details>

<details>
<summary><strong>Step 2 — Make an inference call anyway</strong></summary>

```bash
curl -s -X POST https://inference.local/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-super-120b-a12b","messages":[{"role":"user","content":"hello"}]}' \
  | head -20
```

Expected: a valid JSON response. No auth header was set. The gateway stripped any credentials the agent might have attached and injected its own from the configured provider. **The agent performed inference without ever holding a credential.**

> Per the OpenShell docs, the gateway resolves placeholder tokens in provider configs in header values, Basic auth strings, query params, and URL path segments — but *never* in request bodies, cookies, or response content. If a placeholder can't be resolved, the gateway fails closed with HTTP 500 rather than passing through an unauthenticated request.

</details>

#### The "both layers required" lesson

Credential isolation removes one attack class — *in-process secret dumps*. It does not prevent the agent from routing around `inference.local` if the network policy permits direct access to a provider host.

<details>
<summary><strong>Step 3 — Bypass attempt: add curl to the NVIDIA endpoint's allow-list</strong></summary>

From the host:

```bash
cat > nvidia-curl.yaml <<'EOF'
network_policies:
  nvidia_curl:
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

Expected: **401 Unauthorized**. The agent reached the endpoint because the network policy allowed it, but couldn't authenticate without the gateway. That's the point: a hijacked agent could have POSTed sensitive data as the request body, and while the call would fail auth, the data has already left the sandbox.

</details>

<details>
<summary><strong>Step 4 — Close the gap</strong></summary>

Remove the `nvidia_curl` block and reapply. `curl` can no longer reach `integrate.api.nvidia.com`; the agent is back to using only `inference.local`.

</details>

> **The lesson:** credential isolation (Layer 4) alone does not guarantee privacy. Only **Network layer deny-by-default + Inference layer credential isolation** together give you the property that a compromised agent cannot exfiltrate to a hardcoded URL *and* cannot use your keys to do so. Neither alone is sufficient — that's defense-in-depth.

<!-- fold:break -->

### Exercise 5: Route sensitive queries locally

> *Layer: **Inference** (Privacy Router + your content classifier)*

The Privacy Router's marketing line — *"keep sensitive data private"* — is often misread as "the router inspects content and routes sensitive queries to a local model automatically." That's not what it does. The Privacy Router is an **operator-chosen, credential-isolating HTTP forwarder**: you decide which backend is active; the router enforces that choice. Content-aware routing is something you build *on top*.

<details>
<summary><strong>Step 1 — See what's active</strong></summary>

From the host:

```bash
openshell inference get
```

Expected: one provider + one model (e.g. `nvidia-prod` / `nvidia/nemotron-3-super-120b-a12b`). Every sandbox on this gateway sees the same `inference.local` backend.

</details>

<details>
<summary><strong>Step 2 — Register a local Ollama provider and swap to it</strong></summary>

Pull a small Ollama model (replace with `nemotron-3-super:120b` if you're on a DGX Spark per [NVIDIA's setup guide](https://build.nvidia.com/spark/nemoclaw/instructions) Step 2):

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload && sudo systemctl restart ollama
ollama pull llama3.2:3b
```

Register and activate:

```bash
openshell provider create --name local-ollama --type openai \
    --config OPENAI_BASE_URL=http://host.docker.internal:11434/v1
openshell inference set --provider local-ollama --model llama3.2:3b
```

If `host.docker.internal` doesn't resolve, substitute the Docker-host IP from `cat /proc/net/route`.

Within ~5 seconds, the swap propagates to every sandbox. Verify from inside:

```bash
curl -s https://inference.local/v1/models | head -10
```

The advertised model changed. **Agent code didn't** — the agent still POSTs to `inference.local`. Only the operator-side routing target changed.

</details>

> This is Privacy Router in action: operator-chosen routing enforced at the gateway. Sensitive context stays on local compute when the operator points `inference.local` at a local model, and routes to the frontier when the operator allows that. There is no per-request content inspection — that's a feature you build in front.

<details>
<summary><strong>Step 3 — Python sidekick: build the content classifier</strong></summary>

Open <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 2');"><i class="fas fa-code"></i> # TODO: Exercise 2</button> and complete `classify_sensitivity()`. It scans for three signal classes:

| Class | Pattern | Route to |
|---|---|---|
| PII (SSN, email, credit card) | regex | local |
| Proprietary ("confidential", "internal only", "trade secret") | keyword | local |
| Public (none above) | — | cloud |

Your classifier decides before the call which backend to use (e.g. `openshell inference set` swaps, or the agent routes to an endpoint you've pre-approved). OpenShell ships the routing primitive; the classification layer is yours.

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

Expected: PII → `restricted` → `local`; proprietary → `confidential` → `local`; public → `public` → `cloud`.

<details>
<summary>🆘 Need some help?</summary>

```python
def classify_sensitivity(text: str) -> SensitivityClassification:
    detected_patterns = []
    pii_patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    }
    for name, regex in pii_patterns.items():
        if re.search(regex, text):
            detected_patterns.append(name)

    for keyword in ["confidential", "proprietary", "internal only", "trade secret"]:
        if keyword in text.lower():
            detected_patterns.append(f"proprietary:{keyword}")

    if any(p in detected_patterns for p in ["ssn", "email", "credit_card"]):
        level, route_to = SensitivityLevel.RESTRICTED, "local"
        reasoning = f"PII detected — must stay on local infrastructure"
    elif any(p.startswith("proprietary:") for p in detected_patterns):
        level, route_to = SensitivityLevel.CONFIDENTIAL, "local"
        reasoning = "Proprietary markers — route to local inference"
    else:
        level, route_to = SensitivityLevel.PUBLIC, "cloud"
        reasoning = "No sensitive patterns detected — safe for cloud routing"

    return SensitivityClassification(
        text_preview=text[:100], level=level,
        detected_patterns=detected_patterns, route_to=route_to, reasoning=reasoning,
    )
```

</details>

</details>

<details>
<summary><strong>Limitations of regex-based classification</strong></summary>

Regex is fast but imprecise. The SSN pattern matches any 9-digit `XXX-XX-XXXX` string (product codes, serial numbers), a redacted `***-**-6789` won't match, and "My phone number is 555-12-3456" triggers a false positive. In production, cascade regex → NER (Presidio, spaCy) → LLM-based classification, escalating to slower models only when the fast check is ambiguous.

</details>

> **What you just learned:** Privacy Router is operator-chosen routing + credential isolation. Content-aware routing — often implied by the marketing — is a pattern you build on top, with design-space tradeoffs across speed, precision, and trust boundary.

<!-- fold:break -->

## What's Next

You've hardened the runtime: deny-by-default network egress, kernel-level filesystem + process containment, credential isolation, and operator-chosen inference routing. But enforcement layers contain blast radius — they don't tell you *whether* the agent is behaving safely. For that you need continuous evaluation.

> Head to [Evaluating Agent Safety](evaluating_safety) to build the red-team + LLM-as-judge safety suite that validates your hardened agent on every deployment.
