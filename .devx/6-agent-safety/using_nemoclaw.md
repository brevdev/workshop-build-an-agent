<div class="dx-hero" data-eyebrow="MODULE 06 / 05 - HANDS ON" data-title="Working with NemoClaw" data-meta="TIME::35 min|EXERCISES::5|RUNTIME::OpenShell"></div>

Your NemoClaw sandbox is running. The agent lives inside four enforcement layers: **Network** (egress policy), **Filesystem** (Landlock), **Process** (seccomp + least privilege), and **Inference** (Privacy Router). Reading about those layers and *feeling* them are very different things. This page walks you through five hands-on exercises that turn each layer into a copy-pasteable experience — and revisit the four probes from the [previous page](setup_openclaw) to distinguish model behavior from enforced restrictions.

<div class="dx-bento dx-reveal">
  <div class="dx-cell"><h4>EXERCISE 1</h4><span class="dx-big">Network</span>Stop the agent from phoning home (recalls Probe 1).</div>
  <div class="dx-cell"><h4>EXERCISE 2</h4><span class="dx-big">Network L7</span>Not all allow-rules are equal.</div>
  <div class="dx-cell"><h4>EXERCISE 3</h4><span class="dx-big">FS + Process</span>Make containment irrevocable (recalls Probe 2).</div>
  <div class="dx-cell"><h4>EXERCISE 4</h4><span class="dx-big">Inference</span>Remove the keys from the agent (recalls Probe 3).</div>
  <div class="dx-cell is-wide"><h4>EXERCISE 5</h4><span class="dx-big">Inference</span>Inspect the shared route; build a separate sensitivity classifier.</div>
</div>

> Each exercise follows a simple pattern: **recall** the vanilla behavior, **observe** it against the sandbox, **harden** with a policy, and **validate** the outcome. Exercise 5 ends with an optional Python sidekick — a short TODO in <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 2');"><i class="fas fa-code"></i> agent_safety.py</button> — that proposes a route; it does not connect that classifier to the live gateway. Once you've finished this page, head to [Evaluating Agent Safety](evaluating_safety) for the red-team + continuous-evaluation capstone.

### Before you begin — is your live sandbox up?

Exercises 1–5 include commands for the **running** NemoClaw sandbox (`nemoclaw connect`, `openshell policy set`, …). If a command hangs, or a step fails with *"sandbox not found"* or *"Cannot find module"*, your control plane is down. Check all four layers — tunnel, gateway, CLI, and sandbox — with one read-only command:

```bash
bash code/6-agent-safety/scripts/nemoclaw-health.sh
```

It reports which layer is down and prints the single command that brings the stack back: <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> → `bash code/6-agent-safety/scripts/install-nemoclaw.sh`. A healthy installation may only need its tunnel restored. Recovery can recreate gateway state; inspect the installer output and preserve any existing work before a reset. Re-run the health check afterward; you're ready when it prints **READY**.

> **Sandbox unavailable?** You can still build Exercise 5's classifier and run the [safety suite](evaluating_safety) against its offline mock. Hosted judge reviews need API access; the routing demonstration needs the live sandbox.

<!-- fold:break -->

## Section 1 — Layer 1: Network (Egress Policy)

The Network layer controls **where the agent can reach**. The workshop policy denies destinations without a matching allow rule. Inspect your active policy before testing. Network rules can hot-reload without sandbox recreation — operators can grant (or revoke) access on a running agent.

<!-- fold:break -->

### Exercise 1: Stop the agent from phoning home

> *Layer: **Network** · Recalls: **Probe 1** (Phone Home)*

Compare the `https://httpbin.org/ip` result you observed on the previous page. Let's see what happens inside the NemoClaw sandbox — then write a policy that grants access on purpose.

<details class="dx-peek">
<summary>Step 1 — Observe the deny</summary>

From a host terminal, connect and then run curl inside the sandbox:

```bash
nemoclaw my-assistant connect
curl -sS --max-time 30 https://httpbin.org/ip
```

Expected output:

