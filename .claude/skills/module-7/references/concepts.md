# Module 7 Concepts — tutor reference

Answer conceptual questions accurately and in the workshop's voice. For the
authoritative narrative, read the teaching pages in `.devx/7-agent-harnesses/`.
Explaining these concepts is teaching — do it freely. The token figures are
order-of-magnitude **bets the learner measures in the lab**, not a fixed scoreboard.

## Harness vs LLM — the engine and the car (`intro_agent_harnesses.md`)
The uncomfortable truth the module opens with: the LLM never remembered anything, never
called a tool, never planned a step. **The model is a stateless function** — tokens in,
tokens out. Everything that made the Module 1–6 agents *feel* like agents lived in the
**harness**: memory, tool execution, planning loops, the self-evolving SOUL.md.
- **Engine vs car:** the LLM is the engine; the harness is the chassis/transmission/fuel/
  steering. An engine on a stand goes nowhere; a car without an engine is furniture.
- **Two independent choices:** *same model + different harness* → a very different agent
  (Nemotron in a bare loop vs. inside OpenClaw are night and day); *same harness + different
  model* → the capability ceiling moves but behavior/UX stay consistent.
- Why it matters: the agent performance race is increasingly a **harness race** — models
  are converging, harnesses are differentiating.

## The five things every harness owns
From a 50-line loop to Claude Code, every harness owns the same five responsibilities. The
learner has already touched each:
1. **Memory** — what persists across sessions (OpenClaw `MEMORY.md`/`USER.md`, M6; deepagents `MemorySaver`, M5).
2. **Self-evolution** — the agent improving its own scaffolding (OpenClaw rewriting `IDENTITY.md` each heartbeat, M6).
3. **Skills** — packaged procedural knowledge loaded on demand (Superpowers, M4; skill toggles, M5).
4. **Tool calling** — schemas, execution, sandboxing, permissions, retries (MCP, M2; Docker + HITL, M5).
5. **Token efficiency** — the context window is the scarce resource (sub-agent isolation keeping context clean, M5).

Four are table stakes; **token efficiency is the one designers genuinely disagree on**, and
it's the cleanest axis for understanding the whole ecosystem.

## The context tax (`intro_agent_harnesses.md`, `harness_landscape.md`)
Every piece of harness machinery has a price paid in tokens **on every single model call**:
the system prompt, the tool schemas for every registered tool, skill descriptions, memory
excerpts, environment state. This recurring overhead is the **context tax**.
- A **maximal** harness might spend ~7,000–10,000 tokens/turn before the user says a word;
  a **minimal** one gets under ~1,000.
- Neither is wrong — they're different **bets**: *maximal* = rich built-in capability is
  worth the overhead; *minimal* = most of that machinery is documentation the model could
  load on demand, so strip the core and bet on the model.
- In the lab the learner **measures their own** numbers with `tiktoken` (Exercise 2). The
  in-page targets (minimal ≈ 400, maximal ≈ 3,922 tokens/32K) are illustrative.

## Lazy skill loading (`agent_skills.md`)
The single most effective tax cut. A harness with 30 installed skills does **not** pay for 30
sets of instructions per turn — it pays for 30 *one-line descriptions* and loads a full body
only when a skill is invoked. Eager ≈ 30 × ~1,500 = ~45,000 tokens; lazy ≈ 30 × ~25 = ~750
tokens (+ one body when used). This is pi's signature design, now standard in serious harnesses.

## The harness landscape — seven harnesses, one axis (`harness_landscape.md`)
Sort the ecosystem by **context tax**. Five open (bring any model) + two subscription:
- **pi** (open, *minimal*) — sub-1k system prompt, four tools (Read/Write/Edit/Bash), lazy
  skills, live **self-extension**. "As many as needed, as little as possible." Inspired the
  lab's Exercises 2 and 5.
- **OpenCode** (open, *you decide*) — own every layer; you inherit all five responsibilities.
- **LangChain Deep Agents** (open, *workflow-shaped*) — `create_deep_agent` from Module 5.
- **Hermes** (open, *curated/self-improving*) — NousResearch; tested core, vetted skill hub,
  `hermes skills install` (agentskills.io). Deepest NVIDIA tie (NemoClaw-for-Hermes blueprint,
  `NVIDIA/skills` is a built-in tap). **The harness the lab drives.**
- **OpenClaw** (open, *maximal*) — the Module 6 harness; config-first, always-on, biggest
  community; powers NemoClaw.
