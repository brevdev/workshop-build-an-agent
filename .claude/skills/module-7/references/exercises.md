# Module 7 Exercises — tutor guide (hint ladders)

Help learners through the five lab exercises in `code/7-agent-harnesses/harness_lab.py`
**without completing them**. For each: the learning goal, a graduated hint ladder, common
mistakes, and the target. The teaching page (`harness_lab.md`) prescribes the `.py` track
and delineates every blank as a sub-exercise (**1a**, **1b**, **2a**, **2b(i)**, **2b(ii)**,
**5**) matching the `# TODO: Exercise …` markers; `harness_lab.ipynb` is the equivalent
self-contained notebook track (same blanks, one runnable cell per exercise). Ask which
track the learner is on before pointing at run commands.

**Targets are for checking the learner's work and calibrating hints; never paste or
dictate them, in whole or in part** (equivalent code is fine). L2 hints are pointers (where
to look, which variable holds the value), never the finished line.

**Rules specific to Module 7:**
- **Never open/echo `harness_lab.answers.py` / `.answers.ipynb`, nor the completed
  `skills/.examples/` skill** — check attempts against the targets below. The learner's
  self-serve escape hatch is the per-sub-exercise `🆘 Need some help?` block
  in `harness_lab.md` (`.py` track) or the `💡 NEED SOME HELP?` accordion under each
  exercise cell in `harness_lab.ipynb` (notebook track) — point them there as a last resort.
- **Exercises 3 and 5 are *authoring* exercises** (write a `SKILL.md`). **Coach the shape —
  never write the file for them.** A good skill is the learner's to draft.
- The code blanks 1b, 2a, 2b(i), 2b(ii) and 5 raise `NotImplementedError("Complete Exercise
  N…")` until filled — that's the signal of an untouched blank, not a bug. **1a is different:**
  it starts as `model = ...`, which raises nothing by itself (see 1a below).

Provided scaffolding (do NOT have them rebuild it): the four `@tool`s
(`read_file`/`write_file`/`edit_file`/`run_bash`), `invoke_with_retry`, `count_tokens`,
`parse_frontmatter`/`skill_target`/`read_skill_text` (from `skill_support.py`),
`run_with_skills`, `run_gpu_task`, `format_transcript`, `SKILL_AUTHOR_PROMPT`,
`run_self_evolution_demo`, and `MODEL_NAME = get_model("chat")` (currently
`nvidia/nemotron-3-super-120b-a12b`).

Always start by asking what they've tried / reading the error or token output with them.

---
## Exercise 1 — Build the Minimal Harness (`build_bare_agent`)

### 1a · Create the model and bind the tools
- **Goal:** a tool-calling model — the pi insight that a harness needs very little.
- **L1:** "Which `langchain_nvidia_ai_endpoints` class wraps Nemotron, and what method tells the model
  which tools it may request? `tools` is already assembled for you just above."
- **L2:** "The `# TODO: Exercise 1a` comment lists the four constructor settings and why two
  of them matter. Check `ChatNVIDIA`'s keyword names, then call the chat model's tool-binding
  method on the result with the `tools` list. Replace `None` with that expression."
