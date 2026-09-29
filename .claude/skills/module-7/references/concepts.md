# Module 7 Concepts — tutor reference

Answer conceptual questions accurately and in the workshop's voice. For the
authoritative narrative, read the teaching pages in `.devx/7-agent-harnesses/`.
Explaining these concepts is teaching — do it freely. The token figures are
order-of-magnitude **bets the learner measures in the lab**, not a fixed scoreboard.

## Harness vs LLM — the engine and the car (`intro_agent_harnesses.md`)
The model proposes plans and tool calls from the supplied context. The harness executes
calls, retains messages, and supplies persistent memory. Do not say the model cannot plan.
- **Engine vs car:** the LLM is the engine; the harness is the chassis/transmission/fuel/
  steering. An engine on a stand goes nowhere; a car without an engine is furniture.
- **Two independent choices:** *same model + different harness* → a very different agent
  (Nemotron in a bare loop vs. inside OpenClaw are night and day); *same harness + different
  model* → the interface can stay familiar while reasoning, tool use, latency, and results change.
- Both layers affect results; compare complete configurations on the same tasks.

## Five harness design choices
Capabilities vary by harness and configuration:
1. **State and memory** — context across turns; durable memory requires persistent storage. In-memory checkpointing alone does not survive a process restart.
2. **Optional self-evolution** — proposing reusable procedures, as in this lab’s final exercise.
3. **Skills** — packaged procedures loaded on request (M2 and M5).
4. **Tool calling** — schemas, execution, sandboxing, permissions, retries (MCP, M2; Docker + HITL, M5).
5. **Token efficiency** — the context window is the scarce resource (sub-agent isolation keeping context clean, M5).

Context management is one useful comparison axis alongside permissions, hosting, tools, and model compatibility.

## Context tax and lazy loading
The lab estimates prompt+tool-schema size with `tiktoken`: roughly 400 vs 3,922 tokens for
its two bundled configurations. This is a proxy, not model billing or a vendor benchmark.
Lazy loading starts with descriptions; full bodies enter history when loaded and can stay
there until removed or compacted. Caching can change billed cost without shrinking context.

## The harness landscape
Compare workflow, model support, hosting, and permissions. Do not claim an unsourced
performance or price ranking. Codex CLI is open source; hosted services and model access
are separate. Open-source tools also need compatible models and credentials.

## The open Agent Skills spec (`agent_skills.md`)
A skill is a folder with a `SKILL.md` at its root, two parts:
- **Frontmatter** — `name` and `description`; valid YAML descriptions may span lines. The lab normalizes them for its initial index.
- **Body** — instructions requested through `load_skill`; loaded bodies may remain in history.
The format is the open **Agent Skills specification** ([agentskills.io](https://agentskills.io)).
Compatible harnesses can discover the same `SKILL.md`. Tool names, dependencies and
permissions still need to match the destination runtime. The workshop tutor uses this format.

## NVIDIA Verified Skills (`agent_skills.md`)
NVIDIA publishes skills for compatible harnesses:
**[github.com/NVIDIA/skills](https://github.com/NVIDIA/skills)** — official, verified skills
that teach agents to use NVIDIA software optimally (cuOpt, cuDF, CUDA-Q, NeMo, Dynamo,
Holoscan, Earth2Studio, PhysicsNeMo…), synced daily from product teams. The lab installer
verifies the signed payload before installation; copy the complete verified folder to
Hermes. Remote installers can omit supporting files if fetching fails.
- **Verified, not just published:** a skill is *instructions you inject into your agent*, so
  an unvetted skill is a prompt-injection vector (the Module 6 lesson). Every skill passes an
  publication pipeline: review → security scan (**SkillSpector**: prompt injection, tool
  poisoning, dangerous code) → evaluation → **skill card** → cryptographic **signing**
  (`skill.oms.sig`, OpenSSF Model Signing) → catalog → sync. *Trust should come from
  verifiable integrity, not implied provenance.* In the lab the learner verifies a signature
  before installing the skill. This authenticates signed files, not every possible execution; review dependencies and permissions.

## GPU skills (`gpu_skills.md`)
The model proposes code; the harness runs it where its tool backend lives. In this lab,
that is the workshop GPU machine. Remote sandboxes and MCP tools can run elsewhere.
Tool output returns to the model, so local compute alone is not a data-privacy guarantee.
Measure workload speed rather than treating a row-count rule as a universal threshold.

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
