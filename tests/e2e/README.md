# Workshop release checks

Run these before publishing a change to the workshop. They work through the
modules with the shipped solutions, the way a learner would, and fail on drift
between the exercises, answer keys, lessons and tutor skills.

## 1. Static checks (minutes; no keys or GPU)

```bash
python -m pytest tests
```

Checks that every exercise still has its blanks and no answer key does, that
each tutor **Target** matches its answer key, that the Codex skill tree is in
sync, that lesson file links and code selectors resolve, that lesson images
exist, that workshop outputs and `secrets.env` are git-ignored, and that every
module's own test suite passes.

## 2. End-to-end run with hosted models (about an hour; needs the saved keys)

```bash
python tests/e2e/run_e2e.py                 # Modules 1, 2, 3, 5, 6, 7
python tests/e2e/run_e2e.py 4 --gpu         # Module 4, including GRPO training (about 40 minutes on an A100)
python tests/e2e/run_e2e.py 6 --live        # adds the NemoClaw sandbox checks (install it first, below)
python tests/e2e/run_e2e.py 7 --gpu         # adds the cuDF skill exercise
python tests/e2e/run_e2e.py 3 --only evaluate_rag   # rerun one step
```

Exercise files are never edited. Notebooks run from their answer keys (Module 1
uses each notebook's own "NEED SOME HELP" solutions), input prompts are answered
like a learner would, and generated files are removed afterwards. Module 5 needs
the backend venv the lesson creates (`demo/backend/.venv`). Each step retries
once, because hosted endpoints and DNS fail transiently; a step that passes on
its second attempt is reported as such. HTTP 429 rate limits are expected if
several runs share one key: wait and rerun the step.

## 3. Installers and the local NIM (manual, on a fresh workshop machine)

**NemoClaw.** Install with default answers, including an interrupted onboarding
that must resume, then remove everything:

```bash
python tests/e2e/nemoclaw_install.py --interrupt
python tests/e2e/run_e2e.py 6 --live
python tests/e2e/nemoclaw_install.py --uninstall
```

**OpenClaw.** Follow `.devx/6-agent-safety/setup_openclaw.md` Steps 1-6 by hand;
the wizard's screens change between releases. Check that choosing **Hatch later**
ends the installer with exit code 0 and that `openclaw gateway status` reports
`Connectivity probe: ok`.

**Local NIM (Module 2).** Needs a free GPU and disk:

```bash
python code/2-agentic-rag/nim_setup.py --check          # add --profile nvfp4 on a 124 GB disk
python code/2-agentic-rag/nim_setup.py [--profile nvfp4]
docker logs -f nemotron                                 # wait for "Application startup complete"
python code/2-agentic-rag/nim_smoke_test.py
python code/2-agentic-rag/nim_setup.py --teardown
```

**Workshop Health.** Open the Workshop Health tile and run the endpoint checks;
the GPU, Disk, Network and Local NIM rows should describe the machine correctly.

Record the wall-clock time of each module and the Module 4 held-out result
(`code/4-agent-customization/outputs/grpo_langgraph_cli/held_out_comparison.json`)
in the release notes.
