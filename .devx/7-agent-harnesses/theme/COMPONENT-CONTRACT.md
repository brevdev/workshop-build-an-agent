# DevX component contract (for page authors)

Markup that `_static/css/devx-theme.css` + `_static/js/devx-theme.js` (the shared theme) understand. Pages carry ONLY
attribute-driven HTML — never `<script>` or `<style>` blocks, never `{{ }}`
(docsify-mustache mangles them). Every widget is ONE root element (the
progressive-unfold plugin splits pages by top-level element count).

## Hero band (first element of every page; REPLACES the `# H1` markdown line)

```html
<div class="dx-hero" data-eyebrow="MODULE 07 / AGENT HARNESSES" data-title="Same model. Different harness." data-sub="One-sentence framing in plain text - no quotes or braces." data-meta="DURATION::2-3 hrs|EXERCISES::5|MODEL::Nemotron"></div>
```

- `data-meta`: `LABEL::value` pairs joined by `|` (optional).
- JS builds the inner DOM; leave the div EMPTY. No double quotes inside attribute values.

## Dark island (generic shell for any custom content)

```html
<div class="dx-island">
  <p class="dx-island-title">CONTEXT TAX METER</p>
  ...content (markdown works if surrounded by blank lines)...
</div>
```

## Self-typing terminal

```html
<div class="dx-term">
  <span class="dx-term-title">your-harness</span>
  <span class="dx-term-line" data-kind="prompt">task the user typed</span>
  <span class="dx-term-line" data-kind="think" data-delay="350">thinking...</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[tool] run_bash(head -5 data.csv)</span>
  <span class="dx-term-line" data-kind="tokens">tokens: 4,312 / 128,000</span>
  <span class="dx-term-line" data-kind="answer" data-delay="400">final answer text</span>
</div>
```

- kinds: `prompt` (typed, `$` prefix), `think` (gray italic), `tool` (green), `tokens` (dim), `answer` (typed, white).
- `data-delay` = ms pause before that line. JS adds the replay button; types on scroll-into-view; reduced-motion users see full text instantly.

## Token gauges (conic donuts; pct must be an INTEGER percent)

```html
<div class="dx-island">
  <p class="dx-island-title">WHO EATS A 32K-TOKEN TURN?</p>
  <div class="dx-gauges">
    <div class="dx-gauge" data-pct="12"><div class="dx-gauge-ring">0%</div><p class="dx-gauge-label"><b>maximal harness</b><br>3,922 tokens</p></div>
    <div class="dx-gauge" data-pct="46"><div class="dx-gauge-ring">0%</div><p class="dx-gauge-label"><b>10 eager skills</b><br>~15,000 tokens</p></div>
    <div class="dx-gauge" data-pct="1"><div class="dx-gauge-ring">0%</div><p class="dx-gauge-label"><b>10 lazy skills</b><br>~240 tokens</p></div>
  </div>
</div>
```

## Context tax meter

```html
<div class="dx-island">
  <p class="dx-island-title">CONTEXT TAX METER - PERMANENT PER-TURN OVERHEAD</p>
  <div class="dx-tax">
    <div class="dx-tax-row" style="--dx-w:10"><span class="dx-tax-name">pi</span><div class="dx-tax-track"><div class="dx-tax-fill">~1k</div></div><span class="dx-tax-note">minimal</span></div>
    <div class="dx-tax-row" data-tier="max" style="--dx-w:95"><span class="dx-tax-name">Claude Code / Codex</span><div class="dx-tax-track"><div class="dx-tax-fill">7-10k</div></div><span class="dx-tax-note">maximal</span></div>
  </div>
</div>
```

- `--dx-w` = bar width percent. `data-tier="max"` renders the gray bar. Bars animate on reveal.

## Quiz (one per concept page; distractor feedback must TEACH a real failure mode)

```html
<div class="dx-island dx-quiz">
  <p class="dx-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="dx-quiz-q">The question?</p>
  <button class="dx-quiz-opt" data-fb="Why this is wrong and what it teaches.">Distractor A</button>
  <button class="dx-quiz-opt" data-right data-fb="Why this is right.">Correct answer</button>
  <button class="dx-quiz-opt" data-fb="Why this is wrong.">Distractor C</button>
</div>
```

## Predict-before-reveal

```html
<div class="dx-island dx-bet" data-answer="3,922 tokens" data-explain="measured with tiktoken in Exercise 2; the minimal harness pays just 365.">
  <p class="dx-island-title">PLACE YOUR BET</p>
  <p class="dx-quiz-q">Before you scroll: how many tokens does the bundled maximal config inject per turn?</p>
  <div class="dx-bet-opts">
    <button class="dx-bet-opt">~500</button>
    <button class="dx-bet-opt">~1,500</button>
    <button class="dx-bet-opt">~4,000</button>
    <button class="dx-bet-opt">~9,000</button>
  </div>
</div>
```

## Bento grid (landing page)

```html
<div class="dx-bento">
  <div class="dx-cell is-wide is-tall"><h4>YOU WILL BUILD</h4>...</div>
  <div class="dx-cell"><h4>DURATION</h4><span class="dx-big">2-3 h</span>self-paced</div>
  ...
</div>
```

## Chips (replace ad-hoc colored spans)

