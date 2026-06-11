# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right;max-width:300px;margin:25px;" />

Before exploring agent harnesses, let's make sure you have the API key you need for this module. The agents and harnesses in this module run on NVIDIA's models, so you'll need your NVIDIA API Key ready.

If you've already set this up in an earlier module, you're good to go — skip straight to the next page.

Use the <button onclick="openVoila('code/secrets_management/secrets_management_6.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set up your API Keys. You can also launch the Secrets Manager directly from the Jupyterlab launcher.

<details>
<summary><strong>Still need to set up your NVIDIA API Key? Expand for details.</strong></summary>

## NVIDIA API Key

This key powers every harness you'll drive in this module — from the bare-bones agent loop you build by hand to the OpenClaw assistant from Module 6. All of them call NVIDIA Nemotron through the same endpoint.

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

With your NVIDIA API key configured, you're ready to pop the hood on your agents. Head over to [The Harness Layer](intro_agent_harnesses) to see what's really been running your agents all along.
