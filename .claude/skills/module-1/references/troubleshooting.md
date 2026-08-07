# Module 1 Troubleshooting — tutor reference

**Triage first.** Is this an **environment/setup** problem (give direct fixes), an
**exercise** blank (guide, don't solve — see `exercises.md`), or **agent behavior**
(a teaching moment — see failure modes in `concepts.md`)? Environment fixes below
are fair to give directly; they aren't the learning content.

## API keys / `secrets.env`
Both notebooks load keys at the top:
`load_dotenv("../../variables.env")` then `load_dotenv("../../secrets.env")`.
`secrets.env` lives at the **repo root** and is **gitignored**, so it won't exist on
a fresh clone.

- **`KeyError: 'NVIDIA_API_KEY'`** or **HTTP 401 Unauthorized** from the model → the
  key isn't set. Fix: create `<repo-root>/secrets.env` containing
  `NVIDIA_API_KEY=nvapi-…` (free at https://build.nvidia.com → "Get API Key"), or
  use the workshop's **Secrets Manager**
  (`code/secrets_management/secrets_management_1.ipynb`, opens via Voila). **Restart
  the kernel** after adding keys so `load_dotenv` re-reads them.
- **Tavily error / empty results / `TAVILY_API_KEY` missing** → Module 1's search
  tool needs a Tavily key (free at https://tavily.com). Add `TAVILY_API_KEY=tvly-…`
  to `secrets.env`. **Module 1 requires both** the NVIDIA and Tavily keys; LangSmith
  is optional.
- Setup detail: `.devx/1-build-an-agent/secrets.md`. If they're bootstrapping the
  whole workshop locally, the `setup-workshop` skill writes `secrets.env`.

## Dependencies / imports
- The first cell runs `%pip install -r ../../requirements.txt`. If imports fail
  (`langchain`, `langchain_openai`, `tavily`, `openai`, `dotenv`), have them run
  that cell, then restart the kernel.
- **`ImportError: cannot import name 'create_agent'`** → needs LangChain v1
  (`langchain>1,<2`). Confirm the right kernel/environment (the DevX-Lab container
  has it); they may be on the wrong kernel or a stale venv.

## Async (`await`)
- `docgen_client.ipynb` uses `await agent.ainvoke(...)`. Top-level `await` works in
  Jupyter. If they copied it into a plain `.py` script it will error — wrap it in
  `asyncio.run(...)`, or run it in the notebook.
- **`RuntimeError: this event loop is already running`** → they wrapped it in
  `asyncio.run()` inside Jupyter; use a bare `await` in the notebook instead.

## Model endpoint
- Model `nvidia/nemotron-3-super-120b-a12b` at `https://integrate.api.nvidia.com/v1`.
- **404 / model-not-found** → the catalog id may have changed; have them confirm the
  current id on https://build.nvidia.com and that their key has access. Don't guess a
  replacement model name.
- **Connection/timeout** → network egress to `integrate.api.nvidia.com`; retry; check proxies.

## Kernel / notebook
- Stale state (a variable "not defined", an old import lingering) → "Restart Kernel
  and Run All" from the top. The notebooks are meant to run top-to-bottom.
- Running in Claude Code instead of the Jupyter UI: a notebook can be executed
  headless with `jupyter nbconvert --to notebook --execute <nb>` inside the project
  environment — but for the **exercises**, steer them to the interactive notebook so
  they fill the blanks themselves rather than auto-running solutions.

## Agent behavior (teaching moments, not bugs)
- **No citations / made-up sources** → tie to hallucination + the system prompt's
  citation rules; have them inspect `state["messages"]` and consider prompt tweaks.
- **Repeated identical searches / very many searches** → repeated-query /
  cost-runaway; look at the trace together.
- **Didn't search at all** → the model judged its own knowledge sufficient; discuss
  the system prompt's "you MUST use tavily_search" rule and when that fires.

These map directly onto Module 1's "things that can go wrong" and "what to watch
for," and preview Module 3 (evaluation). Use them to teach, not just to fix.