```text
curl: (56) Received HTTP code 403 from proxy after CONNECT
```

The proxy intercepted your request, checked the policy, found no matching `network_policies` entry for `httpbin.org:443`, and returned a 403. This is the same probe from vanilla OpenClaw — the behavior has changed because the infrastructure has.

</details>

<details class="dx-peek">
<summary>Step 2 — Read the baseline policy</summary>

From a host terminal (outside the sandbox):

```bash
openshell policy get my-assistant --full
```

You'll see three sections: `filesystem_policy` and `process` (both static — locked at creation) and `network_policies` (dynamic — hot-reloadable). If no matching entry permits `httpbin.org`, the proxy should deny it. Remove an earlier lab rule before repeating this comparison.

</details>

<details class="dx-peek">
<summary>Step 3 — Apply the policy</summary>

Open <button onclick="openOrCreateFileInJupyterLab('code/6-agent-safety/policies/httpbin-readonly.yaml');"><i class="fa-solid fa-file-code"></i> httpbin-readonly.yaml</button> and inspect `httpbin_access`. The file is a workshop baseline example, not a snapshot of every installation. Copy your active policy first so a full replacement preserves its existing rules and static settings.

The new block is:

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
openshell policy get my-assistant --full | sed -n '/^version: /,$p' > code/6-agent-safety/policies/lab-policy.yaml
python3 - <<'PYCODE'
from pathlib import Path
import yaml
folder = Path("code/6-agent-safety/policies")
active = yaml.safe_load((folder / "lab-policy.yaml").read_text())
assert isinstance(active, dict) and "version" in active, "Policy export failed"
example = yaml.safe_load((folder / "httpbin-readonly.yaml").read_text())
active.setdefault("network_policies", {})["httpbin_access"] = example["network_policies"]["httpbin_access"]
(folder / "lab-policy.yaml").write_text(yaml.safe_dump(active, sort_keys=False))
PYCODE
openshell policy set my-assistant --policy code/6-agent-safety/policies/lab-policy.yaml --wait
```

The `--wait` flag blocks until the proxy picks up the new policy revision. **No sandbox restart required** — this is dynamic enforcement in action.

</details>

<details class="dx-peek">
<summary>Step 4 — Confirm the change</summary>

Back inside the sandbox:

```bash
nemoclaw my-assistant connect
curl -sS --max-time 30 https://httpbin.org/ip
```

Expected when httpbin is available: a JSON response with your origin IP. The agent can now reach `httpbin.org`.

> Remember this for Exercise 3 — **filesystem** policy is *static*. You cannot change it on a running sandbox. Different layers, different tradeoffs.

</details>

> **What you just learned:** deny-by-default is the posture, and hot-reload is the operational affordance that lets you grant scoped access to a live agent without rebuilding the sandbox.

<!-- fold:break -->

### Exercise 2: Not all allow-rules are equal

> *Layer: **Network** (L7 vs L4) · Continues from Exercise 1*

The rule you applied in Exercise 1 set `access: read-only`. This limits HTTP methods; GET can still transmit data in a URL. Let's test the boundary.

<details class="dx-peek">
<summary>Step 1 — Try a POST against the read-only endpoint</summary>

From inside the sandbox:

```bash
curl -sS --max-time 60 -X POST https://httpbin.org/post -H "Content-Type: application/json" -d '{"test": true}'
```

Expected: blocked at the L7 layer. Check the deny from a host terminal:

```bash
openshell logs my-assistant --since 2m | grep "DENIED POST"
```

Look for: 

```
[1779525948.286] [sandbox] [OCSF ] [ocsf] HTTP:POST [MED] DENIED POST http://httpbin.org:443/post [policy:httpbin_access engine:l7] [reason:L7_REQUEST deny POST httpbin.org:443/post reason=POST /post not permitted by pol...]
```

A `DENIED POST` log establishes that the proxy inspected and denied the HTTP method. An upstream HTTP error by itself does not. That's L7 — layer 7 — enforcement.

</details>

<details class="dx-peek">
<summary>Step 2 — Remove the L7 hint and watch the POST slip through</summary>

Open <button onclick="openExistingFileInJupyterLab('code/6-agent-safety/policies/lab-policy.yaml');"><i class="fa-solid fa-file-code"></i> lab-policy.yaml</button> again and **delete the `protocol: rest` line** under `network_policies.httpbin_access.endpoints[0]`. Reapply:

```bash
openshell policy set my-assistant --policy code/6-agent-safety/policies/lab-policy.yaml --wait
```

Retry the POST. The proxy should now permit it; an upstream 5xx or timeout is a service failure, so check the proxy log separately.

**Why?** Without the L7 protocol hint, the proxy treats the rule as plain TCP — binary/host/port match pass, then *any* payload tunnels through. `access: read-only` is meaningless at the TCP layer.

Put the `protocol: rest` line back, reapply, and POST is blocked again.

</details>

<details class="dx-peek">
<summary>Step 3 — Scope rules by binary</summary>

A rule for `/usr/bin/curl` does **not** cover `/usr/bin/python3`. From the sandbox, try Python against the same endpoint your policy allows for curl:

```bash
python3 -c "import urllib.request; print(urllib.request.urlopen('https://httpbin.org/ip').read())"
```

Expected: a proxy denial if no other rule permits Python. Check `readlink -f "$(command -v python3)"` and the deny log for the binary path to add. Open <button onclick="openExistingFileInJupyterLab('code/6-agent-safety/policies/lab-policy.yaml');"><i class="fa-solid fa-file-code"></i> lab-policy.yaml</button>, add `- { path: /usr/bin/python3 }` under `network_policies.httpbin_access.binaries`, and reapply:

```bash
openshell policy set my-assistant --policy code/6-agent-safety/policies/lab-policy.yaml --wait
```

Re-run the Python snippet. Check both the proxy decision and the upstream response.

</details>

> **What you just learned:** three things make a network allow-rule precise — host+port, L7 method constraint via `protocol: rest` + `access`, and binary identity. Leave any one coarse and you've left room for unexpected behavior.

<!-- fold:break -->

## Section 2 — Layers 2 & 3: Filesystem + Process (kernel-level containment)

<img src="_static/robots/supervisor.png" alt="NemoClaw Hands-On Robot" style="float:right;max-width:300px;margin:25px;" />

Layers 2 and 3 share an exercise because they're both **kernel-level, static containment**. They're set once when the sandbox is created, locked in by the kernel, and unchangeable from inside the agent process by design. That tradeoff — stronger guarantee for less flexibility — is the core teaching point.

<!-- fold:break -->

### Exercise 3: Make containment irrevocable

> *Layers: **Filesystem** (Landlock) + **Process** (seccomp, non-root, dropped capabilities) · Recalls: **Probe 2** (Read the Diary)*

The earlier canary tested reachable data. Here, inspect the actual filesystem and process boundaries; a public system file is not a secret.

#### Part A — Filesystem (Landlock LSM)

<details class="dx-peek">
<summary>Step 1 — Reads often still work</summary>

```bash
cat /etc/passwd | head -3
```

Expected: the first three entries print. Landlock baselines `/etc` as read-only because agents often legitimately need to read config-like files. Reads through pre-approved paths still succeed — the goal is containment, not starvation.

</details>

<details class="dx-peek">
<summary>Step 2 — Writes are where the kernel stops you</summary>

```bash
printf '%s\n' WORKSHOP-CANARY-123 > /sandbox/workshop-canary.txt
cat /sandbox/workshop-canary.txt
touch /usr/share/workshop-denied-canary
```

The workspace write should succeed; creating a file under `/usr` should fail. Ordinary Unix permissions and Landlock can both deny that write. To prove Landlock specifically, an operator must prepare a POSIX-writable canary outside the allowed write paths and compare the same UID with and without the Landlock domain. A generic “Permission denied” does not identify the layer.

</details>

<details class="dx-peek">
<summary>Step 3 — Try two bypasses, watch both fail</summary>

Landlock claims irrevocability. Let's stress-test:

```bash
# Symlink trick
ln -s /usr/share /sandbox/workshop-denied-link
touch /sandbox/workshop-denied-link/workshop-denied-canary

