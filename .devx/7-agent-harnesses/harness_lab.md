<div class="dx-hero" data-eyebrow="MODULE 07 / 05 - HANDS ON" data-title="Build the harness. Measure the tax. Drive the GPU." data-sub="Five exercises that take you from a minimal loop you write yourself to an agent that evolves its own skills." data-meta="TIME::90 min|EXERCISES::5|FORMAT::.py (notebook alt)|ANSWERS::included"></div>

Five exercises. You'll build a minimal harness from scratch, measure the context tax, author a portable skill, put your GPU to work through a verified NVIDIA skill, and finish with an agent that writes its own skills.

This page follows <button onclick="openOrCreateFileInJupyterLab('code/7-agent-harnesses/harness_lab.py');"><i class="fa-brands fa-python"></i> harness_lab.py</button>. Each exercise has one or more blanks marked `# TODO: Exercise …` in that file — the sub-exercise labels below (**1a**, **1b**, **2a**, **2b**…) match those markers exactly, and each blank gets its own instructions and its own `🆘` solution on this page. Fill the blanks, then run one exercise at a time from a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button>:

```bash
cd code/7-agent-harnesses && python harness_lab.py --exercise 1   # …through 5
```

> **Prefer notebooks?** The same lab, cell for cell, lives in <button onclick="openOrCreateFileInJupyterLab('code/7-agent-harnesses/harness_lab.ipynb');"><i class="fa-solid fa-flask"></i> harness_lab.ipynb</button> — identical `TODO` blanks, one runnable cell per exercise, and a collapsible **💡 NEED SOME HELP?** solution built in under each blank. If you go that route, work the notebook top to bottom and skip the `python harness_lab.py` commands on this page; everything else here — the concepts, the sub-exercise guidance, the Hermes detour — applies unchanged. (Full answer keys for either track: `harness_lab.answers.py` / `harness_lab.answers.ipynb`.)

<!-- fold:break -->

## Exercise 1 — Build the Minimal Harness

pi proves a complete harness needs surprisingly little: a short system prompt, four tools, and a loop. You'll build exactly that — Read, Write, Edit, Bash around Nemotron — by filling two blanks inside `build_bare_agent`.

Here's what a finished Exercise 1 run looks like:

<div class="dx-term">
  <span class="dx-term-title">python harness_lab.py --exercise 1</span>
  <span class="dx-term-line" data-kind="prompt">create harness_hello.txt with the words minimal harness</span>
  <span class="dx-term-line" data-kind="think" data-delay="350">thinking...</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[tool] write_file(harness_hello.txt)</span>
  <span class="dx-term-line" data-kind="tool" data-delay="250">[tool] read_file(harness_hello.txt)</span>
  <span class="dx-term-line" data-kind="tokens">tokens: 1,102 / 128,000</span>
  <span class="dx-term-line" data-kind="answer" data-delay="400">Done - file created and verified: minimal harness</span>
</div>

### 1a — Create the model and bind the tools

<button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'TODO: Exercise 1a');"><i class="fas fa-code"></i> TODO: Exercise 1a</button> — one statement: construct the model client and hand it the tool list (already assembled just above as `tools`).

Use `ChatNVIDIA` with `MODEL_NAME`, `temperature=0.2`, `max_completion_tokens=4096` (the 1,024 default truncates long `write_file` calls mid-JSON), and `timeout=180` (a 120B model can exceed the 60s default on long generations) — then `.bind_tools(tools)` so the model knows which tools it may request.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
model = ChatNVIDIA(
    model=MODEL_NAME, temperature=0.2, max_completion_tokens=4096, timeout=180
).bind_tools(tools)
```

Skip `.bind_tools(tools)` and the model never sees the tool schemas — it will answer in prose instead of requesting `write_file`, and your loop in 1b will exit on the first turn having done nothing.

</details>

### 1b — The agentic loop

<button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'TODO: Exercise 1b');"><i class="fas fa-code"></i> TODO: Exercise 1b</button> — the ~10 lines that *are* the harness. One turn: call the model with the message history and append its response; if the response contains **no** tool calls, you're done — return its text; otherwise execute each requested tool and append a `ToolMessage` so the model sees the results next turn.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
response = invoke_with_retry(model, messages)
messages.append(response)
if not response.tool_calls:
    return response.content
for call in response.tool_calls:
    try:
        result = registry[call["name"]].invoke(call["args"])
    except Exception as exc:
        result = f"ERROR: {type(exc).__name__}: {str(exc)[:500]}"
    messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
```

