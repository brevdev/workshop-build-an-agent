# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right;max-width:300px;margin:25px;" />

Before diving into agent safety, let's make sure you have the API key you need for this module. The agents we work with in this module run on NVIDIA's models, so you'll need your NVIDIA API Key ready.

If you've already set this up in an earlier module, you're good to go — skip straight to the next page.

Use the <button onclick="openVoila('code/secrets_management/secrets_management_6.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set up your API Keys. You can also launch the Secrets Manager directly from the Jupyterlab launcher.

<details>
<summary><strong>Still need to set up your NVIDIA API Key? Expand for details.</strong></summary>

## NVIDIA API Key

This key powers the LLM judge that evaluates your agent's safety across constraint adherence, data protection, and injection resistance. It uses NVIDIA Nemotron for scoring.

NGC is the NVIDIA GPU Cloud. This is the repository for all NVIDIA software, models, and more. For this workshop, we will need an API Key in order to access models.

<details>
<summary>Don't have an account?</summary>

You can get free non-commercial access to NVIDIA NIMs with an [NVIDIA Developer Account](https://developer.nvidia.com/developer-program).
</details>

<details>
<summary>Don't have an API Key?</summary>

Manage your API Keys from the [NGC console](https://org.ngc.nvidia.com/setup/api-keys).

</details>

</details>

With your NVIDIA API key configured, you're all set to start exploring agent safety. Head over to [The Autonomous Agent Problem](intro_agent_safety) to understand why the guardrails from previous modules aren't enough.
