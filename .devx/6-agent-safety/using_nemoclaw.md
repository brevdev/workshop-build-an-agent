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

> Each exercise follows a simple pattern: **recall** the vanilla behavior, **observe** it against the sandbox, **harden** with a policy, and **validate** the outcome. Exercise 5 ends with an optional Python sidekick — a short TODO in <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 2');"><i class="fas fa-code"></i> agent_safety.py</button> — that wires a content classifier in front of the inference router. Once you've finished this page, head to [Evaluating Agent Safety](evaluating_safety) for the red-team + continuous-evaluation capstone.

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
curl https://httpbin.org/ip
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
openshell policy get my-assistant --full
```

You'll see three sections: `filesystem_policy` and `process` (both static — locked at creation) and `network_policies` (dynamic — hot-reloadable). `httpbin.org` is nowhere in `network_policies`, so the proxy denied it.

</details>

<details>
<summary><strong>Step 3 — Apply the policy</strong></summary>

Open <button onclick="openOrCreateFileInJupyterLab('code/6-agent-safety/policies/httpbin-readonly.yaml');"><i class="fa-solid fa-file-code"></i> httpbin-readonly.yaml</button>. We've pre-authored the **full** sandbox policy here — the baseline `filesystem_policy`, `process`, `landlock`, and the existing `network_policies` (brave, brew, pypi, …) are all included verbatim because `openshell policy set` does a full policy replacement, and the gateway will refuse a YAML that's missing the kernel-locked static layers (*"filesystem policy cannot be removed on a live sandbox"*).

The interesting part — the one new block we've added on top of the baseline — is under `network_policies.httpbin_access`:

```yaml
network_policies:
  # ... brave, brew, pypi, etc. ...
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

That's the whole rule: *let `/usr/bin/curl` reach `httpbin.org:443`, but only with read-only HTTP methods (GET/HEAD), enforced at L7*. Apply the full file to the live sandbox:

```bash
openshell policy set my-assistant --policy code/6-agent-safety/policies/httpbin-readonly.yaml --wait
```

The `--wait` flag blocks until the proxy picks up the new policy revision. **No sandbox restart required** — this is dynamic enforcement in action.

</details>

<details>
<summary><strong>Step 4 — Confirm the change</strong></summary>

Back inside the sandbox:

```bash
nemoclaw my-assistant connect
curl https://httpbin.org/ip
```

Expected: a JSON response with your origin IP. The agent can now reach `httpbin.org`.

> Remember this for Exercise 3 — **filesystem** policy is *static*. You cannot change it on a running sandbox. Different layers, different tradeoffs.

</details>

> **What you just learned:** deny-by-default is the posture, and hot-reload is the operational affordance that lets you grant scoped access to a live agent without rebuilding the sandbox.

<!-- fold:break -->

### Exercise 2: Not all allow-rules are equal

> *Layer: **Network** (L7 vs L4) · Continues from Exercise 1*

The rule you applied in Exercise 1 set `access: read-only`. Let's find out what that actually enforces — and what it doesn't.

<details>
<summary><strong>Step 1 — Try a POST against the read-only endpoint</strong></summary>

From inside the sandbox:

```bash
curl -s -X POST https://httpbin.org/post -H "Content-Type: application/json" -d '{"test": true}'
```

Expected: blocked at the L7 layer. Check the deny from a host terminal:

```bash
openshell logs my-assistant --since 2m | grep "DENIED POST"
```

Look for: 

```
[1779525948.286] [sandbox] [OCSF ] [ocsf] HTTP:POST [MED] DENIED POST http://httpbin.org:443/post [policy:httpbin_access engine:l7] [reason:L7_REQUEST deny POST httpbin.org:443/post reason=POST /post not permitted by pol...]
```

The proxy terminated TLS, inspected the HTTP request, and denied the POST because `access: read-only`. That's L7 — layer 7 — enforcement.

</details>

<details>
<summary><strong>Step 2 — Remove the L7 hint and watch the POST slip through</strong></summary>

Open <button onclick="openOrCreateFileInJupyterLab('code/6-agent-safety/policies/httpbin-readonly.yaml');"><i class="fa-solid fa-file-code"></i> httpbin-readonly.yaml</button> again and **delete the `protocol: rest` line** under `network_policies.httpbin_access.endpoints[0]`. Reapply:

```bash
openshell policy set my-assistant --policy code/6-agent-safety/policies/httpbin-readonly.yaml --wait
```

Retry the POST from inside the sandbox — it now succeeds.

**Why?** Without the L7 protocol hint, the proxy treats the rule as plain TCP — binary/host/port match pass, then *any* payload tunnels through. `access: read-only` is meaningless at the TCP layer.

Put the `protocol: rest` line back, reapply, and POST is blocked again.

</details>

<details>
<summary><strong>Step 3 — Scope rules by binary</strong></summary>

A rule for `/usr/bin/curl` does **not** cover `/usr/bin/python3`. From the sandbox, try Python against the same endpoint your policy allows for curl:

```bash
python3 -c "import urllib.request; print(urllib.request.urlopen('https://httpbin.org/ip').read())"
```

Expected: `urllib.error.URLError` — the proxy denied Python because it isn't in the binary list. Open <button onclick="openOrCreateFileInJupyterLab('code/6-agent-safety/policies/httpbin-readonly.yaml');"><i class="fa-solid fa-file-code"></i> httpbin-readonly.yaml</button>, add `- { path: /usr/bin/python3 }` under `network_policies.httpbin_access.binaries`, and reapply:

```bash
openshell policy set my-assistant --policy code/6-agent-safety/policies/httpbin-readonly.yaml --wait
```

Re-run the Python snippet from inside the sandbox — it now succeeds.

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
cat > code/6-agent-safety/policies/fs-widen.yaml <<'EOF'
version: 1
filesystem_policy:
  read_write: [/sandbox, /tmp, /dev/null, /etc]
EOF
openshell policy set my-assistant --policy fs-widen.yaml --wait
```

Expected: the gateway rejects the request with `InvalidArgument: filesystem ... cannot be changed on a live sandbox`. **Filesystem policy is creation-time only.** To change it, `nemoclaw my-assistant destroy` + re-onboard. This rigidity is intentional — the strongest containment boundary shouldn't be reachable at operational speed.

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

Expected: all three fail to escalate, each at a different layer:

| Probe | Failure |
|---|---|
| `sudo -n whoami` | `sudo: command not found` — `sudo` isn't installed in the sandbox image at all |
| `mount -t tmpfs tmpfs /mnt` | `mount: /mnt: must be superuser to use mount.` — userspace check fails before the syscall |
| `unshare -U bash -c whoami` | `unshare: unshare failed: Operation not permitted` — seccomp + dropped capabilities block the syscall |

Capabilities are dropped, `no-new-privileges` is set, and seccomp BPF rejects dangerous syscalls (`mount`, `unshare(CLONE_NEWUSER)`, `ptrace`, `reboot`, `kexec_load`) before they reach the kernel's main dispatch.

</details>

<details>
<summary><strong>Step 3 — Confirm toolchain is absent</strong></summary>

```bash
which gcc g++ make netcat nc 2>&1 | head -5
```

Expected: all report empty. An attacker who achieves code execution still has to bring their own compiler.

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

Expected output: a single line — `OPENCLAW_GATEWAY_TOKEN=...`. That's a sandbox-scoped bearer token the agent uses to reach the gateway's loopback services (e.g. `inference.local`); it isn't a vendor API key. 

Crucially, **`NVIDIA_API_KEY` is not present** — the sandbox process does not inherit host-side vendor credentials, so even if the agent gets owned and dumps `env`, the upstream provider key never leaves the host. The NVIDIA API key lives only on the host, in the OpenShell Gateway's provider record.

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
<summary><strong>Step 3 — Bypass attempt: add curl to an unrelated provider's allow-list</strong></summary>

We need a provider host that's **not** already in the baseline policy. `integrate.api.nvidia.com` won't work — the baseline `nvidia` rule already permits `/usr/bin/curl` to reach it (necessary for the gateway's own inference plumbing), so adding our rule would be a no-op. Use `api.openai.com` instead — it's denied at baseline, so adding the rule actually opens new egress:

```bash
openshell policy update my-assistant \
  --add-endpoint api.openai.com:443:read-write:rest:enforce \
  --binary /usr/bin/curl \
  --rule-name openai_curl \
  --wait
```

From the sandbox, try to call the upstream directly without a key:

```bash
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

Expected: **HTTP 401** with body `"You didn't provide an API key. ..."`. The agent reached the endpoint because the new network rule allowed it, but couldn't authenticate. That's the point: a hijacked agent could have POSTed sensitive data as the request body, and while the call fails auth, the data has already left the sandbox.

</details>

<details>
<summary><strong>Step 4 — Close the gap</strong></summary>

Exit the sandbox and remove the `openai_curl` rule with the incremental `--remove-rule` flag — no full policy reapply needed:

```bash
openshell policy update my-assistant --remove-rule openai_curl --wait
```

Retry the same curl from inside the sandbox — you should now see **HTTP 000** (the proxy denied the CONNECT). `curl` can no longer reach `api.openai.com`; the agent is back to using only `inference.local`.

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
<summary><strong>Step 2 — Swap the inference target without touching the agent</strong></summary>

The Privacy Router's headline property is that **operators choose where inference runs and the agent never sees the change**. We'll demonstrate that by switching the active model on the live gateway and watching the next request from the sandbox land on the new target.

Swap the model on the gateway. `meta/llama-3.2-3b-instruct` is a small, fast pick that obviously differs from the baseline (any catalog entry from `curl -s https://inference.local/v1/models | jq '.data[].id'` works):

```bash
sudo apt-get update && sudo apt-get install -y jq
openshell inference set --provider nvidia-prod --model meta/llama-3.2-3b-instruct
```

