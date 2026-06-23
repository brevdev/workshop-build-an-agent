<div class="dx-hero" data-eyebrow="MODULE 07 / 05 - HANDS ON" data-title="Build the harness. Measure the tax. Drive the GPU." data-sub="Five exercises that take you from a minimal loop you write yourself to an agent that evolves its own skills." data-meta="EXERCISES::5|FORMAT::notebook or .py|ANSWERS::included"></div>

Five exercises. You'll build a minimal harness from scratch, measure the context tax, author a portable skill, put your GPU to work through a verified NVIDIA skill, and finish with an agent that writes its own skills.

Work in the notebook <button onclick="openOrCreateFileInJupyterLab('code/7-agent-harnesses/harness_lab.ipynb');"><i class="fa-solid fa-flask"></i> harness_lab.ipynb</button> or directly in <button onclick="openOrCreateFileInJupyterLab('code/7-agent-harnesses/harness_lab.py');"><i class="fa-brands fa-python"></i> harness_lab.py</button> — they mirror each other. Stuck? Answer keys live alongside (`harness_lab.answers.py` / `.answers.ipynb`).

<!-- fold:break -->

## Exercise 1 — Build the Minimal Harness

pi proves a complete harness needs surprisingly little: a short system prompt, four tools, and a loop. You'll build exactly that — Read, Write, Edit, Bash around Nemotron.

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

Complete the agent loop in <button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'def build_bare_agent');"><i class="fas fa-code"></i> build_bare_agent( ... )</button> — wire the four tools to the model and implement the tool-calling loop.

Then run the same task in two very different harnesses. For the full, batteries-included end we'll use **Hermes** — NousResearch's open harness, branded *"the agent that grows with you,"* the one NVIDIA ships a [NemoClaw blueprint for](https://build.nvidia.com/nvidia/nemoclaw-for-hermes-agent), and the one you'll lean on again in Exercises 3 and 5.

<details>
<summary><strong>Set up Hermes (one-time, ~2 min)</strong></summary>

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

<details>
<summary>🆘 Need some help?</summary>

The loop pattern is: call the model with the message history → if the response contains tool calls, execute each and append a `ToolMessage` → repeat until the model answers without tool calls.

```python
while True:
    response = model_with_tools.invoke(messages)
    messages.append(response)
    if not response.tool_calls:
        return response.content
    for call in response.tool_calls:
        result = TOOL_REGISTRY[call["name"]](**call["args"])
        messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
```

</details>

<!-- fold:break -->

## Exercise 2 — Measure the Context Tax

The landscape page showed estimated overhead bars. Now produce real numbers from your own harness.

Complete <button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'def measure_context_tax');"><i class="fas fa-code"></i> measure_context_tax( ... )</button> to count the tokens of (a) your minimal system prompt + 4 tool schemas, and (b) the bundled maximal configuration (a Claude Code-style system prompt + 15 tool schemas).

Then implement <button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'def load_skills_lazily');"><i class="fas fa-code"></i> load_skills_lazily( ... )</button> — give the agent every skill in the `skills/` directory at a cost of *one line each*, expanding to the full body only on demand.

Your output will look something like:

```text
Minimal harness:    847 tokens/turn
Maximal harness:  8,212 tokens/turn        (9.7× tax)
10 eager skills: +14,920 tokens/turn
10 lazy skills:     +236 tokens/turn       (63× savings)
```

<div class="dx-island dx-reveal">
  <p class="dx-island-title">YOUR TARGETS</p>
  <div class="dx-gauges">
    <div class="dx-gauge" data-pct="1"><div class="dx-gauge-ring">0%</div><p class="dx-gauge-label"><b>minimal</b><br>365 tokens / 32K</p></div>
    <div class="dx-gauge" data-pct="12"><div class="dx-gauge-ring">0%</div><p class="dx-gauge-label"><b>maximal</b><br>3,922 tokens / 32K</p></div>
  </div>
</div>

<details>
<summary>🆘 Need some help?</summary>

Use `tiktoken` to count tokens, and remember the tax has two parts — the prompt *and* the tool schemas the harness registers:

```python
enc = tiktoken.get_encoding("cl100k_base")
schema_tokens = len(enc.encode(json.dumps([convert_to_openai_tool(t) for t in tools])))
```

For lazy loading, parse just the YAML frontmatter of each `SKILL.md` and inject only `name: description` lines, plus a `load_skill` tool the model can call to pull a full body in.

</details>

<!-- fold:break -->

## Exercise 3 — Author a Portable Skill

<img src="_static/robots/wrench.png" alt="Wrench Robot" style="float:right;max-width:240px;margin:20px;" />