# Subprocess spawn
bash -c "touch /usr/share/workshop-denied-canary"
```

Both should fail under this policy. Landlock restrictions are inherited by child processes and cannot be relaxed by them; symlinks do not remove the target's restrictions. These probes also remain subject to ordinary Unix permissions.

> This is what *"irrevocable by design"* means. A compromised agent cannot ask politely to be let out — the kernel enforces, not userspace.

</details>

<details class="dx-peek">
<summary>Step 4 — Static vs dynamic: try to hot-reload filesystem policy</summary>

From a host terminal:

```bash
python3 - <<'PYCODE'
from pathlib import Path
import yaml
folder = Path("code/6-agent-safety/policies")
policy = yaml.safe_load((folder / "lab-policy.yaml").read_text())
policy["filesystem_policy"]["read_write"].append("/usr")
(folder / "fs-widen.yaml").write_text(yaml.safe_dump(policy, sort_keys=False))
PYCODE
openshell policy set my-assistant --policy code/6-agent-safety/policies/fs-widen.yaml --wait
```

Filesystem permissions are established at sandbox creation. The pinned runtime may reject this update; another version may accept a stored revision without changing the running process's Landlock domain. Recheck the denied canary: a successful policy response is not proof of wider runtime access. Restore the unchanged policy afterward:

```bash
openshell policy set my-assistant --policy code/6-agent-safety/policies/lab-policy.yaml --wait
```

</details>

#### Part B — Process hardening (seccomp + non-root + dropped capabilities)

Filesystem containment keeps the agent *out of places*. Process hardening keeps the agent from *becoming something it shouldn't be*.

<details class="dx-peek">
<summary>Step 1 — Confirm non-root identity</summary>

```bash
whoami; id
```

Expected: `sandbox` user, `sandbox` group, no sudoer status.

</details>

<details class="dx-peek">
<summary>Step 2 — Try to escalate</summary>

```bash
sudo -n whoami 2>&1 | head -1
mount -t tmpfs tmpfs /mnt 2>&1 | head -1
unshare -U bash -c whoami 2>&1 | head -1
```

Record the result and inspect the process state; messages vary by image:

| Probe | Failure |
|---|---|
| `sudo -n whoami` | `sudo: command not found` — `sudo` isn't installed in the sandbox image at all |
| `mount -t tmpfs tmpfs /mnt` | `mount: /mnt: must be superuser to use mount.` — userspace check fails before the syscall |
| `unshare -U bash -c whoami` | `unshare: unshare failed: Operation not permitted` — consistent with seccomp or capability restrictions; this message alone does not distinguish them |

Inspect `/proc/self/status` for `CapEff`, `CapBnd`, `NoNewPrivs`, and `Seccomp`. These identify enabled controls; attributing a particular syscall denial requires the filter or runtime log.

</details>

<details class="dx-peek">
<summary>Step 3 — Confirm toolchain is absent</summary>

```bash
which gcc g++ make netcat nc 2>&1 | head -5
```

Record which tools are installed. Their absence is image hardening, not a kernel boundary; interpreted code still executes.

</details>

<details class="dx-peek">
<summary>What process hardening adds up to</summary>

| Mechanism | What it blocks |
|---|---|
| `run_as_user: sandbox` | Ambient privilege — the process was never root |
| Dropped capabilities (`CAP_NET_RAW`, `CAP_DAC_OVERRIDE`, `CAP_SYS_CHROOT`, etc.) | Fine-grained root-equivalent operations |
| `PR_SET_NO_NEW_PRIVS` | Privilege escalation via `execve()` of a setuid binary |
| seccomp BPF filter | Dangerous syscalls (mount, ptrace, reboot, kexec_load, unshare-user) |
| Toolchain removal | Reduces available build tools; does not prevent interpreted payloads |
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

The baseline used a fictional environment canary. Now check whether vendor credentials are present without printing their values.

<details class="dx-peek">
<summary>Step 1 — Check the agent's environment</summary>

Inside the sandbox:

```bash
python3 - <<'PYCODE'
import os
for name in ("NVIDIA_API_KEY", "OPENAI_API_KEY", "WORKSHOP_CANARY"):
    print(f"{name}: {'present' if name in os.environ else 'absent'}")
