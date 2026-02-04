# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right; max-width:300px;margin:25px;" />


For this customization module to work, we will need to configure the NVIDIA API Key. Use the <button onclick="openVoila('code/secrets_management/secrets_management_4.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set this up. Note that the secrets you already set for Modules 1 through 3 should persist here as well. 

You can also launch the Secrets Manager directly from the Jupyterlab launcher.

## NVIDIA API Key

NVIDIA API Key provides access to NVIDIA's AI services and models. For this customization module, we will need an API Key to access and customize NVIDIA models.

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free non-commercial access to NVIDIA NIMs with an [NVIDIA Developer Account](https://developer.nvidia.com/developer-program).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [NGC console](https://org.ngc.nvidia.com/setup/api-keys).

</details>

## Previous API Keys

If you had set these previously, they should persist in the Secrets Manager! These keys are not required for this module. 

<details>
<summary>⚠️ Still Want to Set These? Expand Me!</summary>

## Tavily API Key

Tavily is a search API designed for AI agents. It provides real-time web search capabilities that help agents gather up-to-date information from the internet.

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to Tavily with a [Tavily Developer Account](https://tavily.com/).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [Tavily Dashboard](https://app.tavily.com/home).

</details>

## LangSmith API Key (Optional)

LangSmith is LangChain's platform for testing, evaluating, and monitoring LLM applications. It provides tracing and debugging capabilities for your AI agents.

<details>
<summary>⚠️ Don't have an account?</summary>

You can get free access to LangSmith with a [LangSmith Account](https://smith.langchain.com/).
</details>

<details>
<summary>⚠️ Don't have an API Key?</summary>

Manage your API Keys from the [LangSmith Settings](https://smith.langchain.com/settings).

</details>

</details>

## Ready to Customize!

Once you have your NVIDIA API Key configured, you're ready to start customizing your agents. Continue to [Why Customize Agents?](intro_customization.md).
