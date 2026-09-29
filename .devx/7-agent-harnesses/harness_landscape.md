<div class="dx-hero" data-eyebrow="MODULE 07 / 02 - THE LANDSCAPE" data-title="Seven harnesses. One axis." data-sub="Compare tools, model support, hosting, and the context included in each request." data-meta="HARNESSES::7|AXIS::context tax"></div>

Here are seven harnesses with different defaults for tools, memory, and workflows. Their licenses, model access, and hosting options are separate choices.

Let's start with that picture, then meet each one.

<!-- fold:break -->

## The Context Tax Meter

Compare the two bundled lab configurations: system prompt plus tool schemas, estimated with `tiktoken`. These are teaching examples, not benchmarks of commercial harnesses.

<div class="dx-island dx-bet" data-answer="3,922 tokens" data-explain="measured with tiktoken in Exercise 2; the minimal harness pays just 400.">
  <p class="dx-island-title">TAKE A GUESS</p>
  <p class="dx-quiz-q">Before you scroll: how many tokens does the bundled maximal config inject per turn?</p>
  <div class="dx-bet-opts">
    <button class="dx-bet-opt">~500</button>
    <button class="dx-bet-opt">~1,500</button>
    <button class="dx-bet-opt">~4,000</button>
    <button class="dx-bet-opt">~9,000</button>
  </div>
</div>

<div class="dx-island">
  <p class="dx-island-title">CONTEXT TAX METER — BUNDLED EXAMPLES</p>
  <div class="dx-tax">
    <div class="dx-tax-row" style="--dx-w:10"><span class="dx-tax-name">Minimal lab</span><div class="dx-tax-track"><div class="dx-tax-fill">400</div></div><span class="dx-tax-note">estimated tokens</span></div>
    <div class="dx-tax-row" data-tier="max" style="--dx-w:98"><span class="dx-tax-name">Maximal lab</span><div class="dx-tax-track"><div class="dx-tax-fill">3,922</div></div><span class="dx-tax-note">estimated tokens</span></div>
  </div>
</div>

> This measures serialized text with a proxy tokenizer. The model's tokenizer, request format, caching, and loaded context determine actual usage and cost.

Maximal harnesses spend tokens to bake in capability from the get-go. Minimal harnesses assume the model can load capability when needed.

<!-- fold:break -->

## Meet the Harnesses

<img src="_static/robots/hiking.png" alt="Explorer Robot" style="float:right;max-width:240px;margin:20px;" />

Click through the tabs — each profile covers the philosophy, what it optimizes for, and when to reach for it.

<!-- tabs:start -->

#### **🦞 OpenClaw**

### OpenClaw <span class="dx-chip">OPEN SOURCE</span> · the OG

> **Philosophy:** Open community, config-first, always-on. The original — and the harness you already know from Module 6.

Agents are configured with markdown (`SOUL.md`, `AGENTS.md`), run continuously on heartbeats, and self-evolve their own memory. Powers the **NVIDIA NemoClaw** reference stack <span class="dx-chip is-green">NemoClaw ✓</span>

**Choose it when:** you want an always-on autonomous agent, a plugin ecosystem, and any model (it runs Nemotron via NVIDIA endpoints, as you configured in Module 6).