- **Common mistakes:** forgetting `.bind_tools` (the model can't request tools); hardcoding the model string instead of `MODEL_NAME`; dropping `max_completion_tokens=4096` (long `write_file` calls get truncated mid-JSON) or `timeout=180`.
- **Unfilled signature:** no error of its own. Once 1b is filled, `--exercise 1` fails with `AttributeError: 'NoneType' object has no attribute 'invoke'` (from `invoke_with_retry`, after its retries).
- **Target:** `model = ChatNVIDIA(model=MODEL_NAME, temperature=0.2, max_completion_tokens=4096, timeout=180).bind_tools(tools)`

### 1b · The agentic loop (the punchline)
- **Goal:** the loop that *is* the harness — call, execute tools, feed results back, repeat.
- **L1:** "One turn: call the model, append its reply. If it asked for **no** tools, you're
  done — return its text. Otherwise run each requested tool and feed the result back. What
  signals 'done'?"
- **L2:** "The `# TODO: Exercise 1b` comment is the recipe, step by step, including the
  exact trace f-string. Tools live in the local `registry` dict (keyed by name); a LangChain
  tool runs via its `.invoke(args)` method, not by calling it. Wrap that in `try/except` so a
  failure becomes an `"ERROR: ..."` result. Each result goes back as a `ToolMessage` carrying
  the call's id."
- **Common mistakes:** checking `tool_calls` *before* appending the response; returning on the
  first turn (never looping); calling the tool object directly instead of `.invoke(...)`;
  using the module-level `TOOL_REGISTRY` (misses `load_skill` in later exercises); letting a
  tool exception crash the loop; forgetting `tool_call_id=call["id"]` (the model can't match
  the result to its request); never returning on the no-tool case (infinite loop).
- **Target:** `response = invoke_with_retry(model, messages)`; `messages.append(response)`; `if not response.tool_calls: return response.content`; for each `call` in `response.tool_calls`: `print(f"  🛠️  {call['name']}({json.dumps(call['args'])[:120]})")`, then `try: result = registry[call["name"]].invoke(call["args"])` / `except Exception as exc: result = f"ERROR: {type(exc).__name__}: {str(exc)[:500]}"`, then `messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))`. Any `"ERROR: ..."` string the model can read is fine.

> After 1a/1b they run `python harness_lab.py --exercise 1` (creates+reads `harness_hello.txt`)
> and the **same task in Hermes** (or their Module 6 OpenClaw) to *feel* the difference — same
> model, different car. Setting up Hermes is environment work (see `troubleshooting.md`), not
> an exercise; the point is *a* full harness, not a specific one.

---
## Exercise 2 — Measure the Context Tax

### 2a · `harness_overhead` — what every call costs
- **Goal:** the tax = system prompt **plus** the registered tool schemas, in tokens.
- **L1:** "Two parts, both included in the starting context: the prompt text and the JSON of the tool
  schemas. You have `count_tokens(...)`. `convert_to_openai_tool(t)` turns a tool into its
  schema — and it also passes an *already*-converted dict schema straight through, so you
  can call it on every item uniformly (the maximal set is loaded from JSON as dicts)."
- **L2:** "Count the prompt with `count_tokens`. For the schemas, convert every item of `tools`
  with `convert_to_openai_tool` (no type check — dicts pass through), serialize the whole
  list with the `json` module, and count that string too."
- **Common mistakes:** counting only the prompt (forgetting the schemas — that's the whole
  point); **`callable()`-gating the conversion** — LangChain tool objects are NOT callable,
  so `... if callable(t) else t` skips converting them and `json.dumps` then fails with
  "Object of type StructuredTool is not JSON serializable"; forgetting `json.dumps`.
- **Target:** `schemas = [convert_to_openai_tool(t) for t in tools]`; `return count_tokens(system_prompt) + count_tokens(json.dumps(schemas))`

### 2b(i) · `load_skills_lazily` — build the one-line index
- **Goal:** each skill costs *one line* of context; full bodies stay out until needed.
- **L1:** "Inside the loop over each `SKILL.md`: read it, pull `name`/`description` (there's a
  `parse_frontmatter` helper), stash the *full text* somewhere the `load_skill` tool can reach,
  and add a single index line. What does the index line look like?"
- **L2:** "`skill_support.py` (imported just above) has a reader that safely loads a skill
  file given `skill_file` and `skills_dir`, and `parse_frontmatter`, which returns a dict
  with `name` and `description`. Key `bodies` by the name; the index line format is in the TODO."
- **Common mistakes:** putting the **full body** in the index (that *is* eager loading — the
  bug the exercise exposes); not saving to `bodies` (then `load_skill` has nothing to return).
