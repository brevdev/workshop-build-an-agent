# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right; max-width:300px;margin:25px;" />


For this evaluation module to work, we will need to configure the Hugging Face API Key. Use the <button onclick="openVoila('code/secrets_management_3.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set this up. Note that the secrets you already set for Modules 1 and 2 should persist here as well. 

You can also launch the Secrets Manager from the launcher.

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

## Ready to Evaluate!

Once you have your Hugging Face API Key configured (and assuming you have the secrets from previous modules), you're ready to start building evaluation pipelines. Continue to [Introduction to Evaluation](intro.md).