PYCODE
```

In a clean gateway-managed setup, upstream provider keys are absent from the sandbox environment. That does not prove there are no secrets in files you uploaded. A sandbox-local OpenClaw gateway token, if present, serves a different purpose from the upstream vendor key.

</details>

<details class="dx-peek">
<summary>Step 2 — Make an inference call anyway</summary>

```bash
curl -sS --max-time 60 -X POST https://inference.local/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-super-120b-a12b","messages":[{"role":"user","content":"hello"}]}' \
  | head -20
```

Expected: a completion response. This request sends no auth header; the gateway supplies the configured upstream provider credential. An error response or timeout does not prove inference succeeded.

> The operator's provider configuration determines the upstream destination and credentials. The gateway applies that configuration when forwarding the request.

</details>

#### The "both layers required" lesson

Credential isolation removes one attack class — *in-process secret dumps*. It does not prevent the agent from routing around `inference.local` if the network policy permits direct access to a provider host.

<details class="dx-peek">
<summary>Step 3 — Bypass attempt: add curl to an unrelated provider's allow-list</summary>

Inspect the active policy for an endpoint not already allowed for curl. This example uses `api.openai.com` and sends only a harmless greeting. Gateway-managed inference does not require a direct curl allowance to the vendor host.

```bash
openshell policy update my-assistant \
  --add-endpoint api.openai.com:443:read-write:rest:enforce \
  --binary /usr/bin/curl \
  --rule-name openai_curl \
  --wait