- **Claude Code** (subscription, *highest performing*) and **Codex** (subscription, *best
  computer-use*) — maximal, frontier models. Even here the **open skills layer applies** —
  NVIDIA Verified Skills install directly and run on *your* hardware.

**The 3-question chooser:** (1) need your own model/on-prem/Nemotron? → open source. (2)
always-on vs task-shaped? → OpenClaw/Hermes vs LangChain Deep Agents; every-token-counts → pi;
own-every-layer → OpenCode. (3) maximum out-of-box, cost secondary? → Claude Code (SWE/general)
or Codex (computer-use). **The NVIDIA point:** NVIDIA wins in every branch — Nemotron (engine),
NemoClaw (safety), Verified Skills (portable capability) — by *driving the tech with the
ecosystem*, not picking a harness winner.

## The open Agent Skills spec (`agent_skills.md`)
A skill is a folder with a `SKILL.md` at its root, two parts:
- **Frontmatter** — `name` + a one-line `description`. The *only* part the harness keeps in
  context at all times (the trigger surface).
- **Body** — the full instructions. Loaded into context *only* when the description matches
  the task.
The format is the open **Agent Skills specification** ([agentskills.io](https://agentskills.io)).
Because the major harnesses all consume it, the *same* `SKILL.md` runs in OpenClaw, Hermes,
Claude Code, Codex, Cursor… Write once, supercharge any agent. (Meta-note: the `/module-N`
skills tutoring this workshop are exactly this format.)

## NVIDIA Verified Skills (`agent_skills.md`)
The layer where NVIDIA contributes to *every* harness at once:
**[github.com/NVIDIA/skills](https://github.com/NVIDIA/skills)** — official, verified skills
that teach agents to use NVIDIA software optimally (cuOpt, cuDF, CUDA-Q, NeMo, Dynamo,
Holoscan, Earth2Studio, PhysicsNeMo…), synced daily from the product teams. Install with
`npx skills add nvidia/skills --skill <name> --agent <harness>` (the `--agent` flag *is* the
portability story); Hermes has `NVIDIA/skills` as a built-in tap.
- **Verified, not just published:** a skill is *instructions you inject into your agent*, so
  an unvetted skill is a prompt-injection vector (the Module 6 lesson). Every skill passes an
  eight-step pipeline: review → security scan (**SkillSpector**: prompt injection, tool
  poisoning, dangerous code) → evaluation → **skill card** → cryptographic **signing**
  (`skill.oms.sig`, OpenSSF Model Signing) → catalog → sync. *Trust should come from
  verifiable integrity, not implied provenance.* In the lab the learner verifies a signature
  before trusting the skill.

## GPU skills in any harness (`gpu_skills.md`)
The common misconception: "if I pay for a cloud harness, my GPU sits idle." **No** — the model
loop may run in someone else's datacenter, but **tools and skills execute locally, on your
machine.** Division of labor: the cloud model writes a few hundred tokens of code; **your GPU**
does the heavy compute. A subscription buys the brain; the muscles are yours.
- The `accelerated-computing-cudf` skill teaches the model to reach for the GPU *correctly*:
  use `cudf.pandas` for minimal-change acceleration; the **100K-row size gate** (below it,
  transfer overhead beats the speedup); keep intermediate data on GPU; scale past GPU memory
  with dask-cuDF. Without the skill, the model just writes single-threaded pandas.
- True in **every** harness (open or closed) — that's why NVIDIA publishes skills for all of
  them rather than betting on one.

## How the lab maps to production (`evaluating_harnesses.md`)
| Lab exercise | Production counterpart |
|---|---|
| 1. Minimal harness | pi's core; the agentic loop inside every harness |
| 2. Context tax + lazy loading | pi's lazy skills; deferred tool loading in maximal harnesses |
| 3. Portable skill | the open Agent Skills spec powering every skill hub |
| 4. Verified skill + GPU | NVIDIA Verified Skills (SkillSpector, skill cards, OpenSSF signing) |
| 5. Self-evolving skill | pi self-extension; Hermes self-authored skills; OpenClaw memory evolution (+ NemoClaw write-policies) |

## Source map
- Concepts → `intro_agent_harnesses.md` (harness/tax), `harness_landscape.md` (the seven), `agent_skills.md` (spec + verified), `gpu_skills.md` (local GPU)
- The lab → `harness_lab.md` + `code/7-agent-harnesses/harness_lab.py`
- Wrap-up / explore-next → `evaluating_harnesses.md`
