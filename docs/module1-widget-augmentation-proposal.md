# Module 1 — Widget Augmentation Proposal (DRAFT for review)

> Status: **proposal only — no live module files have been changed.**
> Scope chosen: **🟢 free wins + ⭐ high-value** (the ◇ optional/stretch items — bets, chooser,
> skillcard, wrap-up quiz, `dx-gauge` — are intentionally excluded).
> All markup below follows `.devx/7-agent-harnesses/theme/COMPONENT-CONTRACT.md` and matches the
> classes/attributes the shared `devx-theme.js` actually hydrates (verified against the JS).

This doc has two parts:

- **Part A — Net-new authored content** you asked me to draft: 2 quizzes + 2 self-typing terminal
  traces. These contain copy I wrote and grounded in the real notebooks/agent code, so they need
  your review.
- **Part B — Flagship adaptation markup** (reuses existing page text, no new copy): the two
  centerpiece ⭐ structural changes, shown so you can picture the result. The remaining ⭐/🟢
  adaptations follow the same patterns and are listed at the end.

---

## Part A — Net-new content (for review)

### A1 · Quiz — `why_agents.md` (end of page, before the "continue" link)

**Teaches:** the core *when-to-use-an-agent* judgment from this page ("What Problems Do Agents
Solve" + "When Agents Aren't the Answer"). The correct answer is the one task with a *variable
path + multiple sources + multi-step reasoning*; every distractor is a fixed path that a single
call or a chain handles better — each teaching a distinct "don't reach for an agent" failure mode.

```html
<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">Which of these tasks is the best fit for an agent, rather than a single LLM call or a fixed workflow?</p>
  <button class="dx-quiz-opt" data-fb="This is one fixed classification with a fixed set of outputs - a single LLM call does it. An agent's reasoning loop only adds latency and cost when the path never changes.">Sort each incoming support ticket into billing, technical, or other</button>
  <button class="dx-quiz-opt" data-right data-fb="Right. The path changes per bug, it pulls from several sources, and each step depends on the last - exactly where letting the model choose its next move pays off.">Investigate a reported bug by searching the docs, checking recent incident reports, and writing up a likely root cause</button>
  <button class="dx-quiz-opt" data-fb="Input-to-summary is a single fixed path with no decisions to make. That is a workflow (a chain), not an agent.">Condense a customer email into three bullet points</button>
  <button class="dx-quiz-opt" data-fb="A single deterministic transformation - no tools, no branching, no iteration. Reaching for an agent here is over-engineering.">Translate a fixed block of text from English to Spanish</button>
</div>
```

### A2 · Quiz — `introduction_to_agents.md` ("Do It Yourself" section, before the notebook button)

**Teaches:** the misconception the notebook itself flags — *"even though the feature is called tool
calling, the model doesn't actually call the tool!"* This tests whether the learner understands the
request → execute → observe cycle (i.e. routing), which is the heart of the page.

```html
<div class="dx-island dx-quiz dx-reveal">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">Your agent decides to use the add tool. What actually happens next?</p>
  <button class="dx-quiz-opt" data-fb="A common misconception. Despite the name 'tool calling', the model never runs code - it only emits the tool name and arguments as a request. Your code does the running.">The model runs the function internally and returns the sum on its own</button>
  <button class="dx-quiz-opt" data-right data-fb="Exactly. The model emits a structured request; your routing layer runs the function and appends the result to memory, then calls the model again. That request-execute-observe cycle is the ReAct loop.">Your code reads the model's request, runs the function, and adds the result to memory before calling the model again</button>
  <button class="dx-quiz-opt" data-fb="Listing a tool in the schema only tells the model the tool is available - it is the menu, not the kitchen. Your code still has to execute the tool when the model asks for it.">The tool runs automatically because it was included in the tools schema</button>
</div>
```

> **Alternative if you prefer a recall check over a misconception check:** a "which of these is NOT
> one of the four core components?" question (distractor: e.g. "Training" or "Fine-tuning"). I
> recommend the version above — it targets a real, documented misunderstanding rather than
> vocabulary.

### A3 · Self-typing terminal — `introduction_to_agents.md` ("The Agentic Loop" / "The ReAct Pattern")

**Replaces/augments** the abstract Thought→Action→Observation bullet list with a concrete, animated
trace. **Grounded in `intro_to_agents.ipynb`**: the `add` tool, the literal prompt "What is 3 plus
12?", and the result `15`. Keeps the `react_agent` architecture diagram alongside as the static
"map"; this terminal is the "live example." The `[action]`/`[observation]` labels map the ReAct
vocabulary onto what the notebook actually does.

```html
<div class="dx-term dx-reveal">
  <span class="dx-term-title">react-from-scratch</span>
  <span class="dx-term-line" data-kind="prompt">What is 3 plus 12?</span>
  <span class="dx-term-line" data-kind="think" data-delay="300">I could answer from memory, but I was given an add tool - safer to use it than to guess.</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[action] add(a=3, b=12)</span>
  <span class="dx-term-line" data-kind="tool" data-delay="200">[observation] 15</span>
  <span class="dx-term-line" data-kind="think" data-delay="300">The tool returned 15. Now I can answer.</span>
  <span class="dx-term-line" data-kind="answer" data-delay="350">3 plus 12 equals 15.</span>
</div>
```

### A4 · Self-typing terminal — `report_generation_agent.md` ("The Components in Action" or "Peeking Under the Hood")

**Shows a realistic `ReportWriter` run before the learner runs their own**, setting expectations and
building debugging intuition. **Grounded in `docgen_agent.py`** (ReAct system prompt: iterate
broad→refined queries, gather ≥3 sources, cite inline) and the client's renewable-energy example
query. Demonstrates *iteration* — the contrast with A3's single cycle is the teaching point.

```html
<div class="dx-term dx-reveal">
  <span class="dx-term-title">ReportWriter</span>
  <span class="dx-term-line" data-kind="prompt">Write a report on renewable energy adoption worldwide in 2025 for a policy audience.</span>
  <span class="dx-term-line" data-kind="think" data-delay="350">This needs current numbers and dates - I must search before writing. Start broad.</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[action] tavily_search(queries=[global renewable energy adoption 2025], topic=news)</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[observation] 2 sources: IEA Renewables 2025, IRENA capacity report</span>
  <span class="dx-term-line" data-kind="think" data-delay="300">Good baseline. Now refine for hard statistics and growth rates.</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[action] tavily_search(queries=[renewable capacity statistics 2025, solar wind growth rate 2025])</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[observation] 3 sources gathered - that is >= 3 authoritative, enough to write</span>
  <span class="dx-term-line" data-kind="tokens">context: 6,240 / 128,000 tokens</span>
  <span class="dx-term-line" data-kind="answer" data-delay="400"># Renewable Energy Adoption 2025 - Executive summary: global capacity grew ~15% year-over-year [1]; solar led new additions [2]... (full report with a Sources section)</span>
</div>
```

> **Note on accuracy:** the source names (IEA/IRENA), the ~15% figure, and the `6,240` token count
> are *illustrative* — reconstructed from the agent's code/system prompt, not captured from a live
> run. They read as a plausible trace; if you want exact numbers we'd capture a real invocation. The
> queries, tool name/signature, ≥3-source rule, and citation format are all faithful to the code.

---

## Part B — Flagship adaptation markup (reuses existing page text)

These two are the structural centerpieces of the ⭐ scope. No new prose — they re-house copy that
already exists on the page.

### B1 · Anatomy bento — `introduction_to_agents.md` ("Anatomy of an Agent", replaces the `<ul>`)

This is the module's spine (the "four components" recur on four pages). A 2×2 grid makes it the
memorable anchor it deserves to be, and the *same* layout can be reused on `report_generation_agent.md`
(B-reuse) to create the "abstract → concrete" callback.

```html
<div class="dx-bento dx-reveal">
  <div class="dx-cell is-wide"><h4>MODEL</h4>The LLM "brain" that decides which tool to use and how to respond. We use NVIDIA Nemotron 3 Super (120B).</div>
  <div class="dx-cell"><h4>TOOLS</h4>Functions that let the agent act - search, calculate, query APIs.</div>
  <div class="dx-cell"><h4>MEMORY / STATE</h4>What the agent knows during and between turns - here, the conversation log.</div>
  <div class="dx-cell"><h4>ROUTING</h4>The control flow that orchestrates reasoning and acting - the loop.</div>
</div>
```

### B2 · Flexibility tax meter — `introduction_to_agents.md` (replaces the LLM/Workflow/Agent table)

"Flexibility: Low → Medium → High" is a *ladder* — far more legible as growing bars than a 3-row
table. `data-tier="max"` gives the Agent row its distinct emphasis.

```html
<div class="dx-island dx-reveal">
  <p class="dx-island-title">WHO DECIDES WHAT TO DO - AND HOW FLEXIBLE IS IT?</p>
  <div class="dx-tax">
    <div class="dx-tax-row" style="--dx-w:20"><span class="dx-tax-name">Single LLM call</span><div class="dx-tax-track"><div class="dx-tax-fill">low</div></div><span class="dx-tax-note">no decision - one response</span></div>
    <div class="dx-tax-row" style="--dx-w:55"><span class="dx-tax-name">Workflow / chain</span><div class="dx-tax-track"><div class="dx-tax-fill">medium</div></div><span class="dx-tax-note">developer hardcodes the path</span></div>
    <div class="dx-tax-row" data-tier="max" style="--dx-w:95"><span class="dx-tax-name">Agent</span><div class="dx-tax-track"><div class="dx-tax-fill">high</div></div><span class="dx-tax-note">the LLM chooses the path</span></div>
  </div>
</div>
```

### Remaining ⭐/🟢 adaptations (same patterns — markup at implementation time)

| Page | Section | Widget | Type |
|---|---|---|---|
| `README.md` | take-home + duration + objectives | `dx-bento` (+`dx-big` for "1-2 h") | Adapt |
| `secrets.md` | each provider block | `dx-island` + `dx-chip` (REQUIRED / OPTIONAL) | Adapt + new chips |
| `why_agents.md` | "Evolution" 3 stages | `dx-island` trio + `dx-reveal` stagger | Adapt |
| `why_agents.md` | "When Agents Aren't the Answer" | `dx-island` callout | Adapt |
| `introduction_to_agents.md` | "The Tradeoff" | `dx-island` callout | Adapt |
| `introduction_to_agents.md` | "Things That Can Go Wrong" | `dx-island` + `dx-chip` per failure mode | Adapt |
| `introduction_to_agents.md` | `react_agent.png` | convert to live **mermaid** fence | Adapt *(adjacent)* |
| `report_generation_agent.md` | "Components in Action" | `dx-bento` (mirror B1) | Adapt |
| `report_generation_agent.md` | 4 code-jump buttons | `dx-island` wrapper (keep `onclick`) | Wrap |
| `report_generation_agent.md` | "What to Watch For" | `dx-island` checklist + `dx-chip` | Adapt |
| `next_steps.md` | "What's Next?" Module 2/3/4 | `dx-bento` + `dx-chip` + `dx-reveal` | Adapt |
| `next_steps.md` | "Key Takeaways" | `dx-bento` / island grid | Adapt |
| `next_steps.md` | "What You've Learned" | `dx-island` recap | Adapt |

---

## Implementation notes (apply to every insertion)

1. **One root element per widget.** The progressive-unfold plugin splits pages by top-level element
   count — each widget is a single top-level `<div>`. Place new widgets *between* the existing
   `<!-- fold:break -->` comments so they reveal as their own step.
2. **No `<script>` / `<style>` / `{{ }}`.** Only the `--dx-w` and `--i` inline custom properties are
   allowed in `style=""`.
3. **Attribute values (`data-fb`, `data-*`) are ASCII-only and contain no double quotes.** The drafts
   above already comply (hyphens not em-dashes; apostrophes are fine; no `"` inside attributes).
4. **Keep all existing `onclick` Jupyter-link buttons exactly as-is** (class-less, `onclick` intact).
5. **ReAct PNG → mermaid:** replace `![ReAct Agent Architecture](img/react_agent.png)` with a
   ```` ```mermaid ```` fence built from `img/react_agent.mmd`, but **drop** its light-theme `config`
   header and the `classDef ... fill:#hex` lines — the dark theme in `index.html` colors it.
6. **Hero enrichment (adjacent, optional):** M1 heroes carry only `data-eyebrow`+`data-title`; adding
   `data-sub` and a `data-meta` chip strip (e.g. `DURATION::1-2 hrs|COMPONENTS::4|MODEL::Nemotron`)
   would match M7 at a glance. Not one of the 11 widgets, so excluded from scope unless you want it.

## Open questions before implementation

1. **Voice/tone of the quiz copy** — I matched the module's friendly-but-precise register. Adjust?
2. **`dx-term` token/source numbers** — keep illustrative, or capture from a real run?
3. **Implementation order** — do the flagship intro changes (B1/B2 + A2/A3) first as a "show me one
   page" proof, or sweep all pages at once?
