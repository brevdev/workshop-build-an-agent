# Module 6 Diagrams — tutor reference

Help a learner read the agent-safety figures. Diagrams in `.devx/6-agent-safety/img/`.

## enforcement_spectrum (`enforcement_spectrum.mmd`)
- **Depicts:** three grouped columns — **M4 Application** (regex check, command allowlist,
  HITL gate) → **M5 Container** (Docker namespace, resource limits, no host mounts) → **M6
  Kernel/gateway** (Landlock, seccomp, network proxy, Privacy Router). Arrows show what
  each stage adds; Docker also uses kernel mechanisms.
- **Takeaway:** the workshop's whole safety arc — application checks → container isolation →
  kernel and gateway policy. Compare the actual policy at each stage.

## defense_layers_comparison (`defense_layers_comparison.mmd`)
- **Depicts:** 8 complementary controls: HITL (M4) →
  Allowlists (M4) → Tool Permissions (M5) → Docker (M5) → Landlock (M6) → seccomp (M6) → Network
  Proxy (M6) → Privacy Router (M6).
- The lesson presents these as a control table, without numerical strength rankings.
- **Takeaway:** **defense in depth** — layers protect different operations. No single layer
  covers every attack. M6 adds kernel and gateway policies (green).

## nemoclaw_stack (`nemoclaw_stack.mmd`)
- **Depicts:** OpenClaw inference requests go through the Privacy Router to the
  operator-selected model. OpenShell enforces configured boundaries around the agent.
- The classifier exercise is a separate application demo. Its proposed route is not
  connected to the live inference path.

## openshell_architecture (`openshell_architecture.mmd`)
- **Depicts:** filesystem, process and network controls applied to their respective
  operations. These are not three sequential steps for every action.
- **Takeaway:** the operator sets policy outside the agent; actual boundaries depend on
  the configured paths, process identity, syscall filter and network rules.

## privacy_router_flow / credential_flow (`privacy_router_flow.mmd`, `credential_flow_dark.svg`)
- **Depict:** the inference request path — the agent calls `inference.local` with no key;
  OpenShell **strips** any sandbox creds and **injects** the host-side Provider credential,
  then forwards to the real endpoint; the response returns. The agent never holds the key.
- **Takeaway:** credential isolation — and (per `nemoclaw_stack`) the operator, not the agent,
  chooses the backend. **Not** sensitivity classification.

## safety_pipeline (`safety_pipeline_dark.svg`) & nemoclaw_architecture / _deployment (svg)
- **safety_pipeline:** policy checks → compare classification labels → run probes → review
  every completed answer → report failures and missing measurements (Exercise 6). Offline
  screening is separate from a full judged result; response text cannot prove enforcement.
- **nemoclaw_architecture / _deployment:** architecture and deployment views of the same
  OpenClaw + OpenShell + Nemotron + Privacy Router stack.

## Common confusions
- In `nemoclaw_stack`, the classifier demo is separate from the Privacy Router. It
  proposes a route; the operator configures the live route.
- These controls cover different operations; they are not a measured strength ranking or
  a sequence every attack must defeat.
