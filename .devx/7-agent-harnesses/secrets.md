# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right;max-width:300px;margin:25px;" />

Hermes speaks to NVIDIA's models over raw HTTP, so you'll need your NVIDIA API Key in the environment before you build it.

If you've already set this up in an earlier module, you're good to go — skip straight to the next page.

Use the <button onclick="openVoila('code/secrets_management/secrets_management_7.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set up your API Keys. You can also launch the Secrets Manager directly from the Jupyterlab launcher.

<details>
<summary><strong>Still need to set up your NVIDIA API Key? Expand for details.</strong></summary>

## NVIDIA API Key

This key lets Hermes call `nvidia/nemotron-3-super-120b-a12b` at `https://integrate.api.nvidia.com/v1` — the same model and endpoint you used in Module 1.

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

> 💡 Keep an eye on this key — Exercise 5's punchline is doing inference **without** it.

With your NVIDIA API key configured, you're ready to meet the machine. Head over to [The Invisible Machine](intro_agent_harnesses).
