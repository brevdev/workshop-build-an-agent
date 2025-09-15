# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right; max-width:300px;margin:25px;" />


For this agent to work, we will need to configure a few secrets. Use the <button onclick="openVoila('code/secrets_management.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set these up.

You can also launch the Secrets Manager from the launcher.

## OpenRouter API Key

OpenRouter is a unified API that provides access to multiple AI models from different providers, including NVIDIA's models. For this workshop, we will use OpenRouter to access the NVIDIA Nemotron Nano 9B v2 model.

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to OpenRouter with an [OpenRouter Account](https://openrouter.ai/). Nemotron Nano 9B v2 is a free to use model.
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [OpenRouter Keys page](https://openrouter.ai/keys) after logging into your account.

</details>

## NGC API Key

NGC is the NVIDIA GPU Cloud. This is the repository for all NVIDIA software, models, and more. You do **not** need to set this API Key for the Introduction to Agents workshop. 

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

## LangSmith API Key

LangSmith is LangChain's platform for testing, evaluating, and monitoring LLM applications. It provides tracing and debugging capabilities for your AI agents. Get your LangSmith API Key down below!

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to LangSmith with a [LangSmith Account](https://smith.langchain.com/).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [LangSmith Settings](https://smith.langchain.com/settings).

</details>