- **Target:** `text = read_skill_text(skill_file, skills_dir)`; `meta = parse_frontmatter(text)`; `bodies[meta["name"]] = text`; `index_lines.append(f"- {meta['name']}: {meta['description']}")`. (A plain `skill_file.read_text()` also works but skips `read_skill_text`'s folder-name check.)

### 2b(ii) · `load_skill` — pull a body on demand
- **Goal:** the tool the model calls to expand one skill when relevant.
- **L1:** "You stored the bodies by name. Return the right one — and what if the name isn't there?"
- **L2:** "Python dicts have a lookup method that takes a fallback value for a missing key.
  Make that fallback an error string (don't raise)."
- **Common mistakes:** returning the name instead of the body; raising on a miss (the model
  should see an error string and recover).
- **Target:** `return bodies.get(name, f"ERROR: no skill named {name!r}")` — any error string works.

> Running `--exercise 2` prints the minimal-vs-maximal tax and the eager-vs-lazy savings.
> Have them connect the numbers to the landscape page's bars — *their* harness, measured.

---
## Exercise 3 — Author a Portable Skill (`skills/dataset-profiler/SKILL.md`) — *authoring, no code blank*
**Coach the shape; do not write it.** The learner writes a `dataset-profiler` skill that
teaches an agent to summarize an unfamiliar CSV, following the format of the repo-root
`skills/code-review/SKILL.md`.
- **L1:** "Two parts: frontmatter (`name` + a `description`) and the body. The `description` is
  the *trigger* — the lazy loader matches it against the task. Should it describe the *task
  vocabulary* ('profile/summarize/explore an unfamiliar CSV or DataFrame') or the implementation?"
- **L2:** "Body = a numbered procedure the agent follows (e.g. shape → dtypes → nulls →
  numeric distributions → cardinality → a few surprising facts) plus an output format. Save it
  to `code/7-agent-harnesses/skills/dataset-profiler/SKILL.md`."
- **Prove portability (guide, don't run):** load it via their Exercise-2 lazy loader and ask
  the agent to profile `test_data/sensor_readings.csv`; then `cp -r` the folder into
  `~/.hermes/skills/` from the project root and ask Hermes the same. The file is unchanged;
  its runtime still needs the required libraries. Supply the workshop Python path when needed.
- **Common mistakes:** a `description` that names the implementation (won't trigger); no
  numbered procedure (the agent has nothing to follow); wrong save path.
- **Do NOT** open `skills/.examples/` (the completed version) for them; point to
  `skills/code-review/SKILL.md` as the *format* model and let them write their own.

---
## Exercise 4 — Verified NVIDIA Skill, Real GPU (`run_gpu_task` is provided) — *ops, no code blank*
Guide the install → **verify** → run → watch loop; let them run it.
1. **Install + verify:** `bash code/7-agent-harnesses/scripts/install_nvidia_skill.sh accelerated-computing-cudf`
   — clones `NVIDIA/skills`, checks the `skill.oms.sig` signature, shows the skill card, installs into the lab `skills/`.
   Reinforce the Module 6 lesson: *verify the signature before trusting injected instructions.*
2. **Watch the GPU:** open a terminal, `watch -n 0.5 nvidia-smi`.
3. **Run:** `python harness_lab.py --exercise 4` — the task asks for speed but never names the
   GPU; the skill supplies the how. Watch the agent load it, reach for cuDF, and light the GPU
   up; the closing 🧾 receipt says whether the skill was consulted (if not, rerun — loading is
   the model's call).
- **If util stays at 0 / no GPU:** confirm cuDF imports and inspect actual tool calls and
  outputs. Ask for pandas when GPU execution is unavailable; don't infer speed from utilization. See `troubleshooting.md`.
- **Teaching hook:** the cloud model only wrote a few hundred tokens of code; **your GPU** did
  the compute. The skill is what made it reach for cuDF correctly.

---
## Exercise 5 — The Self-Evolving Harness (`self_evolve_skill`)
- **Goal:** after a task, the agent writes a brand-new `SKILL.md` from its own transcript —
  memory + skills + self-evolution + token efficiency collapsing into one loop.
- **L1:** "There's a `SKILL_AUTHOR_PROMPT` and a `model` ready. Invoke the model with the
  transcript, then — before you save — what must you check so a malformed skill doesn't break
  your lazy loader on the next run? (Module 6 lesson.)"
- **L2:** "Follow the four numbered steps in the `# TODO: Exercise 5` comment: send the
  formatted `SKILL_AUTHOR_PROMPT` through `invoke_with_retry` (as in 1b), then read the reply's
  `.content`. String methods such as `removeprefix`/`removesuffix` handle the fences.
  `skill_target` (from `skill_support.py`) gives the save path from the validated name; that
  folder may not exist yet."
- **Common mistakes:** saving without `parse_frontmatter` validation (a malformed skill breaks
  the loader next run — exactly the self-evolution failure M6 warned about); not stripping code
  fences; building the path by hand instead of `skill_target` (wrong directory — the loader globs
  `skills/*/SKILL.md`); not creating the parent folder.
- **Target:** `prompt = SKILL_AUTHOR_PROMPT.format(transcript=transcript)`; `skill_md = invoke_with_retry(model, prompt).content`, stripped of ```` ``` ````/```` ```markdown ```` fences; `meta = parse_frontmatter(skill_md)` (validate first); `target = skill_target(skills_dir, meta["name"])`; `target.parent.mkdir(parents=True, exist_ok=True)`; `target.write_text(skill_md)`; `return target`.

> They run `--exercise 5` **once** — the demo plays both halves (run 1 solves the task bare and
> distills a skill; run 2 starts with it) and ends with a 🧾 line comparing the runs. This is
> the pi/Hermes "grows with you" mechanism, by hand.

---
## Escalation protocol
1. Ask what they've tried / read the error or token output together.
2. **L1** conceptual nudge (which class/method/part of the tax/procedure).
3. **L2** specific pointer (the call/param/shape) — for Ex3/Ex5, the *shape* of the skill, never the file.
4. **Last resort** — the self-serve reveals: the sub-exercise's own `🆘 Need some help?`
   block in `harness_lab.md`, or the matching `💡 NEED SOME HELP?` accordion in
   `harness_lab.ipynb`. Never paste them; never open `harness_lab.answers.*` or
   `skills/.examples/`; never run the lab, author the skill, or drive the harness for them.
