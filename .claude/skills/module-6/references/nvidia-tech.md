# Module 6 NVIDIA technologies — tutor reference

NVIDIA vs adjacent/open for the agent-safety module. Be precise — this module mixes NVIDIA
projects, an open agent framework, and Linux-kernel primitives.

## NVIDIA
- **NemoClaw** — NVIDIA's open-source **reference stack** for running OpenClaw agents securely
  (OpenClaw + OpenShell + Nemotron + Privacy Router). The `nemoclaw` CLI does host-side
  onboarding/lifecycle. github.com/NVIDIA/NemoClaw.
- **OpenShell** — NVIDIA's **kernel-level sandbox runtime**: Landlock (filesystem), seccomp +
  least privilege (process), HTTP CONNECT proxy + OPA/Rego (network), and the inference
  gateway / Privacy Router. The `openshell` CLI manages sandboxes/policies/inference.
  github.com/NVIDIA/OpenShell.
- **Privacy Router** — part of OpenShell's inference gateway: **credential injection +
  operator-chosen backend**, *not* content classification (see `concepts.md`).
- **NVIDIA Nemotron** — `nvidia/nemotron-3-super-120b-a12b` for inference *and* the
  LLM-as-judge in the safety eval (temp 0).
- **NeMo Guardrails** — NVIDIA's input/output filtering library, cited as explore-next.
  github.com/NVIDIA/NeMo-Guardrails.
- **NemoClaw Community** — community-driven examples, showcases, and integrations repo
  (blueprint recipes, field demos, launchables), cited as explore-next.
  github.com/NVIDIA/nemoclaw-community.
- **NIM / NGC** — hosted inference behind the gateway; `NVIDIA_API_KEY`.

## Adjacent / open (NOT NVIDIA — clarify)
- **OpenClaw** — the **config-first autonomous agent framework** (SOUL.md/MEMORY.md,
  heartbeat) that NemoClaw *wraps*. It's the base agent; NemoClaw + OpenShell add the
  enforcement. docs.openclaw.ai.
- **Landlock LSM** — a **Linux kernel** security module (≥ 5.13) for per-path access control.
  Kernel feature, not NVIDIA.
- **seccomp BPF** — **Linux kernel** syscall filtering. Kernel feature.
- **OPA / Rego** — Open Policy Agent (CNCF), the policy engine behind the network proxy.
- **OWASP Top-10 for Agentic Applications (ASI01–10)** — the threat taxonomy (OWASP, Dec 2025).
- **Ollama** — local model server (an option for a local Privacy Router backend).

> Clarifications learners ask: *"Is OpenClaw an NVIDIA product?"* → no — it's the open agent
> framework; **NemoClaw and OpenShell are NVIDIA's** layers around it. *"Is Landlock/seccomp
> NVIDIA?"* → no, they're Linux kernel features OpenShell *uses*. *"What's the difference
> between NemoClaw and OpenShell?"* → NemoClaw is the whole stack + host CLI; OpenShell is the
> sandbox runtime that does the actual kernel-level enforcement.
