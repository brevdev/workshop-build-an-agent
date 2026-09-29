<div class="dx-hero" data-eyebrow="MODULE 07 / SETUP" data-title="Two minutes of setup." data-sub="The core lab uses an NVIDIA API key. Optional harnesses need their own setup." data-meta="NEEDS::NVIDIA_API_KEY|TIME::2 min"></div>

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right;max-width:240px;margin:20px;" />

Before exploring agent harnesses, let's make sure you have the API key you need for this module. The agents and harnesses in this module run on NVIDIA's models, so you'll need your NVIDIA API Key ready.

If you've already set this up in an earlier module, you're good to go — skip straight to the next page.

Use the <button onclick="openVoila('code/secrets_management/secrets_management_7.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set up your API Keys. You can also launch the Secrets Manager directly from the Jupyterlab launcher.

<details class="dx-peek is-setup">
<summary>Still need to set up your NVIDIA API Key? Expand for details.</summary>

## NVIDIA API Key

This key powers the lab’s Nemotron calls and can be reused in the optional Hermes custom-endpoint setup. Claude Code and Codex require their own model access.

NGC is the NVIDIA GPU Cloud. This is the repository for all NVIDIA software, models, and more. For this workshop, we will need an API Key in order to access models.

<details class="dx-peek is-setup">
<summary>Don't have an account?</summary>

You can get free non-commercial access to NVIDIA NIMs with an [NVIDIA Developer Account](https://developer.nvidia.com/developer-program).
</details>

<details class="dx-peek is-setup">
<summary>Don't have an API Key?</summary>

Manage your API Keys from the [NGC console](https://org.ngc.nvidia.com/setup/api-keys).

</details>

</details>

With your NVIDIA API key configured, you're ready to pop the hood on your agents. Head over to [The Harness Layer](intro_agent_harnesses) to see what's really been running your agents all along.
