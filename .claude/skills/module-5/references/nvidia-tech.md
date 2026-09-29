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
- **Framework vs model:** both shipped model choices are NVIDIA Nemotron models; LangChain/deepagents remain third-party libraries.
- **Sandbox vendors** (named in the security spectrum): Daytona, Modal, Runloop, **E2B**
  (Firecracker microVMs); **Bubblewrap/Seatbelt** (OS sandboxing used by Claude Code);
  **gVisor**, **Firecracker** — all third-party isolation tech.

> Clarifications learners ask: *"Is deepagents an NVIDIA library?"* → no, it's LangChain's;
> NVIDIA provides the hosted Nemotron models used here.