**Watch for:** maximal context tax; safety is your job (that's what Module 6 was about).

#### **📜 Hermes**

### Hermes <span class="dx-chip">OPEN SOURCE</span> · refined & self-improving

> **Philosophy:** *"The agent that grows with you."* A curated, tested open harness that writes its own memories and skills over time.

[Hermes](https://hermes-agent.nousresearch.com), from NousResearch, takes the open-harness idea and ships it with refined defaults: a tested core, a vetted skill hub, and a `hermes skills install` command that speaks the open [agentskills.io](https://agentskills.io) spec. There is a [NemoClaw-for-Hermes blueprint](https://build.nvidia.com/nvidia/nemoclaw-for-hermes-agent) on build.nvidia.com, and `NVIDIA/skills` is a built-in tap. <span class="dx-chip is-green">NemoClaw ✓</span>

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

Created by Mario Zechner, pi is the minimal pole of the landscape: a system prompt under **1,000 tokens**, exactly **four core tools** (Read, Write, Edit, Bash), and **lazy skills** — each installed capability costs one line of context per turn, with the full payload loading only when invoked.

Its signature move is **self-extension**: ask for a capability, and the agent writes its own TypeScript extension live, no restart. It's the purest example of a self-evolving harness — and the inspiration for two of your lab exercises.

**Choose it when:** long sessions where context is precious, local/privacy-sensitive deployments, or you simply believe capability belongs in the model.

**Watch for:** fewer batteries included — no built-in sub-agents or plan mode; the idea is you'll add them only if you need them.

#### **🤖 Claude Code**

### Claude Code <span class="dx-chip">COMMERCIAL</span> · integrated coding workflow

> **Philosophy:** Maximal harness, frontier model, deeply integrated. The reference point the open ecosystem measures against.

Anthropic's coding agent combines a tool suite, sub-agents, plan modes, hooks, MCP, and skills. Account access and usage costs depend on how you connect it.

**Choose it when:** out-of-box capability matters more than cost or model choice.

**Worth knowing:** even here, the open skills layer applies — NVIDIA Verified Skills install directly into Claude Code, and their code runs wherever its tools are configured to run. More on that two pages from now.

#### **🛰️ Codex**

### Codex <span class="dx-chip">OPEN-SOURCE CLI</span> · OpenAI's agentic coder

> **Philosophy:** Maximal harness around OpenAI's frontier models — a local CLI plus cloud sandboxes for delegated, parallel runs.

OpenAI's coding agent offers local CLI work and cloud task delegation. The [CLI is open source](https://developers.openai.com/blog/openai-for-developers-2025); model and hosted-service access are separate. [CLI guide](https://learn.chatgpt.com/docs/codex/cli).

**Choose it when:** you're standardized on OpenAI's models, or your workflow leans on delegating batches of long-running tasks to cloud sandboxes.

**Worth knowing:** like Claude Code, Codex consumes the open skills format. The same NVIDIA skill you install for Claude Code installs for Codex with one flag change.

<!-- tabs:end -->

<!-- fold:break -->

## Which Harness Fits?

Work through the three questions below. Your path ends at a recommendation.

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

Whichever harness you land on, the NVIDIA pieces come with you:

- **NemoClaw** powers the open harnesses (OpenClaw, Hermes)
- **Nemotron** works with harnesses that support its endpoint and model capabilities
- **NVIDIA Verified Skills** can travel between compatible harnesses, with the required tools and dependencies

NVIDIA isn't picking a harness winner. The harness layer is where the industry is innovating fastest, and NVIDIA's approach is to **drive the technology forward together with the ecosystem** — contributing open models, open safety stacks, and open, portable, verifiable skills that can extend compatible harnesses.

<div class="dx-island dx-quiz">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">Which option provides the always-on assistant and OpenClaw configuration used in Module 6, with a configurable model endpoint?</p>
  <button class="dx-quiz-opt" data-fb="This option was not the always-on assistant configured in Module 6.">Claude Code</button>
  <button class="dx-quiz-opt" data-fb="Module 7 borrows pi’s minimal design; Module 6 configured OpenClaw.">pi</button>
  <button class="dx-quiz-opt" data-right data-fb="Module 6 configured OpenClaw with NemoClaw; compatible model endpoints can be selected.">OpenClaw</button>
  <button class="dx-quiz-opt" data-fb="OpenCode has its own runtime and server options; Module 6 configured OpenClaw.">OpenCode</button>
</div>

> That portable skills layer is the key that unlocks everything else. Head to [Agent Skills](agent_skills) to take it apart.
