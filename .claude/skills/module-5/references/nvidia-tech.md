# Module 5 NVIDIA technologies — tutor reference

NVIDIA vs third-party for the deep-agents module. Note: the deep-agent *framework* is
third-party; NVIDIA supplies the *models* and the explore-next blueprints.

## NVIDIA
- **NVIDIA Nemotron** — `nvidia/nemotron-3-super-120b-a12b`, the default model
  (`MODEL_MAP["nemotron"]`) via **`ChatNVIDIA`** (temp 0.3). Deep agents need a strong
  **tool-calling** model. Resource: build.nvidia.com.
- **NIM / API Catalog** — hosted inference for all the `MODEL_MAP` choices; `NVIDIA_API_KEY`.
- **AI-Q Research Assistant Blueprint** — NVIDIA's open reference for *enterprise* deep
  (research) agents, cited as where to go next. github.com/NVIDIA-AI-Blueprints/aiq.
- **NeMo Agent Toolkit** — NVIDIA's framework-agnostic connect/evaluate/profile library
  (explore-next). github.com/NVIDIA/NeMo-Agent-Toolkit.

## Third-party (NOT NVIDIA)
- **deepagents** — the deep-agent library (`create_deep_agent`, the `FilesystemBackend` /
  `LocalShellBackend` / `DockerSandboxBackend`). From the **LangChain** ecosystem, not NVIDIA.
- **LangGraph** — the compiled graph + checkpointer (`MemorySaver`) under deepagents.
- **Docker** — the sandbox isolation boundary (`DockerSandboxBackend`).
- **Tavily** — optional web-search tool (`TavilySearchResults`, `TAVILY_API_KEY`).
- **Model choices in `MODEL_MAP`** — note these include **non-NVIDIA models served via
  NVIDIA's endpoints**: `meta/llama-3.3-70b-instruct` (Meta), `deepseek-ai/deepseek-r1-0528`
  (DeepSeek). They run through `ChatNVIDIA`/NIM but the *models* aren't NVIDIA's. Only
  `nemotron` is an NVIDIA model.
- **Sandbox vendors** (named in the security spectrum): Daytona, Modal, Runloop, **E2B**
  (Firecracker microVMs); **Bubblewrap/Seatbelt** (OS sandboxing used by Claude Code);
  **gVisor**, **Firecracker** — all third-party isolation tech.

> Clarifications learners ask: *"Is deepagents an NVIDIA library?"* → no, it's LangChain's;
> NVIDIA provides the models it runs on. *"Are llama/deepseek NVIDIA models?"* → no — they're
> Meta/DeepSeek models *served through* NVIDIA's API; `nemotron` is the NVIDIA one.
