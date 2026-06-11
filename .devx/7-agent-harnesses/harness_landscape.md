# The Harness Landscape

<img src="_static/robots/hiking.png" alt="Explorer Robot" style="float:right;max-width:300px;margin:25px;" />

Seven harnesses dominate the conversation today — five open source (bring any model) and two closed source (subscription). They don't differ much in *what* they do. They differ enormously in *how much context they spend doing it*.

Let's start with that picture, then meet each one.

<!-- fold:break -->

## The Context Tax Meter

Approximate **permanent per-turn overhead** (system prompt + always-loaded tool schemas) for each design philosophy:

<style>
.tax-meter { margin: 1em 0; }
.tax-row { display: flex; align-items: center; margin: 6px 0; }
.tax-label { width: 180px; font-weight: bold; font-size: 0.9em; flex-shrink: 0; }
.tax-track { flex-grow: 1; background: rgba(128,128,128,0.15); border-radius: 6px; height: 22px; overflow: hidden; }
.tax-fill { height: 100%; border-radius: 6px; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; color: white; font-size: 0.75em; font-weight: bold; min-width: 60px; animation: taxgrow 1.2s ease-out; }
.tax-tokens { width: 90px; text-align: right; font-size: 0.8em; padding-left: 8px; flex-shrink: 0; }
@keyframes taxgrow { from { width: 0; } }
</style>

<div class="tax-meter">
  <div class="tax-row"><div class="tax-label">pi</div><div class="tax-track"><div class="tax-fill" style="width:10%;background:#76b900;">~1k</div></div><div class="tax-tokens">minimal</div></div>
  <div class="tax-row"><div class="tax-label">OpenCode (typical)</div><div class="tax-track"><div class="tax-fill" style="width:35%;background:#5b8f00;">~3.5k</div></div><div class="tax-tokens">you decide</div></div>
  <div class="tax-row"><div class="tax-label">LC Deep Agents</div><div class="tax-track"><div class="tax-fill" style="width:45%;background:#8a8d00;">~4.5k</div></div><div class="tax-tokens">moderate</div></div>
  <div class="tax-row"><div class="tax-label">Hermes</div><div class="tax-track"><div class="tax-fill" style="width:60%;background:#b88a00;">~6k</div></div><div class="tax-tokens">curated</div></div>
  <div class="tax-row"><div class="tax-label">OpenClaw</div><div class="tax-track"><div class="tax-fill" style="width:75%;background:#c46a00;">~7.5k</div></div><div class="tax-tokens">maximal</div></div>
  <div class="tax-row"><div class="tax-label">Claude Code / Codex</div><div class="tax-track"><div class="tax-fill" style="width:95%;background:#b5483b;">7–10k</div></div><div class="tax-tokens">maximal</div></div>
</div>

> Figures are order-of-magnitude estimates that shift with every release and configuration — that's exactly why you'll **measure your own** in the lab. The shape of the chart is the lesson: a 10× spread in what different designers consider "necessary."

Remember: this is a *bet*, not a scoreboard. Maximal harnesses spend those tokens on built-in capability. Minimal harnesses bet the model can load capability on demand.

<!-- fold:break -->

## Meet the Harnesses

Click through the tabs — each profile covers the philosophy, what it optimizes for, and when to reach for it.

<!-- tabs:start -->

#### **🦞 OpenClaw**

### OpenClaw — <span style="color:#76b900;">●</span> Open Source · the OG

> **Philosophy:** Open community, config-first, always-on. The original — and the harness you already know from Module 6.

The largest open harness community. Agents are defined by markdown (`SOUL.md`, `AGENTS.md`), run continuously on heartbeats, and self-evolve their own memory. Powers the **NVIDIA NemoClaw** reference stack <span style="background:#76b900;color:white;border-radius:4px;padding:1px 6px;font-size:0.8em;">NemoClaw ✓</span>

**Choose it when:** you want an always-on autonomous agent, the biggest community and plugin ecosystem, and any model (it runs Nemotron via NVIDIA endpoints, as you configured in Module 6).

