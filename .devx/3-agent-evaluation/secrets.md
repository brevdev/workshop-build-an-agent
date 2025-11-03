# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right; max-width:300px;margin:25px;" />


For this module to work, we will need to configure a few secrets. Use the <button onclick="openVoila('code/secrets_management.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set these up.

You can also launch the Secrets Manager from the launcher.

## NGC API Key

If you completed the previous modules, you may already have this configured and don't need to update it. If you haven't added this key yet, please do so now. 

NGC is the NVIDIA GPU Cloud. This is the repository for all NVIDIA software, models, and more. For this workshop, we will need an API Key in order to access NVIDIA models for evaluation.

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free non-commercial access to NVIDIA NIMs with an [NVIDIA Developer Account](https://developer.nvidia.com/developer-program).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [NGC console](https://org.ngc.nvidia.com/setup/api-keys).

</details>

## OpenRouter API Key 

If you completed Module 1 (Build an AI Agent), you may already have this configured and don't need to update it. If you haven't added this key yet, please do so now. 

OpenRouter provides API access to NVIDIA's Nemotron models which we used in the document generation agent. 

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to OpenRouter with an [OpenRouter Account](https://openrouter.ai/). Nemotron Nano 9B v2 is a free to use model.
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [OpenRouter Keys page](https://openrouter.ai/keys) after logging into your account.

</details>

## Tavily API Key

If you completed Module 1 (Build an AI Agent), you may already have this configured and don't need to update it. If you haven't added this key yet, please do so now. 

Tavily is used by the report generation agent in Module 1 for web search tool calling capabilities. 

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to Tavily with a [Tavily Developer Account](https://tavily.com/).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [Tavily Dashboard](https://app.tavily.com/home).

</details>

## LangSmith API Key (Optional)

LangSmith is LangChain's platform for testing, evaluating, and monitoring LLM applications. 

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to LangSmith with a [LangSmith Account](https://smith.langchain.com/).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [LangSmith Settings](https://smith.langchain.com/settings).

</details>

## Ready to Evaluate!

Once you have your NGC, OpenRouter, and Tavily API Keys configured, you're ready to start building evaluation pipelines. Continue to [Introduction to Evaluation](intro.md) to learn about the metrics we'll use to assess agent performance.

