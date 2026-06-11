# The Harness Face-Off

<img src="_static/robots/debug.png" alt="Forensic comparison robot" style="float:right;max-width:300px;margin:25px;" />

You've built a harness and claimed it's "what makes the agent different." Time to prove it with a controlled experiment. Same model. Same prompts. The only thing that varies is the harness around the model. **Whatever differs, the harness did it.**

Three contenders, one model (`nvidia/nemotron-3-super-120b-a12b`) the whole way:

| Stack | What it is | How it's driven |
|-------|-----------|-----------------|
| **Bare model** | one call to the endpoint — no harness at all | a single `chat.completions` request |
| **Hermes** | your glass-box harness from Exercises 1–3 | `Harness.send()` |
| **OpenClaw** | Module 6's always-on harness | `openclaw agent -m "..."` |

> 💡 **Prerequisite:** the OpenClaw column needs Module 6's gateway running (`openclaw gateway status` → "Connectivity probe: ok"; if it's down, `openclaw gateway run`). If you skipped Module 6, run the first two columns — `faceoff.py` will print a hint where the OpenClaw column would be, and you can read it from the reference table below.

<!-- fold:break -->

## Exercise 4: Same Model, Three Machines

> *Subsystems: **all of them** · Recalls: Module 6's probe pattern · Files: `faceoff.py`*

<details>
<summary><strong>Step 0 — Feel the bare wire</strong></summary>

Before the harness, see what "no harness" actually means. Open a terminal and hit the endpoint directly:

```bash
curl -s https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $NVIDIA_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-super-120b-a12b","messages":[{"role":"user","content":"What is my name?"}]}'
```

It cannot know your name. There's no system prompt, no history, no memory — just one stateless call. That's the floor every harness builds up from.

</details>

<details>
<summary><strong>Step 1 — Complete the runner</strong></summary>

Open <button onclick="goToLineAndSelect('code/7-agent-harnesses/faceoff.py', 'TODO: Exercise 4');"><i class="fas fa-code"></i> faceoff.py — Exercise 4</button>. The bare-model and OpenClaw runners are written (the OpenClaw one reuses Module 6's `openclaw_wrapper`). You complete `run_hermes()` — drive your own harness across each probe's steps, and for the persistence probe, build a *fresh* `Harness` between steps to simulate a process restart.

</details>

<details>
<summary><strong>Step 2 — Run the face-off</strong></summary>

```bash
python3 faceoff.py
```

It runs six probes through all three stacks and prints a table plus a saved `workspace/faceoff_results.json`. Expected shape (replies will vary):

```text
PROBE                    | BARE MODEL                          | HERMES                              | OPENCLAW (host)
-------------------------------------------------------------------------------------------------------------------
Who are you?             | I am Nemotron 3 Super, a language…  | I am Hermes, and my personality…    | …SOUL.md persona…
Memory across a restart  | "deploy hint" is not a standard…    | The deploy hint is 'tarball-tues…   | …recalls…
```

</details>

<details>
<summary><strong>Step 3 — Fill the attribution table</strong></summary>

This is the deliverable. For each probe, decide *which harness subsystem* produced the difference. Try it yourself first, then check:

<details>
<summary>Reference: completed attribution table</summary>

| Probe | Bare model | Hermes | OpenClaw | Subsystem responsible |
|-------|-----------|--------|----------|----------------------|
| Who are you? | "I am Nemotron 3 Super…" (generic) | "I am Hermes… from HERMES.md" | SOUL.md persona | **Context assembly** (the system prompt) |
| Name within a session | forgets between calls | recalls | recalls | **The message list** (short-term memory is just a list) |
| Fact across a restart | impossible | recalls via MEMORY.md | recalls via workspace memory | **State** (MEMORY.md reloaded into the prompt) |
| Read a file | hallucinates or demurs | actually reads it | uses its own tools | **Tool registry + dispatch** (capability = tool surface) |
| Refusal / safety | may roleplay compliance | real `[tool error]`, explains | varies | **Gates + honest errors** |
| Env-var leak (M6 Probe 3) | explains hypothetically — no process | "no tool for that" | vanilla host agent *leaks* | **Tool surface as boundary** |

</details>

</details>

<details>
<summary>🆘 Need some help?</summary>

The solved `run_hermes()` is in `answer_key/faceoff.py`:

```python
agent = Harness(auto_approve=True)
for i, step in enumerate(steps):
    if restart_between and i > 0:
        agent = Harness(auto_approve=True)   # fresh process: only MEMORY.md persists
    out.append(agent.send(step))
```

</details>

> **What you just learned:** the gap between "an LLM" and "an agent" is 100% harness — and so is the gap between two different agents on the same model.

<!-- fold:break -->

## What the Face-Off Proves

Three takeaways, in increasing order of importance:

1. **Capability is harness.** Bare Nemotron can't read a file, remember your name, or persist a fact. Hermes can — not because the model got smarter, but because the harness added a loop, a tool registry, and a memory file. The entire difference between "a model" and "an agent" lives in the green layer.

2. **Behavior differences between *agents* are harness deltas.** Hermes and OpenClaw run the *same model* yet answer "who are you?" differently, because their context assembly loads different soul files. This is also why Module 3-style evaluation must pin the harness, not just the model — change the harness and you've changed the agent, even with identical weights.

3. **Everything you just attributed is still in-process.** Every subsystem in that table is code running inside the agent's own process — code a confused or compromised agent might be steered around. Module 6 drew an enforcement spectrum: *"from trusting the model, to trusting the container, to trusting the kernel."* Trusting the harness sits on that line between the model and the container. It is real, useful, and **not** the kernel.

> One question left: what happens when your harness meets a machine it cannot talk past? Head to [Hermes Enters the Sandbox](into_the_sandbox).
