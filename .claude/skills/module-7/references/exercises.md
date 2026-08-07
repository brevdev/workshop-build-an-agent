# Module 7 Exercises — tutor guide (hint ladders)

Help learners through the five lab exercises in `code/7-agent-harnesses/harness_lab.py`
**without completing them**. For each: the learning goal, a graduated hint ladder, common
mistakes, and the target. The teaching page (`harness_lab.md`) prescribes the `.py` track
and delineates every blank as a sub-exercise (**1a**, **1b**, **2a**, **2b(i)**, **2b(ii)**,
**5**) matching the `# TODO: Exercise …` markers; `harness_lab.ipynb` is the equivalent
self-contained notebook track (same blanks, one runnable cell per exercise). Ask which
track the learner is on before pointing at run commands.

**Rules specific to Module 7:**
- **Never paste a target, and never open/echo `harness_lab.answers.py` / `.answers.ipynb`,
  nor the completed `skills/.examples/` skill.** Targets below are for *your* calibration;
  the learner's self-serve escape hatch is the per-sub-exercise `🆘 Need some help?` block
  in `harness_lab.md` (`.py` track) or the `💡 NEED SOME HELP?` accordion under each
  exercise cell in `harness_lab.ipynb` (notebook track) — point them there as a last resort.
- **Exercises 3 and 5 are *authoring* exercises** (write a `SKILL.md`). **Coach the shape —
  never write the file for them.** A good skill is the learner's to draft.
- The code blanks raise `NotImplementedError("Complete Exercise N…")` until filled — that's
  the signal of an untouched blank, not a bug.

Provided scaffolding (do NOT have them rebuild it): the four `@tool`s
(`read_file`/`write_file`/`edit_file`/`run_bash`), `invoke_with_retry`, `count_tokens`,
`parse_frontmatter`, `run_with_skills`, `run_gpu_task`, `run_self_evolution_demo`, and
`MODEL_NAME = "nvidia/nemotron-3-super-120b-a12b"`.

Always start by asking what they've tried / reading the error or token output with them.

---
## Exercise 1 — Build the Minimal Harness (`build_bare_agent`)

### 1a · Create the model and bind the tools
- **Goal:** a tool-calling model — the pi insight that a harness needs very little.
- **L1:** "Which `langchain_nvidia` class wraps Nemotron, and what method tells the model
  which tools it may request? `tools` is already assembled for you just above."