Write your own `SKILL.md` — a **dataset profiler** skill that teaches an agent a systematic procedure for summarizing an unfamiliar CSV. Follow the format of <button onclick="openOrCreateFileInJupyterLab('skills/code_review/SKILL.md');"><i class="fa-solid fa-book"></i> skills/code_review/SKILL.md</button>: frontmatter with `name` and a trigger-worthy `description`, then the procedure.

Save it to `code/7-agent-harnesses/skills/dataset_profiler/SKILL.md`, then prove portability:

1. **Your harness:** load it through your Exercise 2 lazy loader and ask the agent to profile `test_data/sensor_readings.csv`. Watch it follow *your* procedure.
2. **Hermes:** drop the very same folder into Hermes's skills directory — Hermes auto-discovers everything in `~/.hermes/skills/` and is [agentskills.io](https://agentskills.io)-compatible, so there are zero changes to make:

```bash
cp -r code/7-agent-harnesses/skills/dataset_profiler ~/.hermes/skills/
```

Then start `hermes` and ask it to profile the same CSV. It follows the identical procedure you wrote. (For a skill that already lives in a repo or at a URL, Hermes can pull it directly — e.g. `hermes skills install NVIDIA/skills/accelerated-computing-cudf`, which you'll use in Exercise 4.)

One file. Two harnesses. Zero changes. *That* is the open skills spec doing its job.

<details>
<summary>🆘 Need some help?</summary>

The `description` line is what triggers skill loading — make it match the task vocabulary ("profile, summarize, or explore an unfamiliar CSV or DataFrame"), not the implementation. A good body gives the agent a numbered procedure (shape → dtypes → nulls → numeric distributions → cardinality → 3 surprising facts) and an output format to follow.

</details>

<!-- fold:break -->

## Exercise 4 — Verified NVIDIA Skill, Real GPU

Time to combine everything: governance from Module 6, skills from this module, and the GPU under your workshop.

First, fetch and **verify** the `accelerated-computing-cudf` skill before trusting it:

```bash
bash code/7-agent-harnesses/scripts/install_nvidia_skill.sh accelerated-computing-cudf
```

The script clones [NVIDIA/skills](https://github.com/NVIDIA/skills), checks the skill's `skill.oms.sig` signature, shows you the skill card, and installs it into your lab `skills/` directory. *Then* open a <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i>terminal</button>, start `watch -n 1 nvidia-smi`, and run:

```bash
python harness_lab.py --exercise 4
```

Your minimal harness — armed with the verified skill — gets asked to aggregate a large dataset. Watch the model choose `cudf.pandas`, and watch your GPU light up in `nvidia-smi`.

<details>
<summary>🆘 Need some help?</summary>

If GPU utilization stays at zero: check the dataset actually crossed the 100K-row size gate the skill teaches (the generator script makes 1M rows by default), and confirm cuDF imported GPU-side with `python -c "import cudf; print(cudf.__version__)"`. No GPU on your machine? The exercise prints a clear skip message and the answers notebook shows expected output.

</details>

<!-- fold:break -->

## Exercise 5 — The Self-Evolving Harness

The pi finale: an agent that improves its own scaffolding. Complete <button onclick="goToLineAndSelect('code/7-agent-harnesses/harness_lab.py', 'def self_evolve_skill');"><i class="fas fa-code"></i> self_evolve_skill( ... )</button> so that after finishing a task, the agent:

1. Reviews its own transcript for reusable procedure
2. Writes a brand-new `SKILL.md` capturing it
3. Saves it into the skills directory — where your lazy loader picks it up on the very next run

Run the same task twice (`--exercise 5`). The second run starts with the skill the agent wrote for itself the first time — fewer steps, fewer tokens, same result. That's **memory**, **skills**, **self-evolution**, and **token efficiency** — four of the five harness responsibilities — collapsing into a single loop.

> This is exactly the bet Hermes makes — it brands itself *"the agent that grows with you"* and persists self-authored skills into `~/.hermes/skills/`. You just built that mechanism by hand in ~30 lines. Same idea, no magic.

<details>
<summary>🆘 Need some help?</summary>

Prompt the model with its own transcript and the skill format spec, asking for *only* the SKILL.md content. Validate the frontmatter parses before saving — a malformed skill that breaks your loader on the next run is exactly the kind of self-evolution failure Module 6 warned about. (Production note: this is why NemoClaw treats the skills directory as a write-policied path.)

</details>

> All five exercises done? Head to [Wrapping Up](evaluating_harnesses) to connect the lab back to the production ecosystem.