```

From the sandbox, try to call the upstream directly without a key:

```bash
curl -sS --max-time 30 -X POST https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

Expected: **HTTP 401** with body `"You didn't provide an API key. ..."`. The agent reached the endpoint because the new network rule allowed it, but couldn't authenticate. That's the point: a hijacked agent could have POSTed sensitive data as the request body, and while the call fails auth, the data has already left the sandbox.

</details>

<details class="dx-peek">
<summary>Step 4 — Close the gap</summary>

Exit the sandbox and remove the `openai_curl` rule with the incremental `--remove-rule` flag — no full policy reapply needed:

```bash
openshell policy update my-assistant --remove-rule openai_curl --wait
```

Retry the same curl from inside the sandbox — expect a proxy CONNECT denial; confirm it in the log. `curl` can no longer reach `api.openai.com`; that direct route is closed. Other permitted endpoints still remain reachable.

</details>

> **The lesson:** credential isolation (Layer 4) alone does not guarantee privacy. Combine **Network policy + credential isolation**, and inspect allowed destinations too: permitted network requests can still carry data.

<!-- fold:break -->

### Exercise 5: Inspect and change the inference route

> *Layer: **Inference** (Privacy Router + your content classifier)*

The Privacy Router's marketing line — *"keep sensitive data private"* — is often misread as "the router inspects content and routes sensitive queries to a local model automatically." That's not what it does. The Privacy Router is an **operator-chosen, credential-isolating HTTP forwarder**: you decide which backend is active; the router enforces that choice. Content-aware routing is something you build *on top*.

<details class="dx-peek">
<summary>Step 1 — See what's active</summary>

From the host:

```bash
openshell inference get
```

Expected: one provider + one model (e.g. `nvidia-prod` / `nvidia/nemotron-3-super-120b-a12b`). Every sandbox on this gateway sees the same `inference.local` backend.

</details>

<details class="dx-peek">
<summary>Step 2 — Swap the inference target without touching the agent</summary>

The Privacy Router's headline property is that **operators choose where inference runs and the agent never sees the change**. We'll demonstrate that by switching the active model on the live gateway and watching the next request from the sandbox land on the new target.

