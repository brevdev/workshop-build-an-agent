# Module 1 NVIDIA technologies — tutor reference

What each NVIDIA (and adjacent third-party) technology is, its role in *this* module, and
where to learn more. Be precise about what is NVIDIA vs not — learners conflate these.

## NVIDIA
- **NVIDIA Nemotron 3 Super (120B)** — model id `nvidia/nemotron-3-super-120b-a12b`. The
  reasoning LLM that powers the agent (the "Model" pillar). Chosen for strong tool-calling
  and reasoning; hosted, so no local GPU is needed. Resource: https://build.nvidia.com.
- **NVIDIA API Catalog / NIM** — hosted inference at `https://integrate.api.nvidia.com/v1`,
  an OpenAI-compatible endpoint. "NIM" = NVIDIA Inference Microservices, the serving layer
  behind the catalog. This is what lets Module 1 run GPU-free. Resources:
  https://build.nvidia.com, https://docs.nvidia.com/nim.
- **NGC (NVIDIA GPU Cloud)** — where the `NVIDIA_API_KEY` is created/managed. Resource:
  https://org.ngc.nvidia.com/setup/api-keys.
- **NVIDIA AI Workbench** — the platform that hosts the DevX-Lab environment the workshop
  runs in (see the `nvwb` / `setup-workshop` skills).

## Third-party (clarify when asked — NOT NVIDIA)
- **LangChain** (`create_agent`) — builds the ReAct agent in `docgen_agent.py`. A
  framework; LangGraph (its stateful-graph layer) runs under the hood.
- **Tavily** — the web-search API behind the `search_tavily` tool (`TAVILY_API_KEY`).
- **OpenAI Python SDK / LangChain `ChatOpenAI`** — the from-scratch notebook
  (`intro_to_agents.ipynb`) uses the raw `OpenAI` client (`from openai import OpenAI`); the
  report agent (`docgen_agent.py`) uses LangChain's `ChatOpenAI`. Both are only the *client*
  talking to NVIDIA's OpenAI-compatible endpoint — neither uses an OpenAI model.

> Frequent confusion: seeing `ChatOpenAI`/`from openai import OpenAI`, learners think
> "this uses OpenAI's models." Clarify: it's the OpenAI-compatible *client/SDK*; the
> *model* is NVIDIA Nemotron served from NVIDIA's endpoint. Module 2 switches to the
> NVIDIA-native `ChatNVIDIA` client.
