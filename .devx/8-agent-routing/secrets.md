<div class="dx-hero" data-eyebrow="MODULE 08 / SETUP" data-title="Two minutes of setup." data-sub="One NVIDIA API key is all this module needs - every model your router picks between is served through it." data-meta="NEEDS::NVIDIA_API_KEY|TIME::2 min"></div>

<img src="_static/robots/spyglass.png" alt="Secrets Management Robot" style="float:right;max-width:240px;margin:20px;" />

Before you can route anything, let's make sure you have the API key this module needs. Every model your router chooses between — the small cheap one and the large expensive one — is served by NVIDIA, so a single NVIDIA API Key covers the whole module.

If you've already set this up in an earlier module, you're good to go — skip straight to the next page.

Use the <button onclick="openVoila('code/secrets_management/secrets_management_8.ipynb');"><i class="fas fa-key"></i> Secrets Manager</button> to set up your API Keys. You can also launch the Secrets Manager directly from the Jupyterlab launcher.

Setting it here is all this module's **Routing Client** tile needs, too: the client reads the key straight out of `secrets.env` on every poll, so it finds a key you save now — or later, with the tile already open — on its own. Terminals are the one place you still export it yourself (`set -a; source /project/secrets.env; set +a`), and the gateway you'll start in Exercise 4 is the case that actually depends on it.

<details class="dx-peek is-setup">
<summary>Still need to set up your NVIDIA API Key? Expand for details.</summary>

## NVIDIA API Key

This key pays for every token you route in this module — the small model, the large model, and the judge that grades both.

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

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-secrets8-1">One gotcha worth reading now: the gateway reads the key from its own terminal</button>
<div id="aside-secrets8-1" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-secrets8-1" popovertargetaction="hide" aria-label="Close">×</button>

Later in this module you start a gateway that fronts several models. Its routes name the key with `api_key_env`, so the **gateway process** reads it from its own environment — not from your notebook, and not from the terminal next door. Export it in the terminal you start the gateway from:

```bash
set -a; source /project/secrets.env; set +a
bash scripts/serve_gateway.sh routes.toml
```

Keep that path absolute: `secrets.env` sits at the project root, so sourcing it by bare filename fails from the lab directory. And the gateway ships inside the Python wheel — the script above is how you start it, and there is no separate server binary to install.

Then check it from any other terminal:

```bash
curl -s localhost:4000/v1/models
```

A missing key is this module's most predictable failure. The script catches it before starting and prints that exact `source` line, absolute path already filled in.

</div>
</div>

With your NVIDIA API key configured, you're ready to find out what your agents have been costing you. Head over to [The Tokenomics Problem](intro_agent_routing) to see why one model for every call is the expensive default.
