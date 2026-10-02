# Module 6 Concepts — tutor reference

Answer conceptual questions accurately and in the workshop's voice. For the
authoritative narrative, read the teaching pages in `.devx/6-agent-safety/`. **Agent
safety is the discipline; NemoClaw is one implementation.** Explaining concepts is
teaching — do it freely.

## Why agent security is a distinct discipline (`intro_agent_safety.md`)
Untrusted text can influence actions. Five properties:
1. **Blurred trust boundaries** — instructions and external data share model context;
   tool permissions need enforcement outside the model.
2. **The confused deputy** — the agent wields *your* credentials; a forged instruction
   (prompt injection) makes it act with your authority.
3. **Tool use as attack surface** — every tool is a potential privilege-escalation vector.
4. **Persistent memory** — retained MEMORY.md / diary entries can carry poisoned instructions into later sessions.
5. **Amplification through reasoning** — a small early manipulation compounds across a chain.

## The three gaps M4/M5 leave
Application allowlists (M4) and container isolation (M5) are necessary but insufficient for
*autonomous* operation:
- **No human awake** — required approvals pause work; unattended actions need explicit permissions.
- **Agent drift** — changes in memory, instructions, or context can change later behavior.
- **Mixed-sensitivity data** — container isolation does not classify content or select models by sensitivity.

**Enforcement spectrum:** application checks (M4) → container isolation (M5) →
**kernel and gateway policy** (M6: Landlock/seccomp/proxy + Privacy Router).
Use OS boundaries for child processes; prompt rules do not constrain native code.
Enforced allowlists still apply when model context changes, but permissions need review.

## Roles (use this vocabulary)
- **Operator** — host-level access to the OpenShell gateway; configures providers, sets the
  active inference backend, applies policies. *The agent cannot do these.*
- **Agent** — runs inside the sandbox under the four enforcement layers.
- **End user** — sends prompts; one step further removed.
M6's thesis: *the operator's configuration is enforced even when the agent is compromised.*

## NemoClaw = a reference stack
**OpenClaw** (the autonomous agent framework, config-first, SOUL.md/MEMORY.md, heartbeat) +
**OpenShell** (the sandbox runtime that *enforces*) + **Nemotron** (inference) + **Privacy
Router** (inference gateway). `nemoclaw` CLI = host-side onboarding/lifecycle; `openshell`
CLI = sandbox/policy/inference management. **NemoClaw enhances OpenClaw; it doesn't replace
it**. OpenClaw has its own configurable tool controls; SOUL.md is guidance, not an OS
boundary. NemoClaw adds the runtime policies studied here. A heartbeat needs a nonempty
task; the pinned OpenClaw default is 30 minutes, and an effectively empty file is skipped.

