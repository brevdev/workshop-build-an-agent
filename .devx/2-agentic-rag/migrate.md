<div class="dx-hero" data-eyebrow="MODULE 02 / 06 - LOCAL NIM" data-title="Migrate to Local NIM Microservices" data-meta="TIME::30 min|EXERCISES::3|GPU::local NIM (Nano)"></div>

[NVIDIA's API Catalog](https://build.nvidia.com) is an excellent resource for discovering and evaluating many different Generative AI models. There is a wide breadth of available models, and getting started is free.

These APIs are useful for fast starts and experiments. Local NVIDIA NIM containers give you deployment control, with throughput limited by hardware, model size, and configuration.

In this exercise, we will run our LLM model locally and transition our code to our private model.

<div class="dx-island dx-reveal">
  <p class="dx-island-title">API CATALOG vs LOCAL NIM</p>
  <p><span class="dx-chip">API CATALOG</span> Free, instant, and a huge model selection - ideal for fast starts, evaluation, and experiments.</p>
  <p><span class="dx-chip">LOCAL NIM</span> Control over model hosting and data handling. This exercise moves only the chat model: embeddings, reranking, and Tavily still use hosted services until you migrate or disable them too.</p>
</div>

<!-- fold:break -->

## Find Deployment Instructions

<img src="_static/robots/relocate.png" alt="Box 'em up and bring 'em home." style="float:right;max-width:300px;margin:25px;" />

Our agent has been running on **Nemotron 3 Super (120B)** through NVIDIA's hosted API Catalog - powerful, and no local GPU required. To run locally, we'll switch to the smaller, more accessible [Nemotron 3 Nano](https://build.nvidia.com/nvidia/nemotron-3-nano-30b-a3b), whose deployment needs depend on the GPU, precision, and model profile. Check the *Deploy* tab’s supported hardware, container instructions, and memory requirements against the machine’s free memory before starting.

For our model, you can find the relevant details on the [deployment page](https://build.nvidia.com/nvidia/nemotron-3-nano-30b-a3b/deploy), including Docker commands and environment setup.

This workshop pins **NIM 2.0.13 / vLLM 0.28.0** by its multi-architecture image digest in `code/2-agentic-rag/nim_setup.py`. The model and its output parsers must match: ordinary chat can work even when an agent's tool calls fail.

The pinned image uses CUDA 13. The launch helper checks for **R580 or newer** before downloading anything; see [NVIDIA's driver compatibility table](https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html#cuda-driver). An older driver needs a host administrator to assess a supported upgrade or [platform-specific compatibility setup](https://docs.nvidia.com/deploy/cuda-compatibility/forward-compatibility.html). The helper does not change the host driver. You can keep using the hosted agent if the local requirements are not met.

Check **free GPU memory and disk space on the Docker host**, including the model cache. For this image, the A100 BF16 profile downloads about 59 GiB of model files and the unpacked image occupies about 30 GiB; allow additional space during download. Other GPU/profile combinations differ. Stop training or other GPU services before starting this exercise.

<!-- fold:break -->

## Pull and Run the NIM

<img src="_static/robots/startup.png" alt="It's alive!" style="float:right;max-width:300px;margin:25px;" />

Open a new <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> tab in Jupyter and run commands from the project root:

```bash
cd /project
python code/2-agentic-rag/nim_setup.py --check
```

This checks Docker, the shared `workbench` network, the driver, the container name, and the presence of your saved NVIDIA key. **Save the key in Workshop Secrets Manager first.** Saving a key in a notebook does not export it into a new terminal; this helper loads `secrets.env` directly without printing the key or putting it in command arguments.

<!-- fold:break -->

### Inspect the launch configuration

```bash
python code/2-agentic-rag/nim_setup.py --print-command
```

The command creates a container named `nemotron` on the `workbench` network and mounts the `nim-cache` model volume. It uses a 16,384-token context and up to four concurrent sequences, with 80% of GPU memory allocated to Nano. This leaves some headroom for the optional retrieval models; check their requirements separately.

These model-specific settings are essential for our agent:

```text
--enable-auto-tool-choice
--tool-call-parser qwen3_coder
--reasoning-parser nemotron_v3
```

The tool parser converts Nano's generated tool markup into structured calls the agent can execute. The reasoning parser separates reasoning from visible answer content. These are the [built-in parsers NVIDIA specifies for Nemotron 3](https://docs.nvidia.com/nemo/labs-voice-agent/build-voice-agents/model-serving/v-llm-plugins/). Changing only `ChatNVIDIA`'s URL cannot configure the server's parsers.

<!-- fold:break -->

### Start the container

```bash
python code/2-agentic-rag/nim_setup.py
docker logs -f nemotron
```

The helper authenticates to NGC using the saved key, creates the model-cache volume, and starts the pinned container in the background. Docker may download the image before the helper returns. In the container log, watch for profile selection, model download, model loading, and then `Application startup complete`. A cold start can take several minutes.

Press **Ctrl+C** to stop following the logs; the background container keeps running. If startup exits, inspect `docker logs nemotron` before retrying. The helper will not overwrite an existing container.

<!-- fold:break -->

## Test an Actual Tool Round Trip

A successful chat request alone does not prove that this service can run an agent. From the project root, run:

```bash
python code/2-agentic-rag/nim_smoke_test.py
```

The test first checks readiness, then asks Nano to call a small verification tool using **automatic** tool choice. The tool generates a fresh code only after the model requests it. The script sends that result back with the matching tool-call ID and verifies that Nano's final answer reproduces the code.

You should see:

```text
PASS: readiness, automatic tool call, matching tool-call ID, and final answer from the tool result.
Verification code: workshop-...
```

This tests the same model → tool request → tool result → final answer cycle you built in Module 1. A plain answer, an HTTP error, a truncated response, an incorrect tool result, or visible unparsed reasoning markup fails the check. If the service is still loading, wait for readiness and retry. An `auto tool choice` error means the server was launched without the required parser flags; inspect its launch configuration before continuing.

<!-- fold:break -->

## Reconfigure the Agent

Now that your NIM is running locally, let's update your agent to use it.

In your agent code, you previously created the `llm` object with the <button onclick="goToLineAndSelect('code/2-agentic-rag/rag_agent.py', 'llm =');"><i class="fas fa-code"></i> ChatNVIDIA</button> class. Connect to your local NIM by setting `base_url` to `http://nemotron:8000/v1` and pointing `model` at the Nano you just launched (`nvidia/nemotron-3-nano`) when initializing `ChatNVIDIA`.

Refer to the [official LangChain documentation](https://python.langchain.com/docs/integrations/chat/nvidia_ai_endpoints/) for more details.

<details class="dx-peek is-solution">
<summary>🆘 Need some help?</summary>

```python
# Point the agent at your local Nemotron 3 Nano NIM
llm = ChatNVIDIA(
    base_url="http://nemotron:8000/v1",
    model="nvidia/nemotron-3-nano",
    temperature=0.6,
    top_p=0.95,
    max_tokens=8192
)
```

</details>

<!-- fold:break -->

## Test the Results

> **👷‍♂️ Heads Up:** For these steps, your `langgraph` server should still be running. If you stopped the server, make sure to [start it back up](running.md). If it is still running, no need to restart! It will see your changes.

Go back to our <button onclick="launch('Simple Agents Client');"><i class="fa-solid fa-rocket"></i> Simple Agents Client</button> and ask **“How do I connect to VPN?”** Confirm that the trace includes `company_llc_it_knowledge_base`, a returned tool result, and a final answer. Check its citations against those returned chunks. Nano is a different model, so wording and answer quality can differ from the hosted model.

The NIM log should also show successful requests for the model turns:

```
INFO 2025-09-10 19:08:21.184 httptools_impl.py:481] 172.19.0.3:35474 - "POST /v1/chat/completions HTTP/1.1" 200
```

<!-- fold:break -->

## Keep Going!

<img src="_static/robots/hiking.png" alt="You can reach the top." style="float:right;max-width:300px;margin:25px;" />

So far, we've only migrated one of our three models to run locally.

Recall that our agent also uses two additional models:

  - [Reranker: llama-nemotron-rerank-vl-1b-v2](https://build.nvidia.com/nvidia/llama-nemotron-rerank-vl-1b-v2)
  - [Embedding: nemotron-3-embed-1b](https://build.nvidia.com/nvidia/nemotron-3-embed-1b)

Local retrieval also requires supported embedding and reranking deployments. Check each model's deployment availability, GPU profiles, and free memory before running it; configure its endpoint separately with `base_url`.

Running all three models locally will give you full control over your agent's stack and may improve performance. Give it a try!


<!-- fold:break -->

## Release the GPU When Finished

For the container you created in this exercise:

```bash
docker stop nemotron
docker rm nemotron
```

Stopping it releases GPU memory. The `nim-cache` volume retains downloaded model files for a later run. If you also deployed local embedding/reranking containers, stop those when finished. Revert your agent's `llm` configuration to the hosted model before continuing without the local service.