Within seconds, the new route propagates to every sandbox. Don't run `nemoclaw connect` for this test — connect re-pins the gateway to the sandbox's *recorded* model (stored in `~/.nemoclaw/sandboxes.json`) on every entry, which would silently roll your swap back. Instead, exec into the sandbox non-interactively from the same workbench shell, and **put a *bogus* model name in the request body** to prove the agent's request value is *ignored* by the gateway:

```bash
nemoclaw my-assistant exec -- bash -c "curl -s -X POST https://inference.local/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{\"model\":\"agent-thinks-this-matters\",\"messages\":[{\"role\":\"user\",\"content\":\"hello\"}]}' \
  | jq '{returned_model: .model, content: .choices[0].message.content}'"
```

The `returned_model` field in the response will be `"meta/llama-3.2-3b-instruct"` — the gateway-configured model — not the bogus string the agent sent. **Agent code didn't change at all.** Only the operator-side routing did.

Swap back when you're done:

```bash
openshell inference set --provider nvidia-prod --model nvidia/nemotron-3-super-120b-a12b
```

> What you just demonstrated is the **transient / runtime** half of operator routing. For **durable per-sandbox routing** (the pattern an operator would use in production: "agent A always uses local Ollama, agent B always uses cloud Nemotron"), the source of truth is the sandbox *pin* — see the first aside below.

<details>
<summary><strong>The two-layer Privacy Router model: gateway-live vs sandbox-pin</strong></summary>

When you `nemoclaw connect`, the CLI reads the entering sandbox's pin, compares it to the gateway's live route, and if they don't match it forcibly resets to the pinned model *before* opening your SSH session — printing `Switching inference route to ...` when it does. The pin wins; the live route gets reconciled.

That's why the workshop's demo above used `nemoclaw exec` (which skips reconciliation) rather than `nemoclaw connect` (which would reconcile back to the pin and hide the swap). It's also why this design is *stronger* than a single gateway-wide switch: hosting multiple sandboxes can have each pinned to a different backend, and `connect` will flip the gateway to the right one each time — so a finance-data agent can stay local while a public-Q&A agent can run in the cloud, no matter who last touched the gateway live route.

**To make a swap *durable*** for a sandbox: either re-run `nemoclaw onboard --recreate-sandbox --name <sandbox>` with the new provider/model, or (faster, for an existing sandbox) edit `~/.nemoclaw/sandboxes.json` to update the pin and then run `nemoclaw <name> connect --probe-only` to trigger the reconciliation. The gateway will flip to the new pin and stay there.

</details>

<details>
<summary><strong>Why this exercise swaps the model within `nvidia-prod` rather than the provider (e.g. to a local Ollama)</strong></summary>

A full provider swap (the "cloud → local for sensitive data" pattern) requires the OpenShell gateway to run in **cluster mode**, where the sandbox-side `inference.local` DNS proxy can be refreshed by `kubectl` against the cluster's CoreDNS. 

This workshop environment runs OpenShell in **Docker-driver mode** (a single-container deployment), and the cluster-mode DNS refresh path doesn't apply — `openshell inference set` against a different provider would succeed, but `nemoclaw connect` would detect a broken `inference.local` proxy, fail to repair it, and silently revert. 

The in-provider model swap above demonstrates the operator-chosen-routing half of the Privacy Router story end-to-end; the keep-data-local half unlocks when your gateway runs in cluster mode outside of this workshop environment.

</details>

</details>

> This is Privacy Router in action: operator-chosen routing enforced at the gateway. The same primitive that swaps a model within one provider also swaps providers entirely (cloud ↔ local) on a cluster-mode gateway, keeping sensitive context on local compute when the operator routes there. There is no per-request content inspection — that's a feature you build in front.

<details>
<summary><strong>Step 3 — Python sidekick: build the content classifier</strong></summary>

Open <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 2');"><i class="fas fa-code"></i> # TODO: Exercise 2</button> and complete `classify_sensitivity()`. It scans for three signal classes:

| Class | Pattern | Route to |
|---|---|---|
| PII (SSN, email, credit card) | regex | local |
| Proprietary ("confidential", "internal only", "trade secret") | keyword | local |
| Public (none above) | — | cloud |

Your classifier decides before the call which backend to use (e.g. `openshell inference set` swaps, or the agent routes to an endpoint you've pre-approved). OpenShell ships the routing primitive; the classification layer is yours.

Test against the fixture — the corpus has 16 entries spanning all three categories, so iterate the whole list to verify each branch fires:

```bash
cd /project/code/6-agent-safety
python -c "
import json
from agent_safety import classify_sensitivity
for doc in json.load(open('test_data/mixed_sensitivity_corpus.json')):
    r = classify_sensitivity(doc['text'])
    print(f'{doc[\"id\"]:12} → {r.level:12} → {r.route_to}')
"
```

Expected: `pii-*` rows → `restricted → local`; `prop-*` and `mixed-*` rows → `confidential → local`; `pub-*` rows → `public → cloud`.

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
