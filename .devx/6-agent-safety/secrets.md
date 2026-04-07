# Setting up Secrets

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right;max-width:300px;margin:25px;" />

Before diving into agent safety, let's make sure you have the API key you need for this module. The safety evaluation exercises use NVIDIA models as LLM-as-judge evaluators, so you'll need your NVIDIA API Key ready.

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

<!-- fold:break -->

## What You Won't Need

Unlike Module 5, this module does **not** require Tavily or LangSmith keys. All exercises run against local policy files, local test data, and the NVIDIA API for LLM-as-judge evaluation.

| Key | Required? | Used For |
|-----|-----------|----------|
| NVIDIA API Key | Yes | LLM-as-judge safety evaluation (Exercises 4 and 5) |
| Tavily API Key | No | Not used in this module |
| LangSmith API Key | No | Not used in this module |

## Ready to Go!

With your NVIDIA API key configured, you're all set to start exploring agent safety. Head over to [The Autonomous Agent Problem](intro_agent_safety) to understand why the guardrails from previous modules aren't enough.
