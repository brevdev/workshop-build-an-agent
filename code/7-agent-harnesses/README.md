# Module 7 — Agent Harnesses & Skills 🦾

**The big idea:** an LLM is just a brain in a jar. The *harness* is everything around it — memory, tools, skills, the loop. This module takes that layer apart and lets you build one yourself.

---

## Run it in 3 steps

```bash
# 1. Set your NVIDIA key (get one free at build.nvidia.com)
export NVIDIA_API_KEY=nvapi-xxxxxxxx

# 2. Install what the lab needs
pip install -r ../../requirements.txt

# 3. Do the exercises
python harness_lab.py --exercise 1
```

That's it. Five exercises, run them in order: `--exercise 1` → `5`.

> Prefer notebooks? Open **`harness_lab.ipynb`** instead. Stuck? Every answer is in the `.answers` files.

---

## The 5 exercises

| # | You build | In one line |
|---|-----------|-------------|
| 1 | A minimal harness | 4 tools + a loop = a working agent |
| 2 | The "context tax" meter | Measure what each harness costs per turn |
| 3 | A portable skill | Write it once, run it in any harness |
| 4 | A GPU skill | Drive your GPU with a signed NVIDIA cuDF skill |
| 5 | A self-evolving harness | The agent writes its own skill, then uses it |

---

## What's in this folder

```
harness_lab.py            ← do the exercises here (TODOs to fill in)
harness_lab.answers.py    ← the completed version
harness_lab.ipynb         ← same thing, as a notebook
skills/                   ← skills the agent loads (you add one in Ex 3)
scripts/                  ← test-data generator + NVIDIA skill installer
```

## Read the lesson

The full guided walkthrough (concepts, the harness landscape, diagrams) is the
web module — launch **"7. Agent Harnesses"** from the JupyterLab launcher, or
serve it locally:

```bash
cd ../../.devx/7-agent-harnesses && python3 -m http.server 8137
# then open http://localhost:8137
```

Built on NVIDIA Nemotron + [NVIDIA Verified Skills](https://github.com/NVIDIA/skills). Runs in any harness — including [Hermes](https://hermes-agent.nousresearch.com).
