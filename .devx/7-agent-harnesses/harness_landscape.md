<div class="dx-hero" data-eyebrow="MODULE 07 / 02 - THE LANDSCAPE" data-title="Seven harnesses. One axis." data-sub="The fastest way to sort the ecosystem is by context tax - how much permanent per-turn overhead each harness spends before your task even starts." data-meta="HARNESSES::7|AXIS::context tax"></div>

Seven harnesses dominate the conversation today — five open source (bring any model) and two closed source (subscription). They don't differ much in *what* they do. They differ enormously in *how much context they spend doing it*.

Let's start with that picture, then meet each one.

<!-- fold:break -->

## The Context Tax Meter

Approximate **permanent per-turn overhead** (system prompt + always-loaded tool schemas) for each design philosophy:

<div class="dx-island dx-bet" data-answer="3,922 tokens" data-explain="measured with tiktoken in Exercise 2; the minimal harness pays just 400.">
  <p class="dx-island-title">PLACE YOUR BET</p>
  <p class="dx-quiz-q">Before you scroll: how many tokens does the bundled maximal config inject per turn?</p>
  <div class="dx-bet-opts">
    <button class="dx-bet-opt">~500</button>
    <button class="dx-bet-opt">~1,500</button>
    <button class="dx-bet-opt">~4,000</button>
    <button class="dx-bet-opt">~9,000</button>
  </div>
</div>

<div class="dx-island">
  <p class="dx-island-title">CONTEXT TAX METER - PERMANENT PER-TURN OVERHEAD</p>
  <div class="dx-tax">
    <div class="dx-tax-row" style="--dx-w:10"><span class="dx-tax-name">pi</span><div class="dx-tax-track"><div class="dx-tax-fill">~1k</div></div><span class="dx-tax-note">minimal</span></div>
    <div class="dx-tax-row" style="--dx-w:35"><span class="dx-tax-name">OpenCode</span><div class="dx-tax-track"><div class="dx-tax-fill">~3.5k</div></div><span class="dx-tax-note">you decide</span></div>
    <div class="dx-tax-row" style="--dx-w:45"><span class="dx-tax-name">LC Deep Agents</span><div class="dx-tax-track"><div class="dx-tax-fill">~4.5k</div></div><span class="dx-tax-note">moderate</span></div>
    <div class="dx-tax-row" style="--dx-w:60"><span class="dx-tax-name">Hermes</span><div class="dx-tax-track"><div class="dx-tax-fill">~6k</div></div><span class="dx-tax-note">curated</span></div>
    <div class="dx-tax-row" style="--dx-w:75"><span class="dx-tax-name">OpenClaw</span><div class="dx-tax-track"><div class="dx-tax-fill">~7.5k</div></div><span class="dx-tax-note">maximal</span></div>
    <div class="dx-tax-row" data-tier="max" style="--dx-w:95"><span class="dx-tax-name">Claude Code / Codex</span><div class="dx-tax-track"><div class="dx-tax-fill">7-10k</div></div><span class="dx-tax-note">maximal</span></div>
  </div>
</div>

> Figures are order-of-magnitude estimates that shift with every release and configuration — that's exactly why you'll **measure your own** in the lab. The shape of the chart is the lesson: a 10× spread in what different designers consider "necessary."

Remember: this is a *bet*, not a scoreboard. Maximal harnesses spend those tokens on built-in capability. Minimal harnesses bet the model can load capability on demand.

<!-- fold:break -->

## Meet the Harnesses

<img src="_static/robots/hiking.png" alt="Explorer Robot" style="float:right;max-width:240px;margin:20px;" />

Click through the tabs — each profile covers the philosophy, what it optimizes for, and when to reach for it.

<!-- tabs:start -->

#### **🦞 OpenClaw**

### OpenClaw <span class="dx-chip">OPEN SOURCE</span> · the OG

> **Philosophy:** Open community, config-first, always-on. The original — and the harness you already know from Module 6.

The largest open harness community. Agents are defined by markdown (`SOUL.md`, `AGENTS.md`), run continuously on heartbeats, and self-evolve their own memory. Powers the **NVIDIA NemoClaw** reference stack <span class="dx-chip is-green">NemoClaw ✓</span>

**Choose it when:** you want an always-on autonomous agent, the biggest community and plugin ecosystem, and any model (it runs Nemotron via NVIDIA endpoints, as you configured in Module 6).