Three details that matter: use the loop's local `registry` (not the module-level `TOOL_REGISTRY`) so extra tools like `load_skill` stay callable in later exercises; execute tools with `.invoke(call["args"])` — LangChain tool objects are not plain functions you can call directly; and feed tool errors back as the `ToolMessage` instead of letting them crash the loop — models occasionally emit a malformed call, and reading its own error is what lets the agent self-correct (that's tool-calling resilience, harness responsibility #4).

</details>

<!-- fold:break -->

### Run it — then feel the difference

Run the same task in two very different harnesses. For the full, batteries-included end we'll use **Hermes** — NousResearch's open harness, branded *"the agent that grows with you,"* the one NVIDIA ships a [NemoClaw blueprint for](https://build.nvidia.com/nvidia/nemoclaw-for-hermes-agent), and the one you'll lean on again in Exercises 3 and 5.

<details class="dx-peek">
<summary>Set up Hermes (one-time, ~2 min)</summary>

Install it and point it at the same Nemotron endpoint your minimal harness uses:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Run the wizard and choose the **Custom OpenAI-compatible endpoint** option:

```bash
hermes setup
```

When prompted, enter the NVIDIA endpoint, model, and your key — or skip the wizard and write `~/.hermes/config.yaml` directly:

```yaml
model:
  provider: custom
  default: nvidia/nemotron-3-super-120b-a12b
  base_url: https://integrate.api.nvidia.com/v1
  api_key: ${NVIDIA_API_KEY}
```

> Prefer to reuse the **OpenClaw** agent you already hardened in Module 6? That works too — the point is *a* full harness, not a specific one.

</details>

Now run the identical task in each:

1. **Your minimal harness:** `python harness_lab.py --exercise 1`
2. **Hermes:** run `hermes` and type the same request.

Both complete the task. Feel how different they are — verbosity, persistence, initiative, how much each one says before it acts. Same model. Different car.

<!-- fold:break -->

## Exercise 2 — Measure the Context Tax

The landscape page showed estimated overhead bars. Now produce real numbers from your own harness. Three blanks this time: the tax meter itself, then the two halves of the lazy skill loader.

### 2a — `harness_overhead`: what every call costs

<button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'TODO: Exercise 2a');"><i class="fas fa-code"></i> TODO: Exercise 2a</button> — return the tokens a harness pays on **every** call: the system prompt **plus** the JSON-serialized schemas of all registered tools. Run each tool through `convert_to_openai_tool()` — it accepts both LangChain tool objects and already-converted dict schemas.

The provided `measure_context_tax()` then calls your function twice: once with your minimal prompt + 4 tools, once with the bundled maximal configuration (a Claude Code-style system prompt + 15 tool schemas).

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
schemas = [convert_to_openai_tool(t) for t in tools]
return count_tokens(system_prompt) + count_tokens(json.dumps(schemas))
```

Counting only the prompt misses the point — the schemas are the bigger half of a maximal harness's tax. And don't `callable()`-gate the conversion: the maximal tools arrive from JSON as plain dicts, and `convert_to_openai_tool()` passes those through untouched.

</details>

<!-- fold:break -->

### 2b(i) — Build the one-line skill index

Lazy loading is the tax dodge: every installed skill costs *one line* of context, expanding to the full body only on demand. Two skills (`code_review`, `technical_writing`) come pre-installed so you have something to measure.

<button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'TODO: Exercise 2b(i)');"><i class="fas fa-code"></i> TODO: Exercise 2b(i)</button> — inside the loop over each `SKILL.md`: read the file, `parse_frontmatter()` it, store the full text in `bodies[meta["name"]]`, and append a `- {name}: {description}` line to `index_lines`.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
text = skill_file.read_text()
meta = parse_frontmatter(text)
bodies[meta["name"]] = text
index_lines.append(f"- {meta['name']}: {meta['description']}")
```

