# Module 6 Diagrams — tutor reference

Help a learner read the agent-safety figures. Diagrams in `.devx/6-agent-safety/img/`.

## enforcement_spectrum (`enforcement_spectrum.mmd`)
- **Depicts:** three grouped columns — **M4 Application** (regex check, command allowlist,
  HITL gate) → **M5 Container** (Docker namespace, resource limits, no host mounts) → **M6
  Kernel** (Landlock, seccomp, network proxy, Privacy Router) — with labeled **gaps** between
  ("agent can bypass app controls", "no per-file/per-endpoint granularity").
- **Takeaway:** the workshop's whole safety arc — *trust the model → trust the container →
  trust the kernel*. Each stage closes a gap the previous can't.

## defense_layers_comparison (`defense_layers_comparison.mmd`)
- **Depicts:** 8 stacked layers from closest-to-user to closest-to-hardware: HITL (M4) →
  Allowlists (M4) → App Sandbox (M5) → Docker (M5) → Landlock (M6) → seccomp (M6) → Network
  Proxy (M6) → Privacy Router (M6).
- **Takeaway:** **defense in depth** — an attacker must defeat *all* layers; each is
  independent. M6 adds the kernel + data layers (green).

## nemoclaw_stack (`nemoclaw_stack.mmd`)
- **Depicts:** the full stack — `OpenClaw Agent → Content Classifier (your code, Exercise 5)
  → Privacy Router (inference.local: credential injection + operator-chosen backend) →
  {Nemotron local | Cloud model}`; `OpenShell Runtime` enforces the agent; `Policy YAML +
  openshell inference set` configures OpenShell and sets the active backend.
- **Takeaway:** shows *exactly* where the **Content Classifier is your code** (not the router)
  and that the **Policy/operator** sets the backend the router enforces — the Privacy Router
  correctness point, drawn out. Note the classifier sits *in front of* the router.

## openshell_architecture (`openshell_architecture.mmd`)
- **Depicts:** `OpenClaw Agent Process` wrapped by the `OpenShell Runtime` with three layers:
  Filesystem (Landlock LSM, kernel 5.13+; read-only vs read-write paths), Process (seccomp,
  `run_as_user: agent`, syscall filtering), Network (HTTP CONNECT proxy + policy engine:
  ALLOW specific hosts/methods, DENY everything else).
- **Takeaway:** OpenShell's **out-of-process** enforcement — the policy lives outside the
  agent, so the agent can't lift it.

## privacy_router_flow / credential_flow (`privacy_router_flow.mmd`, `credential_flow_dark.svg`)
- **Depict:** the inference request path — the agent calls `inference.local` with no key;
  OpenShell **strips** any sandbox creds and **injects** the host-side Provider credential,
  then forwards to the real endpoint; the response returns. The agent never holds the key.
- **Takeaway:** credential isolation — and (per `nemoclaw_stack`) the operator, not the agent,
  chooses the backend. **Not** content inspection.

## safety_pipeline (`safety_pipeline_dark.svg`) & nemoclaw_architecture / _deployment (svg)
- **safety_pipeline:** the eval flow — red-team probes → violation checks → LLM-judge →
  aggregate score (Exercise 6).
- **nemoclaw_architecture / _deployment:** architecture and deployment views of the same
  OpenClaw + OpenShell + Nemotron + Privacy Router stack.

## Common confusions
- In `nemoclaw_stack`, the **Content Classifier is labeled "your code, Exercise 5"** — it is
  *not* part of the Privacy Router. This is the most-misread point in the module.
- The enforcement_spectrum "gaps" are the *reason* each layer exists — point a confused
  learner at the gap label, not just the boxes.