**Watch for:** maximal context tax; safety is your job (that's what Module 6 was about).

#### **📜 Hermes**

### Hermes <span class="dx-chip">OPEN SOURCE</span> · refined & self-improving

> **Philosophy:** *"The agent that grows with you."* A curated, tested open harness that writes its own memories and skills over time.

[Hermes](https://hermes-agent.nousresearch.com), from NousResearch, takes the open-harness idea and ships it with refined defaults: a tested core, a vetted skill hub, and a `hermes skills install` command that speaks the open [agentskills.io](https://agentskills.io) spec. NVIDIA's tie is the deepest of any open harness — there's a [NemoClaw-for-Hermes blueprint](https://build.nvidia.com/nvidia/nemoclaw-for-hermes-agent) on build.nvidia.com, and `NVIDIA/skills` is a built-in tap. <span class="dx-chip is-green">NemoClaw ✓</span>

**Choose it when:** you want open source with guardrails — strong defaults, curated skills, and a harness that accumulates skills as it works. **It's the harness you'll drive in this module's lab.**

**Watch for:** opinionated means opinionated; going off the paved road takes more effort than OpenCode.

#### **🔧 OpenCode**

### OpenCode <span class="dx-chip">OPEN SOURCE</span> · the open coding agent

> **Philosophy:** Claude Code-class capability, fully open — any provider, any model, every layer inspectable and configurable.

OpenCode is a complete, batteries-included coding agent you run in your terminal: the open ecosystem's answer to the closed subscription harnesses. It speaks to dozens of providers (including OpenAI-compatible endpoints, so Nemotron drops right in), and its config surface — custom agents, modes, permissions — lets you decide how much harness you carry on each turn.

**Choose it when:** you want the closed-harness coding experience — rich tools, TUI, deep configurability — but open source, self-hostable, and on the model of your choice.

**Watch for:** "you decide" cuts both ways — the context tax is in your hands, and a fully loaded config approaches the maximal harnesses it competes with.

#### **🕸️ LangChain Deep Agents**

### LangChain Deep Agents <span class="dx-chip">OPEN SOURCE</span> · workflow-shaped

> **Philosophy:** A harness shaped around a specific task graph, not a general-purpose assistant.

You used this in Module 5: `create_deep_agent()` with planning, sub-agent delegation, memory, and skills. Deep Agents excels when the work has a known shape — research pipelines, report generation, structured multi-step workflows.

**Choose it when:** the task is a workflow you can describe, you're already in the LangChain/LangGraph ecosystem, and you want planning + delegation without building them.

**Watch for:** less suited to open-ended, always-on operation than OpenClaw.

#### **🥧 pi**

### pi <span class="dx-chip">OPEN SOURCE</span> · *"as many as needed, as little as possible"*

> **Philosophy:** Less harness, more model. No context tax.

Built by Mario Zechner and Armin Ronacher, pi is the minimal pole of the landscape: a system prompt under **1,000 tokens**, exactly **four core tools** (Read, Write, Edit, Bash), and **lazy skills** — each installed capability costs one line of context per turn, with the full payload loading only when invoked.

Its signature move is **self-extension**: ask for a capability, and the agent writes its own TypeScript extension live, no restart. It's the purest example of a self-evolving harness — and the inspiration for two of your lab exercises.

**Choose it when:** long sessions where context is precious, local/privacy-sensitive deployments, or you simply believe capability belongs in the model.

**Watch for:** fewer batteries included — no built-in sub-agents or plan mode; the bet is you'll add them only if you need them.

#### **🤖 Claude Code**

### Claude Code <span class="dx-chip">SUBSCRIPTION</span> · highest performing

> **Philosophy:** Maximal harness, frontier model, deeply integrated. The reference point the open ecosystem measures against.

Anthropic's subscription harness: rich tool suite, sub-agents, plan modes, hooks, MCP, and a skills system. The most capable out-of-box experience — and the most expensive.

**Choose it when:** out-of-box capability matters more than cost or model choice.

**Worth knowing:** even here, the open skills layer applies — NVIDIA Verified Skills install directly into Claude Code, and they execute on **your** hardware. More on that two pages from now.

#### **🛰️ Codex**

### Codex <span class="dx-chip">SUBSCRIPTION</span> · OpenAI's agentic coder

> **Philosophy:** Maximal harness around OpenAI's frontier models — a local CLI plus cloud sandboxes for delegated, parallel runs.

OpenAI's subscription harness for software engineering. Its signature move is **cloud task delegation**: hand long-horizon jobs to sandboxed cloud environments and fan several out at once while you keep working. Also expensive, also closed.

**Choose it when:** you're standardized on OpenAI's models, or your workflow leans on delegating batches of long-running tasks to cloud sandboxes.

**Worth knowing:** like Claude Code, Codex consumes the open skills format. The same NVIDIA skill you install for Claude Code installs for Codex with one flag change.

<!-- tabs:end -->

<!-- fold:break -->

## Which Harness Fits? — A 3-Question Chooser

Work through the questions. Your path ends at a recommendation card.

<div class="dx-choose">

<details>
<summary><b>❓ Question 1 — Do you need to choose your own model (open weights, on-prem, Nemotron)?</b></summary>

<details>
<summary><b>✅ Yes, model flexibility is required → Question 2: What shape is the work?</b></summary>

<details>
<summary><b>🔄 Always-on assistant (heartbeats, evolving memory)</b></summary>

> ### 🦞 → **OpenClaw** &nbsp;<span class="dx-chip is-green">recommended</span>
> The community standard for always-on agents — and you already hardened one with NemoClaw in Module 6. Prefer stronger defaults and a curated skill hub? Pick **Hermes** instead.

</details>

<details>
<summary><b>📋 Task-shaped workflow, or an agent embedded in your product (research, reports, pipelines)</b></summary>

> ### 🕸️ → **LangChain Deep Agents**
> Planning, delegation, and memory pre-built around a describable workflow — exactly what you used in Module 5, and the natural fit when the agent lives inside your codebase.

</details>

<details>
<summary><b>💻 Interactive coding in your terminal</b></summary>

> ### 🔧 → **OpenCode**
> The open, provider-flexible coding agent: the closed-harness experience with Nemotron — or anything else — as the engine.

</details>

<details>
<summary><b>⚡ Long live sessions where every token counts</b></summary>

> ### 🥧 → **pi**
> Sub-1k system prompt, four tools, lazy skills. As many as needed, as little as possible.

</details>

</details>

<details>
<summary><b>💳 No — maximum out-of-box capability, cost is secondary → Question 3: Whose frontier models?</b></summary>

<details>
<summary><b>🤖 Anthropic's — strongest out-of-box agentic performance</b></summary>

> ### 🤖 → **Claude Code**
> Highest performing harness available today. And your GPU still gets to work — install NVIDIA skills into it (next two pages).

</details>

<details>
<summary><b>🛰️ OpenAI's — with cloud sandboxes for delegated, parallel runs</b></summary>

> ### 🛰️ → **Codex**
> OpenAI's agentic coder, built for handing long jobs to cloud sandboxes. Same story: open skills install right in.

</details>

</details>

</details>

</div>

<!-- fold:break -->

## The NVIDIA Perspective: Driving the Technology Together

Notice something about that chooser: **NVIDIA wins in every branch** — and so do you. That's not an accident; it's the strategy.

- **NemoClaw** powers the open harnesses (OpenClaw, Hermes)
- **Nemotron** runs inside any open harness you pick
- **NVIDIA Verified Skills** work across *all of them* — including Claude Code and Codex

NVIDIA isn't picking a harness winner. The harness layer is where the industry is innovating fastest, and NVIDIA's approach is to **drive the technology forward together with the ecosystem** — contributing open models, open safety stacks, and open, portable, verifiable skills that make every harness better.

<div class="dx-island dx-quiz">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">Your team needs an always-on assistant, on-prem models are mandatory, and you want the largest community. Which harness do you pick?</p>
  <button class="dx-quiz-opt" data-fb="Closed source means no on-prem model choice.">Claude Code</button>
  <button class="dx-quiz-opt" data-fb="Minimal and model-flexible but the smallest batteries-included assistant story.">pi</button>
  <button class="dx-quiz-opt" data-right data-fb="Open source + any model + the biggest always-on community - and NemoClaw hardens it.">OpenClaw</button>
  <button class="dx-quiz-opt" data-fb="A capable open coding agent, but it is built for interactive terminal sessions, not always-on operation.">OpenCode</button>
</div>

> That portable skills layer is the key that unlocks everything else. Head to [Agent Skills](agent_skills) to take it apart.