Use the workshop's tested `fast_chat` model role. This remains hosted inference; the change demonstrates routing, not local privacy. Use a dedicated workshop gateway because this route is shared:

```bash
WORKSHOP_FAST_MODEL=$(PYTHONPATH=code python3 -c 'from workshop_support import get_model; print(get_model("fast_chat"))')
openshell inference set --provider nvidia-prod --model "$WORKSHOP_FAST_MODEL"
sleep 10
```

Updates propagate asynchronously. After the initial wait, confirm an `Inference routes updated` entry in `openshell logs my-assistant --since 1m`. Don't run `nemoclaw connect` here: connect re-pins the gateway to the sandbox's recorded model. Use `exec` and a **bogus request model** to check that the gateway applies the operator's choice:

```bash
nemoclaw my-assistant exec -- bash -c "curl -sS --max-time 60 -X POST https://inference.local/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{\"model\":\"agent-thinks-this-matters\",\"max_tokens\":256,\"chat_template_kwargs\":{\"enable_thinking\":false},\"messages\":[{\"role\":\"user\",\"content\":\"hello\"}]}' \
  | python3 -m json.tool"
```

Check that the completion's `model` field identifies the selected Lightning model rather than the bogus request value. The agent code stayed the same; the operator changed the route.

Swap back when you're done:

```bash
openshell inference set --provider nvidia-prod --model nvidia/nemotron-3-super-120b-a12b
```

The gateway route is shared in this lab. NemoClaw's connect-time pin can reset it when you enter a sandbox; that is a reconnect convenience, not concurrent per-sandbox privacy isolation. Use separate gateways or a verified sandbox-aware router before running agents with different privacy requirements together.

Provider switching depends on the installed version and driver; it is not inherently limited to cluster mode. A local route also needs a reachable local model server. This lab does not start one or automatically classify requests.

</details>

<!-- fold:break -->

<details class="dx-peek">
<summary>Step 3 — Python sidekick: build the content classifier</summary>

Open <button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 2');"><i class="fas fa-code"></i> # TODO: Exercise 2</button> and complete `classify_sensitivity()`. It scans for three signal classes:

| Class | Pattern | Route to |
|---|---|---|
| PII (SSN, email, credit card) | regex | local |
| Proprietary ("confidential", "internal only", "trade secret") | keyword | local |
| Public (none above) | — | cloud |

The classifier returns a proposed route only. A production application must enforce it before sending data; changing a shared gateway route for each prompt can race with other agents.

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

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
def classify_sensitivity(text: str) -> SensitivityClassification:
    detected_patterns = []
    pii_patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
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
        reasoning = "No configured sensitive patterns matched; this small classifier can miss other cases."

    return SensitivityClassification(
        text_preview=text[:100], level=level,
        detected_patterns=detected_patterns, route_to=route_to, reasoning=reasoning,
    )
```

</details>

</details>

<details class="dx-peek">
<summary>Limitations of regex-based classification</summary>

Regex is fast but imprecise. The SSN pattern matches any 9-digit `XXX-XX-XXXX` string (product codes, serial numbers), a redacted `***-**-6789` won't match, and "My phone number is 555-12-3456" triggers a false positive. In production, cascade regex → NER (Presidio, spaCy) → LLM-based classification, escalating to slower models only when the fast check is ambiguous.

</details>

> **What you just learned:** Privacy Router is operator-chosen routing + credential isolation. Content-aware routing — often implied by the marketing — is a pattern you build on top, with design-space tradeoffs across speed, precision, and trust boundary.

<!-- fold:break -->

## What's Next

You've hardened the runtime: deny-by-default network egress, kernel-level filesystem + process containment, credential isolation, and operator-chosen inference routing. But enforcement layers contain blast radius — they don't tell you *whether* the agent is behaving safely. For that you need continuous evaluation.

> Head to [Evaluating Agent Safety](evaluating_safety) to build a red-team and LLM-judge suite for checking the supplied safety cases.