```html
<span class="dx-chip">OPEN SOURCE</span>
<span class="dx-chip is-green">NemoClaw ✓</span>
<span class="dx-chip is-outline-green">VERIFIED</span>
```

## Verified skill card

```html
<div class="dx-skillcard">
  <div class="dx-skillcard-head"><span class="dx-skillcard-name">accelerated-computing-cudf</span><span class="dx-chip is-green">NVIDIA VERIFIED ✓</span></div>
  <p>description...</p>
  <ul>
    <li><b>Owner</b> NVIDIA · <b>License</b> CC-BY-4.0 AND Apache-2.0</li>
    <li><b>SkillSpector</b> <span class="dx-check">✓</span> prompt injection <span class="dx-check">✓</span> tool poisoning <span class="dx-check">✓</span> dangerous code</li>
    <li><b>Signature</b> skill.oms.sig - OpenSSF Model Signing</li>
  </ul>
</div>
```

## Chooser

Wrap the existing nested `<details>` decision flow in `<div class="dx-choose"> ... </div>`
(keep blank lines so inner markdown renders). Recommendation blockquotes inside get the
green card styling automatically.

## Reveal widgets (replace bare `<details>` accordions)

Pick by the content's *reading model*: inline when the reader follows along, an overlay when it's a tangent, a grid for scannable term lists. All native + attribute-driven (no `<script>`). Leave `.dx-choose` decision-trees (above) as-is.

**`dx-peek` — inline reveal tile.** Native `<details>`; expands in place, so the reading thread stays put. Use for sequential lab steps, hint/solution reveals, and conditional setup notes.

```html
<details class="dx-peek">
<summary>Step 1 — Observe the deny</summary>

Body markdown (blank line above). Prose and code render at 15px.

</details>
```

- Modifiers: `is-solution` (amber accent — for 🆘 hint/answer reveals), `is-setup` (compact + muted — for tiny "⚠️ Don't have a key?" fallbacks).
- Nesting is fine — a step may contain a nested `dx-peek`; each `<details>` is styled by its own summary.
- Headings inside keep their normal size; only body + code drop to 15px.

**`dx-aside` — popover overlay.** Opens in the browser top layer over the page (no reflow), so the reader never loses their place. Use for "how does X work?", optional examples, and long file dumps.

```html
<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-PAGE-1">How is this calculated?</button>
<div id="aside-PAGE-1" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-PAGE-1" popovertargetaction="hide" aria-label="Close">×</button>

Body markdown (blank line above).

</div>
</div>
```

- The `id` must be UNIQUE across the whole workshop — convention `aside-<page>-<n>`. The trigger, the panel, and the × button all reference the same id.
- Native Popover API (no JS): Esc / click-outside / × all dismiss; re-clicking the trigger toggles. The panel scrolls internally, so long code is fine.
- NOT for sequential steps — showing one at a time hides the thread.

**`dx-defs` — glossary grid.** A 4-column bento grid (matches `.dx-bento`) of term → definition tiles that expand in place. Use for scannable term lists.

```html
<div class="dx-defs">
<details class="dx-def">
<summary>seccomp BPF</summary>

A syscall filter that blocks dangerous operations like mount() and ptrace().

</details>
<details class="dx-def is-wide">
<summary>Audit trail</summary>

Definition text. Give any code-bearing tile is-wide so the code fits.

</details>
</div>
```

- `is-wide` (span 2) / `is-full` (span the whole row) pack tiles so each row fills with no dead space; give any code-bearing tile `is-wide`. Re-balance the spans if you add or remove tiles.
- Keep a whole grid inside ONE fold section — never split it across a `<!-- fold:break -->`.

## Reveal-on-scroll

Add `class="dx-reveal"` (optionally `style="--i:1"`, `--i:2`... for stagger) to islands,
bento cells, and skill cards. Never to text paragraphs.

## Hard rules

1. Keep ALL `<button onclick="...">` jupyter-link buttons exactly as they are (class-less, onclick intact).
2. Keep ALL `<!-- fold:break -->` comments in place.
3. Keep docsify-tabs syntax (`<!-- tabs:start -->` ... `#### **Tab**`) — tabs are restyled by CSS automatically.
4. NO live ```mermaid fences — the progressive-unfold plugin hides later fold sections before mermaid measures them, producing zero-size renders that never retry (mermaid marks nodes `data-processed` before rendering). Diagrams ship as pre-rendered dark SVGs: `![Title](img/<name>_dark.svg)` with the mermaid source kept beside it as `img/<name>.mmd` (same convention as modules 1-6; dx palette #161616 fill / #3a3a3a stroke / #f2f2f2 text / #76b900 cluster accents).
5. No `<style>` blocks, no `style=""` except `--dx-w`/`--i` custom properties and the existing mascot float pattern (`style="float:right;max-width:240px;margin:20px;"`).
6. Mascot images: keep ONE per page, max-width 240px, never in the hero — place beside a later prose section.
7. Keep every link, code fence, and the instructional text intact unless the text directly describes a replaced visual.
8. ASCII only in attribute values (data-title etc.) — emoji fine in visible text.
9. Reveal widgets replace bare `<details>`: `dx-peek` (inline), `dx-aside` (popover), `dx-defs` (glossary grid). A class-less `<details>` should appear ONLY inside a `.dx-choose` block.
