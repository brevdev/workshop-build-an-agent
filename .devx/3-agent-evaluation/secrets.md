# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right; max-width:300px;margin:25px;" />


For this evaluation module to work, we will need to configure the Hugging Face API Key. Use the <button onclick="openVoila('code/secrets_management/secrets_management_3.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set this up. Note that the secrets you already set for Modules 1 and 2 should persist here as well. 

You can also launch the Secrets Manager directly from the Jupyterlab launcher.

## Hugging Face API Key

We need a Hugging Face Token to access datasets and models for evaluation. Make sure you have both **read** and **write** permissions enabled for your key!

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access with a [Hugging Face Account](https://huggingface.co/join).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your Access Tokens from the [Hugging Face Settings](https://huggingface.co/settings/tokens).

</details>

## Previous API Keys

We will be evaluating the previous agents that you built in Modules 1 and 2. This means that you should have the keys for these modules set for these agents to function properly. 

The good news is if you had set these previously, they should persist in the Secrets Manager!

<details>
<summary>⚠️ Still Need to Set These? Expand Me! </summary>

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

## NGC API Key

NGC is the NVIDIA GPU Cloud. This is the repository for all NVIDIA software, models, and more. For this workshop, we will need an API Key in order to access models.

<details>
<summary>⚠️ Dont have an account?</summary>

You can get free non-commercial access to NVIDIA NIMs with an [NVIDIA Developer Account](https://developer.nvidia.com/developer-program).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [NGC console](https://org.ngc.nvidia.com/setup/api-keys).

</details>

</details>

## Ready to Evaluate!

Once you have your Hugging Face API Key configured (and assuming you have the secrets from previous modules), you're ready to start building evaluation pipelines. Continue to [Introduction to Evaluation](intro_evaluation.md).
