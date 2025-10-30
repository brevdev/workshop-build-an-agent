# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right; max-width:300px;margin:25px;" />


For this module to work, we will need to configure a few secrets. Use the <button onclick="openVoila('code/secrets_management.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set these up.

You can also launch the Secrets Manager from the launcher.

## NGC API Key

NGC is the NVIDIA GPU Cloud. This is the repository for all NVIDIA software, models, and more. For this workshop, we will need an API Key in order to access NVIDIA models for evaluation.

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free non-commercial access to NVIDIA NIMs with an [NVIDIA Developer Account](https://developer.nvidia.com/developer-program).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [NGC console](https://org.ngc.nvidia.com/setup/api-keys).

</details>

## LangSmith API Key

LangSmith is LangChain's platform for testing, evaluating, and monitoring LLM applications. It provides powerful dataset management and evaluation capabilities that we'll use in this module. If you haven't already set this up in previous modules, get your LangSmith API Key now!

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to LangSmith with a [LangSmith Account](https://smith.langchain.com/).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [LangSmith Settings](https://smith.langchain.com/settings).

</details>

## OpenRouter API Key (Optional)

If you completed Module 1 (Build an Agent), you already have this configured. OpenRouter provides access to NVIDIA's Nemotron models which we used in the document generation agent. You do **not** need to reconfigure this for the evaluation module.

## Tavily API Key (Optional)

If you completed Module 1 (Build an Agent), you already have this configured. Tavily is used by the report generation agent for web search. You do **not** need to reconfigure this for the evaluation module.

## Ready to Evaluate!

Once you have your NGC API Key and LangSmith API Key configured, you're ready to start building evaluation pipelines. Continue to [Understanding Evaluation Metrics](evaluation_metrics.md) to learn about the metrics we'll use to assess agent performance.

