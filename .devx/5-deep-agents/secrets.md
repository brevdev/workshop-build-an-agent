# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right; max-width:300px;margin:25px;" />

Before diving into deep agents, let's set up the API keys you'll need for this module. Your deep agent will use NVIDIA models for reasoning, Tavily for web search, and optionally LangSmith for tracing and debugging.

Use the <button onclick="openVoila('code/secrets_management/secrets_management_5.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set up your API Keys. You can also launch the Secrets Manager directly from the Jupyterlab launcher.

<details>
<summary>⚠️ Still Need to Set These? Expand for details! </summary>

## NVIDIA API Key

This key powers the LLM backbone — NVIDIA Nemotron and other models that drive your deep agent's reasoning.

NGC is the NVIDIA GPU Cloud. This is the repository for all NVIDIA software, models, and more. For this workshop, we will need an API Key in order to access models.

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free non-commercial access to NVIDIA NIMs with an [NVIDIA Developer Account](https://developer.nvidia.com/developer-program).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [NGC console](https://org.ngc.nvidia.com/setup/api-keys).

</details>

## Tavily API Key

Tavily is a search API designed for AI agents. It provides real-time web search capabilities that help agents gather up-to-date information from the internet. We will also need a Tavily API key for this workshop.

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to Tavily with a [Tavily Developer Account](https://tavily.com/).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [Tavily Dashboard](https://app.tavily.com/home).

</details>

## LangSmith API Key (Optional)

You'll use LangSmith to trace and debug your agent's multi-step tool calls — essential for understanding what's happening inside a deep agent's autonomous workflow.

LangSmith is LangChain's platform for testing, evaluating, and monitoring LLM applications. It provides tracing and debugging capabilities for your AI agents. Get your LangSmith API Key down below!

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to LangSmith with a [LangSmith Account](https://smith.langchain.com/).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [LangSmith Settings](https://smith.langchain.com/settings).

</details>

</details>

## Ready to Go!

With your API keys configured, you're all set to start exploring deep agents. Head over to [Introduction to Deep Agents](intro_deep_agents) to learn what makes deep agents different — and why they matter.