- **L2:** "`ChatNVIDIA(model=MODEL_NAME, temperature=0.2)` then `.bind_tools(tools)` — assign the result to `model`."
- **Common mistakes:** forgetting `.bind_tools` (the model can't request tools); hardcoding the model string instead of `MODEL_NAME`; wrong temperature.
- **Target:** `model = ChatNVIDIA(model=MODEL_NAME, temperature=0.2).bind_tools(tools)`

### 1b · The agentic loop (the punchline)
- **Goal:** the loop that *is* the harness — call, execute tools, feed results back, repeat.
- **L1:** "One turn: call the model, append its reply. If it asked for **no** tools, you're
  done — return its text. Otherwise run each requested tool and feed the result back. What
  signals 'done'?"
- **L2:** "`response = invoke_with_retry(model, messages)`; `messages.append(response)`; `if
  not response.tool_calls: return response.content`; else for each `call` in
  `response.tool_calls`, run it via the local `registry` and append
  `ToolMessage(content=str(result), tool_call_id=call["id"])`." (The `🆘` block in
  `harness_lab.md` shows this exact pattern.)
- **Common mistakes:** checking `tool_calls` *before* appending the response; returning on the
  first turn (never looping); forgetting `tool_call_id=call["id"]` (the model can't match the
  result to its request); building an infinite loop by never returning on the no-tool case.
- **Target:** the call → append → (return | run-tools-and-append-`ToolMessage`) loop, executing
  each call through `registry[call["name"]]`.

> After 1a/1b they run `python harness_lab.py --exercise 1` (creates+reads `harness_hello.txt`)
> and the **same task in Hermes** (or their Module 6 OpenClaw) to *feel* the difference — same
> model, different car. Setting up Hermes is environment work (see `troubleshooting.md`), not
> an exercise; the point is *a* full harness, not a specific one.

---
## Exercise 2 — Measure the Context Tax

### 2a · `harness_overhead` — what every call costs
- **Goal:** the tax = system prompt **plus** the registered tool schemas, in tokens.
- **L1:** "Two parts, both billed every turn: the prompt text and the JSON of the tool
  schemas. You have `count_tokens(...)`. `convert_to_openai_tool(t)` turns a tool into its
  schema — and it also passes an *already*-converted dict schema straight through, so you
  can call it on every item uniformly (the maximal set is loaded from JSON as dicts)."
- **L2:** "Return `count_tokens(system_prompt) + count_tokens(json.dumps([...]))` where the
  list is `[convert_to_openai_tool(t) for t in tools]` — call it on every item; no type check."
- **Common mistakes:** counting only the prompt (forgetting the schemas — that's the whole
  point); **`callable()`-gating the conversion** — LangChain tool objects are NOT callable,
  so `... if callable(t) else t` skips converting them and `json.dumps` then fails with
  "Object of type StructuredTool is not JSON serializable"; forgetting `json.dumps`.
- **Target:** `count_tokens(system_prompt) + count_tokens(json.dumps([convert_to_openai_tool(t) for t in tools]))`

### 2b(i) · `load_skills_lazily` — build the one-line index
- **Goal:** each skill costs *one line* of context; full bodies stay out until needed.
- **L1:** "Inside the loop over each `SKILL.md`: read it, pull `name`/`description` (there's a
  `parse_frontmatter` helper), stash the *full text* somewhere the `load_skill` tool can reach,
  and add a single index line. What does the index line look like?"
- **L2:** "`text = skill_file.read_text()`; `meta = parse_frontmatter(text)`;
  `bodies[meta['name']] = text`; `index_lines.append(f\"- {meta['name']}: {meta['description']}\")`."
- **Common mistakes:** putting the **full body** in the index (that *is* eager loading — the
  bug the exercise exposes); not saving to `bodies` (then `load_skill` has nothing to return).
- **Target:** read → `parse_frontmatter` → store body in `bodies[name]` → append `"- {name}: {description}"`.

### 2b(ii) · `load_skill` — pull a body on demand
- **Goal:** the tool the model calls to expand one skill when relevant.
- **L1:** "You stored the bodies by name. Return the right one — and what if the name isn't there?"
- **L2:** "`return bodies.get(name, f\"ERROR: no skill named '{name}'\")` — return a string either way (don't raise)."
- **Common mistakes:** returning the name instead of the body; raising on a miss (the model
  should see an error string and recover).
- **Target:** `return bodies.get(name, <error string>)`.

> Running `--exercise 2` prints the minimal-vs-maximal tax and the eager-vs-lazy savings.
> Have them connect the numbers to the landscape page's bars — *their* harness, measured.

---
## Exercise 3 — Author a Portable Skill (`skills/dataset_profiler/SKILL.md`) — *authoring, no code blank*
**Coach the shape; do not write it.** The learner writes a `dataset_profiler` skill that
teaches an agent to summarize an unfamiliar CSV, following the format of the repo-root
`skills/code_review/SKILL.md`.
- **L1:** "Two parts: frontmatter (`name` + a `description`) and the body. The `description` is
  the *trigger* — the lazy loader matches it against the task. Should it describe the *task
  vocabulary* ('profile/summarize/explore an unfamiliar CSV or DataFrame') or the implementation?"
- **L2:** "Body = a numbered procedure the agent follows (e.g. shape → dtypes → nulls →
  numeric distributions → cardinality → a few surprising facts) plus an output format. Save it
  to `code/7-agent-harnesses/skills/dataset_profiler/SKILL.md`."
- **Prove portability (guide, don't run):** load it via their Exercise-2 lazy loader and ask
  the agent to profile `test_data/sensor_readings.csv`; then `cp -r` the folder into
  `~/.hermes/skills/` and ask Hermes the same — *one file, two harnesses, zero changes.*
- **Common mistakes:** a `description` that names the implementation (won't trigger); no
  numbered procedure (the agent has nothing to follow); wrong save path.
- **Do NOT** open `skills/.examples/` (the completed version) for them; point to
  `skills/code_review/SKILL.md` as the *format* model and let them write their own.

---
## Exercise 4 — Verified NVIDIA Skill, Real GPU (`run_gpu_task` is provided) — *ops, no code blank*
Guide the install → **verify** → run → watch loop; let them run it.
1. **Install + verify:** `bash code/7-agent-harnesses/scripts/install_nvidia_skill.sh accelerated-computing-cudf`
   — clones `NVIDIA/skills`, checks the `skill.oms.sig` signature, shows the skill card, installs into the lab `skills/`.
   Reinforce the Module 6 lesson: *verify the signature before trusting injected instructions.*
2. **Watch the GPU:** open a terminal, `watch -n 0.5 nvidia-smi`.
3. **Run:** `python harness_lab.py --exercise 4` — the minimal harness, armed with the skill,
   aggregates a ~1M-row CSV; watch the model choose `cudf.pandas` and the GPU light up.
- **If util stays at 0 / no GPU:** check the data crossed the 100K-row gate; confirm cuDF
  imported GPU-side; on a no-GPU box the exercise prints a skip message and the answers
  notebook shows expected output (it's a clean fallback, not a failure). See `troubleshooting.md`.
- **Teaching hook:** the cloud model only wrote a few hundred tokens of code; **your GPU** did
  the compute. The skill is what made it reach for cuDF correctly.

---
## Exercise 5 — The Self-Evolving Harness (`self_evolve_skill`)
- **Goal:** after a task, the agent writes a brand-new `SKILL.md` from its own transcript —
  memory + skills + self-evolution + token efficiency collapsing into one loop.
- **L1:** "There's a `SKILL_AUTHOR_PROMPT` and a `model` ready. Invoke the model with the
  transcript, then — before you save — what must you check so a malformed skill doesn't break
  your lazy loader on the next run? (Module 6 lesson.)"
- **L2:** "`resp = model.invoke(SKILL_AUTHOR_PROMPT.format(transcript=transcript))`; strip any
  ``` fences from `resp.content`; `meta = parse_frontmatter(content)` to **validate**; then
  `path = skills_dir / meta['name'] / 'SKILL.md'`, `mkdir(parents=True, exist_ok=True)`,
  `write_text(content)`, and `return path`."
- **Common mistakes:** saving without `parse_frontmatter` validation (a malformed skill breaks
  the loader next run — exactly the self-evolution failure M6 warned about); not stripping code
  fences; saving to the wrong directory (the loader globs `skills/*/SKILL.md`).
- **Target:** invoke → strip fences → `parse_frontmatter` (validate) → save to
  `skills_dir/<name>/SKILL.md` → return the path.

> They run `--exercise 5` **twice**: run 1 writes the skill; run 2 starts with it (fewer
> steps/tokens, same result). This is the pi/Hermes "grows with you" mechanism, by hand.

---
## Escalation protocol
1. Ask what they've tried / read the error or token output together.
2. **L1** conceptual nudge (which class/method/part of the tax/procedure).
3. **L2** specific pointer (the call/param/shape) — for Ex3/Ex5, the *shape* of the skill, never the file.
4. **Last resort** — the self-serve reveals: the sub-exercise's own `🆘 Need some help?`
   block in `harness_lab.md`, or the matching `💡 NEED SOME HELP?` accordion in
   `harness_lab.ipynb`. Never paste them; never open `harness_lab.answers.*` or
   `skills/.examples/`; never run the lab, author the skill, or drive the harness for them.
