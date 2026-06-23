# Module 7 component contract (for page authors)

Markup that `_static/css/m7-theme.css` + `_static/js/m7-theme.js` (the shared theme) understand. Pages carry ONLY
attribute-driven HTML — never `<script>` or `<style>` blocks, never `{{ }}`
(docsify-mustache mangles them). Every widget is ONE root element (the
progressive-unfold plugin splits pages by top-level element count).

## Hero band (first element of every page; REPLACES the `# H1` markdown line)

```html
<div class="m7-hero" data-eyebrow="MODULE 07 / AGENT HARNESSES" data-title="Same model. Different harness." data-sub="One-sentence framing in plain text - no quotes or braces." data-meta="DURATION::2-3 hrs|EXERCISES::5|MODEL::Nemotron"></div>
```

- `data-meta`: `LABEL::value` pairs joined by `|` (optional).
- JS builds the inner DOM; leave the div EMPTY. No double quotes inside attribute values.

## Dark island (generic shell for any custom content)

```html
<div class="m7-island">
  <p class="m7-island-title">CONTEXT TAX METER</p>
  ...content (markdown works if surrounded by blank lines)...
</div>
```

## Self-typing terminal

```html
<div class="m7-term">
  <span class="m7-term-title">your-harness</span>
  <span class="m7-term-line" data-kind="prompt">task the user typed</span>
  <span class="m7-term-line" data-kind="think" data-delay="350">thinking...</span>
  <span class="m7-term-line" data-kind="tool" data-delay="250">[tool] run_bash(head -5 data.csv)</span>
  <span class="m7-term-line" data-kind="tokens">tokens: 4,312 / 128,000</span>
  <span class="m7-term-line" data-kind="answer" data-delay="400">final answer text</span>
</div>
```

- kinds: `prompt` (typed, `$` prefix), `think` (gray italic), `tool` (green), `tokens` (dim), `answer` (typed, white).
- `data-delay` = ms pause before that line. JS adds the replay button; types on scroll-into-view; reduced-motion users see full text instantly.

## Token gauges (conic donuts; pct must be an INTEGER percent)

```html
<div class="m7-island">
  <p class="m7-island-title">WHO EATS A 32K-TOKEN TURN?</p>
  <div class="m7-gauges">
    <div class="m7-gauge" data-pct="12"><div class="m7-gauge-ring">0%</div><p class="m7-gauge-label"><b>maximal harness</b><br>3,922 tokens</p></div>
    <div class="m7-gauge" data-pct="46"><div class="m7-gauge-ring">0%</div><p class="m7-gauge-label"><b>10 eager skills</b><br>~15,000 tokens</p></div>
    <div class="m7-gauge" data-pct="1"><div class="m7-gauge-ring">0%</div><p class="m7-gauge-label"><b>10 lazy skills</b><br>~240 tokens</p></div>
  </div>
</div>
```

## Context tax meter

```html
<div class="m7-island">
  <p class="m7-island-title">CONTEXT TAX METER - PERMANENT PER-TURN OVERHEAD</p>
  <div class="m7-tax">
    <div class="m7-tax-row" style="--m7-w:10"><span class="m7-tax-name">pi</span><div class="m7-tax-track"><div class="m7-tax-fill">~1k</div></div><span class="m7-tax-note">minimal</span></div>
    <div class="m7-tax-row" data-tier="max" style="--m7-w:95"><span class="m7-tax-name">Claude Code / Codex</span><div class="m7-tax-track"><div class="m7-tax-fill">7-10k</div></div><span class="m7-tax-note">maximal</span></div>
  </div>
</div>
```

- `--m7-w` = bar width percent. `data-tier="max"` renders the gray bar. Bars animate on reveal.

## Quiz (one per concept page; distractor feedback must TEACH a real failure mode)

```html
<div class="m7-island m7-quiz">
  <p class="m7-island-title">CHECK YOUR UNDERSTANDING</p>
  <p class="m7-quiz-q">The question?</p>
  <button class="m7-quiz-opt" data-fb="Why this is wrong and what it teaches.">Distractor A</button>
  <button class="m7-quiz-opt" data-right data-fb="Why this is right.">Correct answer</button>
  <button class="m7-quiz-opt" data-fb="Why this is wrong.">Distractor C</button>
</div>
```

## Predict-before-reveal

```html
<div class="m7-island m7-bet" data-answer="3,922 tokens" data-explain="measured with tiktoken in Exercise 2; the minimal harness pays just 365.">
  <p class="m7-island-title">PLACE YOUR BET</p>
  <p class="m7-quiz-q">Before you scroll: how many tokens does the bundled maximal config inject per turn?</p>
  <div class="m7-bet-opts">
    <button class="m7-bet-opt">~500</button>
    <button class="m7-bet-opt">~1,500</button>
    <button class="m7-bet-opt">~4,000</button>
    <button class="m7-bet-opt">~9,000</button>
  </div>
</div>
```

## Bento grid (landing page)

```html
<div class="m7-bento">
  <div class="m7-cell is-wide is-tall"><h4>YOU WILL BUILD</h4>...</div>
  <div class="m7-cell"><h4>DURATION</h4><span class="m7-big">2-3 h</span>self-paced</div>
  ...
</div>
```

## Chips (replace ad-hoc colored spans)

```html
<span class="m7-chip">OPEN SOURCE</span>
<span class="m7-chip is-green">NemoClaw ✓</span>
<span class="m7-chip is-outline-green">VERIFIED</span>
```

## Verified skill card

```html
<div class="m7-skillcard">
  <div class="m7-skillcard-head"><span class="m7-skillcard-name">accelerated-computing-cudf</span><span class="m7-chip is-green">NVIDIA VERIFIED ✓</span></div>
  <p>description...</p>
  <ul>
    <li><b>Owner</b> NVIDIA · <b>License</b> CC-BY-4.0 AND Apache-2.0</li>
    <li><b>SkillSpector</b> <span class="m7-check">✓</span> prompt injection <span class="m7-check">✓</span> tool poisoning <span class="m7-check">✓</span> dangerous code</li>
    <li><b>Signature</b> skill.oms.sig - OpenSSF Model Signing</li>
  </ul>
</div>
```

## Chooser

Wrap the existing nested `<details>` decision flow in `<div class="m7-choose"> ... </div>`
(keep blank lines so inner markdown renders). Recommendation blockquotes inside get the
green card styling automatically.

## Reveal-on-scroll

Add `class="m7-reveal"` (optionally `style="--i:1"`, `--i:2`... for stagger) to islands,
bento cells, and skill cards. Never to text paragraphs.

## Hard rules

1. Keep ALL `<button onclick="...">` jupyter-link buttons exactly as they are (class-less, onclick intact).
2. Keep ALL `<!-- fold:break -->` comments in place.
3. Keep docsify-tabs syntax (`<!-- tabs:start -->` ... `#### **Tab**`) — tabs are restyled by CSS automatically.
4. Keep mermaid code fences — theme comes from index.html. REMOVE any `style ... fill:#hex` lines inside mermaid blocks (the theme handles color now).
5. No `<style>` blocks, no `style=""` except `--m7-w`/`--i` custom properties and the existing mascot float pattern (`style="float:right;max-width:240px;margin:20px;"`).
6. Mascot images: keep ONE per page, max-width 240px, never in the hero — place beside a later prose section.
7. Keep every link, code fence, and the instructional text intact unless the text directly describes a replaced visual.
8. ASCII only in attribute values (data-title etc.) — emoji fine in visible text.