## OWASP Top-10 Agentic risks (`why_nemoclaw.md`)
Three clusters (the module's own grouping of the official OWASP list): **Goal/Identity**
(ASI01 goal hijack, ASI03 identity & privilege abuse, ASI09 human-agent trust exploitation,
ASI10 rogue agents), **Capability/Tool** (ASI02 tool misuse, ASI04 agentic supply chain,
ASI05 unexpected code execution), **State/Comms** (ASI06 context & memory poisoning, ASI07
insecure inter-agent comms, ASI08 cascading failures). No single layer covers all; hence
defense in depth. (ASI06/ASI07/ASI09/ASI10 need additional controls.) NOTE: the
official OWASP list merges Identity+Privilege into one entry (ASI03) and ends with ASI10
Rogue Agents — don't cite the old shifted numbering.

## OpenShell: out-of-process enforcement
Containers provide namespaces, mount permissions, and process controls. OpenShell adds
agent-focused policies. Its key idea:
policies are enforced **outside the agent's address space**, so agent code cannot simply
change them. Some policy information may still be observable from the sandbox. Four mechanisms: Landlock (FS), HTTP CONNECT proxy
+ OPA/Rego (network), seccomp BPF + least privilege (process), gateway routing (inference).

## The four layers
- **Network.** The proxy checks configured host, port, protocol, and executable rules.
  With `protocol: rest`, `access: read-only` restricts HTTP methods. Without HTTP inspection,
  a matching TCP rule cannot enforce methods. GET can still transmit data in a URL.
  Network rules can hot-reload; compare the
  active policy and proxy logs. An upstream timeout or 5xx does not establish a policy deny.
- **Filesystem.** Landlock applies kernel path restrictions inherited by child processes.
  Restrictions cannot be relaxed by the confined process. `no_new_privs` prevents gaining
  privileges; it is not the mechanism that inherits Landlock rules. A permission error can
  also come from ordinary POSIX permissions. Inspect the active policy rather than assuming
  every image has the same read/write paths. Changes need sandbox recreation to take effect.
- **Process.** A non-root identity, dropped capabilities, `no_new_privs`, and seccomp reduce
  privileges and available operations. The precise syscall and resource limits depend on
  the runtime and policy. A missing program is not evidence of a syscall block.
- **Inference.** The configured gateway route selects the provider and model and injects
  provider credentials. These settings can change without recreating the sandbox.

Judge output can be well-formed and wrong. Calibrate on known good and bad answers,
inspect explanations, and keep missing measurements separate from failures.

## The Privacy Router (the most-misread concept — get it right)
Two functions, both via the `inference.local` gateway:
- **Credential isolation:** the agent calls `https://inference.local/...`; the gateway
  **strips** any sandbox-supplied creds and **injects** the real key from the host-side
  **Provider** record, then forwards. With provider credentials kept on the operator side, the agent does not need that key
  in its environment. Separately injected keys would defeat this property. Policy-configured
  credential rewriting can also cover JSON bodies and WebSocket text; this is separate
  from model routing.
- **Operator-controlled routing:** the operator sets **one backend (provider+model) per
  gateway** (`openshell inference set --provider … --model …`); the router enforces that
  choice for every sandbox. It does **NOT classify sensitivity** and does **NOT auto-route
  sensitive queries**. (Demo: swap the gateway model, send a *bogus* model name from the
  sandbox — the response uses the gateway's model, proving the agent's value is ignored.)
- **The classifier is a separate exercise.** `classify_sensitivity` returns a proposed
  local/cloud route; the lab does not wire it into request handling. A production router
  needs authorized destinations and isolation between requests. Do not implement it by
  switching shared gateway state per prompt. `nemoclaw connect` may restore a sandbox's
  saved pin to that shared route; a pin is not an independent concurrent route.

## YAML policy schema
One file governs a sandbox. **Static** (locked at creation): `filesystem_policy`
(read_write/read_only), `landlock` (compatibility), `process` (user/group). **Dynamic** (hot-
reloadable): `network_policies` (map → endpoints[host/port/protocol/enforcement/access] +
binaries). Provided policies: `baseline_permissive.yaml`, `httpbin-readonly.yaml` (Ex 1–2),
`research_assistant.yaml` (a policy fixture for the evaluation suite).

## Safety evaluation (`evaluating_safety.md`, extends Module 3)
The sandbox contains actions; evaluation checks behavior, including permitted but harmful actions such as memory poisoning.
- **Screening:** 16 cases with expected behavior, including two benign controls. Canary leaks and simple compliance claims are flagged; errors and empty replies are separate missing measurements. A refusal prefix never excuses a later leak.
- **Enforcement evidence:** a claimed permission error is not proof of a kernel block. Use tool results and operator-side logs; do not assign a mechanism score from response wording.
- **Judge:** optionally reviews every completed answer against expected behavior and the full policy. Strict 1–5 JSON scores; missing or invalid results remain missing.
- **Suite:** compare classification level and route with fixture labels. Known failures block a pass. A summary score exists only when all measurements are complete.
- **Modes:** default CLI screens the mock offline; `--judge` adds hosted review. Statuses: failed, incomplete, screened, passed. A pass covers only the supplied cases.

## Source map
- Concepts → `intro_agent_safety.md`, `why_nemoclaw.md`
- Hardening → `using_nemoclaw.md` + `policies/*.yaml`; setup → `setup_openclaw.md`, `setup_nemoclaw.md`
- Evaluation → `evaluating_safety.md` + `agent_safety.py` / `safety_eval_framework.py`