If you put the full body in the index you've rebuilt eager loading — the very bug this exercise exposes. The index gets one line per skill; the bodies stay in the dict until asked for.

</details>

### 2b(ii) — `load_skill`: pull a body on demand

<button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'TODO: Exercise 2b(ii)');"><i class="fas fa-code"></i> TODO: Exercise 2b(ii)</button> — the other half: the tool the model calls when an index line looks relevant. Return the stored full body for `name` — or an error *string* on a miss (don't raise; the model should read the error and recover).

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
return bodies.get(name, f"ERROR: no skill named {name!r}")
```

</details>

Run `python harness_lab.py --exercise 2`. A correct implementation prints exactly this:

```text
Minimal harness:     400 tokens/turn
Maximal harness:   3,922 tokens/turn   (9.8x tax)
2 eager skills: +516 tokens/turn
2 lazy skills:  +41 tokens/turn   (13x savings)
```

The savings scale with the catalog: at 30 installed skills, eager loading costs ~45,000 tokens per turn while the lazy index stays a few hundred. Rerun this after Exercises 3–5 and watch the skill lines grow.

<div class="dx-island dx-reveal">
  <p class="dx-island-title">YOUR TARGETS</p>
  <div class="dx-gauges">
    <div class="dx-gauge" data-pct="1"><div class="dx-gauge-ring">0%</div><p class="dx-gauge-label"><b>minimal</b><br>400 tokens / 32K</p></div>
    <div class="dx-gauge" data-pct="12"><div class="dx-gauge-ring">0%</div><p class="dx-gauge-label"><b>maximal</b><br>3,922 tokens / 32K</p></div>
  </div>
</div>

<!-- fold:break -->

## Exercise 3 — Author a Portable Skill

<img src="_static/robots/wrench.png" alt="Wrench Robot" style="float:right;max-width:240px;margin:20px;" />

No `TODO` in the Python this time — the blank is a whole new file. Write your own `SKILL.md`: a **dataset profiler** skill that teaches an agent a systematic procedure for summarizing an unfamiliar CSV. Follow the format of <button onclick="openOrCreateFileInJupyterLab('skills/code_review/SKILL.md');"><i class="fa-solid fa-book"></i> skills/code_review/SKILL.md</button>: frontmatter with `name` and a trigger-worthy `description`, then the procedure.

Save it to `code/7-agent-harnesses/skills/dataset_profiler/SKILL.md`, then prove portability:

1. **Your harness:** load it through your Exercise 2 lazy loader — `python harness_lab.py --exercise 3` asks the agent to profile `test_data/sensor_readings.csv`. Watch it follow *your* procedure.
2. **Hermes:** drop the very same folder into Hermes's skills directory — Hermes auto-discovers everything in `~/.hermes/skills/` and is [agentskills.io](https://agentskills.io)-compatible, so there are zero changes to make:

```bash
cp -r code/7-agent-harnesses/skills/dataset_profiler ~/.hermes/skills/
```

Then start `hermes` and ask it to profile the same CSV. It follows the identical procedure you wrote. (For a skill that already lives in a repo or at a URL, Hermes can pull it directly — e.g. `hermes skills install nvidia/skills/accelerated-computing-cudf`, which you'll use in Exercise 4.)

One file. Two harnesses. Zero changes. *That* is the open skills spec doing its job.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

The `description` line is what triggers skill loading — make it match the task vocabulary ("profile, summarize, or explore an unfamiliar CSV or DataFrame"), not the implementation. A good body gives the agent a numbered procedure and an output format to follow:

```markdown
---
name: dataset_profiler
description: Systematic procedure for profiling, summarizing, or exploring an unfamiliar CSV file or DataFrame
---

# Dataset Profiler Skill

Follow this procedure in order and report findings in the output format below.