**Watch for:** maximal context tax; safety is your job (that's what Module 6 was about).

#### **📜 Hermes**

### Hermes — <span style="color:#76b900;">●</span> Open Source · refined & tested

> **Philosophy:** A curated, packaged perspective. Opinionated defaults that have been tested — including partnerships for verified skills.

Hermes takes the open-harness idea and ships it with refined defaults: a tested core, a vetted skill hub, and integration partnerships (NVIDIA skills syndicate to **Hermes Hub**). Also runs the NemoClaw stack. <span style="background:#76b900;color:white;border-radius:4px;padding:1px 6px;font-size:0.8em;">NemoClaw ✓</span>

**Choose it when:** you want open source with guardrails — strong defaults, curated skills, less assembly required.

**Watch for:** opinionated means opinionated; going off the paved road takes more effort than OpenCode.

#### **🔧 OpenCode**

### OpenCode — <span style="color:#76b900;">●</span> Open Source · complete custom builder

> **Philosophy:** Own every layer. The harness is your codebase.

OpenCode is for teams that want to build the harness itself: bring your own loop, your own memory backend, your own permission model. Maximum control, maximum responsibility.

**Choose it when:** you're embedding an agent inside a product and need to control every behavior, or your compliance story requires owning the whole stack.

**Watch for:** you inherit all five harness responsibilities yourself — including the ones that are hard to get right (sandboxing, token efficiency).

#### **🕸️ LangChain Deep Agents**

### LangChain Deep Agents — <span style="color:#76b900;">●</span> Open Source · workflow-shaped

> **Philosophy:** A harness shaped around a specific task graph, not a general-purpose assistant.

You used this in Module 5: `create_deep_agent()` with planning, sub-agent delegation, memory, and skills. Deep Agents excels when the work has a known shape — research pipelines, report generation, structured multi-step workflows.

**Choose it when:** the task is a workflow you can describe, you're already in the LangChain/LangGraph ecosystem, and you want planning + delegation without building them.

**Watch for:** less suited to open-ended, always-on operation than OpenClaw.

#### **🥧 pi**

### pi — <span style="color:#76b900;">●</span> Open Source · *"as many as needed, as little as possible"*

> **Philosophy:** Less harness, more model. No context tax.

Built by Mario Zechner and Armin Ronacher, pi is the minimal pole of the landscape: a system prompt under **1,000 tokens**, exactly **four core tools** (Read, Write, Edit, Bash), and **lazy skills** — each installed capability costs one line of context per turn, with the full payload loading only when invoked.

Its signature move is **self-extension**: ask for a capability, and the agent writes its own TypeScript extension live, no restart. It's the purest example of a self-evolving harness — and the inspiration for two of your lab exercises.

**Choose it when:** long sessions where context is precious, local/privacy-sensitive deployments, or you simply believe capability belongs in the model.

**Watch for:** fewer batteries included — no built-in sub-agents or plan mode; the bet is you'll add them only if you need them.

#### **🤖 Claude Code**

### Claude Code — <span style="color:#b5483b;">●</span> Closed Source · highest performing

> **Philosophy:** Maximal harness, frontier model, deeply integrated. The reference point the open ecosystem measures against.

Anthropic's subscription harness: rich tool suite, sub-agents, plan modes, hooks, MCP, and a skills system. The most capable out-of-box experience — and the most expensive.

**Choose it when:** out-of-box capability matters more than cost or model choice.

**Worth knowing:** even here, the open skills layer applies — NVIDIA Verified Skills install directly into Claude Code, and they execute on **your** hardware. More on that two pages from now.

#### **🛰️ Codex**

### Codex — <span style="color:#b5483b;">●</span> Closed Source · best computer use

> **Philosophy:** Maximal harness optimized for driving full computer environments.

OpenAI's subscription harness, strongest at **computer-use (CUA)** tasks — driving desktops, browsers, and long-horizon execution environments. Also expensive, also closed.

**Choose it when:** the agent's job is to operate software the way a human would — full desktop and browser automation.

**Worth knowing:** like Claude Code, Codex consumes the open skills format. The same NVIDIA skill you install for Claude Code installs for Codex with one flag change.

<!-- tabs:end -->

<!-- fold:break -->

## Which Harness Fits? — A 3-Question Chooser

Work through the questions. Your path ends at a recommendation card.

<details>
<summary><b>❓ Question 1 — Do you need to choose your own model (open weights, on-prem, Nemotron)?</b></summary>

<details>
<summary><b>✅ Yes, model flexibility is required → Question 2: Is the agent always-on, or task-shaped?</b></summary>

<details>
<summary><b>🔄 Always-on assistant (heartbeats, evolving memory)</b></summary>

> ### 🦞 → **OpenClaw** &nbsp;<span style="background:#76b900;color:white;border-radius:4px;padding:1px 6px;font-size:0.8em;">recommended</span>
> The community standard for always-on agents — and you already hardened one with NemoClaw in Module 6. Prefer stronger defaults and a curated skill hub? Pick **Hermes** instead.

</details>

<details>
<summary><b>📋 Task-shaped workflow (research, reports, pipelines)</b></summary>

> ### 🕸️ → **LangChain Deep Agents**
> Planning, delegation, and memory pre-built around a describable workflow — exactly what you used in Module 5.

</details>

<details>
<summary><b>⚡ Long live sessions where every token counts</b></summary>

> ### 🥧 → **pi**
> Sub-1k system prompt, four tools, lazy skills. As many as needed, as little as possible.

</details>

</details>

<details>
<summary><b>🏗️ No model required, but I need to own every layer (product embedding, compliance)</b></summary>

> ### 🔧 → **OpenCode**
> Build the harness you need and nothing else. All five responsibilities are yours — budget for them.

</details>

<details>
<summary><b>💳 No — maximum out-of-box capability, cost is secondary → Question 3: What's the job?</b></summary>

<details>
<summary><b>💻 Software engineering and general agentic work</b></summary>

> ### 🤖 → **Claude Code**
> Highest performing harness available today. And your GPU still gets to work — install NVIDIA skills into it (next two pages).

</details>

<details>
<summary><b>🖱️ Driving desktops and browsers like a human</b></summary>

> ### 🛰️ → **Codex**
> The strongest computer-use agent. Same story: open skills install right in.

</details>

</details>

</details>

<!-- fold:break -->

## The NVIDIA Perspective: Driving the Technology Together

Notice something about that chooser: **NVIDIA wins in every branch** — and so do you. That's not an accident; it's the strategy.

- **NemoClaw** powers the open harnesses (OpenClaw, Hermes)
- **Nemotron** runs inside any open harness you pick
- **NVIDIA Verified Skills** work across *all of them* — including Claude Code and Codex

NVIDIA isn't picking a harness winner. The harness layer is where the industry is innovating fastest, and NVIDIA's approach is to **drive the technology forward together with the ecosystem** — contributing open models, open safety stacks, and open, portable, verifiable skills that make every harness better.

> That portable skills layer is the key that unlocks everything else. Head to [Agent Skills](agent_skills) to take it apart.