1. **Shape & size** — row count, column count, file size on disk.
2. **Schema** — every column with its dtype; flag dtypes that look wrong.
3. **Nulls** — per-column null counts; call out any column over 5% null.
4. **Duplicates** — count of fully duplicated rows.
5. **Numeric distributions** — min / max / mean / std; flag impossible values.
6. **Cardinality** — unique counts; likely categoricals vs identifiers.
7. **Three surprising facts** — the most decision-relevant findings.

## Output format
(a compact template the agent fills in)
```

A fully worked version lives at `code/7-agent-harnesses/skills/.examples/dataset_profiler/SKILL.md` — but draft yours first; a skill you authored yourself is the one worth carrying across harnesses.

</details>

<!-- fold:break -->

## Exercise 4 — Verified NVIDIA Skill, Real GPU

Time to combine everything: governance from Module 6, skills from this module, and the GPU under your workshop. No blanks here either — `run_gpu_task` is provided. This one is an ops loop: **install → verify → run → watch**.

First, fetch and **verify** the `accelerated-computing-cudf` skill before trusting it:

```bash
bash code/7-agent-harnesses/scripts/install_nvidia_skill.sh accelerated-computing-cudf
```

The script clones [NVIDIA/skills](https://github.com/NVIDIA/skills), checks the skill's `skill.oms.sig` signature, shows you the skill card, and installs it into your lab `skills/` directory. *Then* open a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button>, start `watch -n 0.5 nvidia-smi`, and run:

```bash
python harness_lab.py --exercise 4
```

Your minimal harness — armed with the verified skill — gets asked to aggregate a large dataset. Watch the model choose `cudf.pandas`, and watch your GPU light up in `nvidia-smi`.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

If GPU utilization stays at zero: check the dataset actually crossed the 100K-row size gate the skill teaches (the generator script makes 1M rows by default), and confirm cuDF imported GPU-side with `python -c "import cudf; print(cudf.__version__)"` — if that fails, `pip install cudf-cu12`. No GPU on your machine? The exercise warns you up front and the agent falls back to pandas; the same aggregation still completes, just CPU-slow.

</details>

<!-- fold:break -->

## Exercise 5 — The Self-Evolving Harness

The pi finale: an agent that improves its own scaffolding. One blank, four steps.

<button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'TODO: Exercise 5');"><i class="fas fa-code"></i> TODO: Exercise 5</button> — complete `self_evolve_skill` so that after finishing a task, the agent:

1. Reviews its own transcript for reusable procedure — invoke the model with `SKILL_AUTHOR_PROMPT.format(transcript=...)`
2. Strips any Markdown code fences from the response
3. **Validates** the result with `parse_frontmatter()` *before* saving — a malformed skill breaks your lazy loader on the next run (the Module 6 lesson)
4. Saves it to `skills_dir / <name> / "SKILL.md"` and returns the path — where your lazy loader picks it up on the very next run

Run the same task twice (`--exercise 5`). The second run starts with the skill the agent wrote for itself the first time — fewer steps, fewer tokens, same result. That's **memory**, **skills**, **self-evolution**, and **token efficiency** — four of the five harness responsibilities — collapsing into a single loop.

> This is exactly the bet Hermes makes — it brands itself *"the agent that grows with you"* and persists self-authored skills into `~/.hermes/skills/`. You just built that mechanism by hand in ~30 lines. Same idea, no magic.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

````python
prompt = SKILL_AUTHOR_PROMPT.format(transcript=transcript)
skill_md = invoke_with_retry(model, prompt).content
skill_md = skill_md.strip().removeprefix("```markdown").removeprefix("```").removesuffix("```").strip()

meta = parse_frontmatter(skill_md)  # validate BEFORE saving
target = skills_dir / meta["name"] / "SKILL.md"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(skill_md)
print(f"🌱 Agent wrote itself a new skill: {target}")
return target
````

The `parse_frontmatter()` call is the line to internalize: validate *before* anything lands in the skills directory, not after the loader crashes on the next run — that's exactly the kind of self-evolution failure Module 6 warned about. (Production note: this is why NemoClaw treats the skills directory as a write-policied path.)

</details>

> All five exercises done? Head to [Wrapping Up](evaluating_harnesses) to connect the lab back to the production ecosystem.
