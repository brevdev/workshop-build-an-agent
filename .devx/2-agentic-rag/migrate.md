<div class="dx-hero" data-eyebrow="MODULE 02 / 06 - LOCAL NIM" data-title="Migrate to Local NIM Microservices" data-meta="TIME::30 min|EXERCISES::3|GPU::local NIM (Nano)"></div>

[NVIDIA's API Catalog](https://build.nvidia.com) is an excellent resource for discovering and evaluating many different Generative AI models. There is a wide breadth of available models, and getting started is free.

These APIs are useful for fast starts and experiments. However, for the unlimited performance and control needed in production, deploy models locally with NVIDIA NIM microservice containers.

In this exercise, we will run our LLM model locally and transition our code to our private model.

<div class="dx-island dx-reveal">
  <p class="dx-island-title">API CATALOG vs LOCAL NIM</p>
  <p><span class="dx-chip">API CATALOG</span> Free, instant, and a huge model selection - ideal for fast starts, evaluation, and experiments.</p>
  <p><span class="dx-chip">LOCAL NIM</span> Unlimited performance, full control, and data privacy - what you want for production. This exercise migrates your LLM to a local NIM container.</p>
</div>

<!-- fold:break -->

## Find Deployment Instructions

<img src="_static/robots/relocate.png" alt="Box 'em up and bring 'em home." style="float:right;max-width:300px;margin:25px;" />

Our agent has been running on **Nemotron 3 Super (120B)** through NVIDIA's hosted API Catalog - powerful, and no local GPU required. To run locally, we'll switch to the smaller, more accessible [Nemotron 3 Nano](https://build.nvidia.com/nvidia/nemotron-3-nano-30b-a3b), which fits comfortably on a single GPU. For any model you want to run locally, look for the *Deploy* tab on its API Catalog page for step-by-step container instructions.

For our model, you can find the relevant details on the [deployment page](https://build.nvidia.com/nvidia/nemotron-3-nano-30b-a3b/deploy), including Docker commands and environment setup.

Whenever you want to deploy a new model, check its *Deploy* tab for reference instructions. We'll be closely following these directions, with slight modifications, to run our LLM locally.

<!-- fold:break -->

## Pull and Run the NIM

<img src="_static/robots/startup.png" alt="It's alive!" style="float:right;max-width:300px;margin:25px;" />

Start by opening a new <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> tab in Jupyter. We'll use this dedicated terminal to launch the NIM container.

In a typical development workflow, both your agent and NIM containers would run in the background, allowing you to multitask and iterate quickly. For this exercise, it's perfectly fine to run the NIM in the foreground so you can easily monitor its output and ensure everything starts up correctly.

<!-- fold:break -->

### Login to NGC

Login to the NVIDIA GPU Cloud (NGC) container registry.

```bash
echo $NVIDIA_API_KEY | \
  docker login nvcr.io \
  --username '$oauthtoken' \
  --password-stdin
```
<!-- fold:break -->

### Create your NIM Cache

Create a location for NIM containers to save their downloaded model files.

```bash
docker volume create nim-cache
```

<!-- fold:break -->

### 🔥 Let's go!

Light the fires with this Docker run command! This command will pull the NIM container image and model data files before hosting the model behind a local OpenAI compliant API. Start this command and go on to the next step.

```bash
docker run -it --rm \
    --name nemotron \
    --network workbench \
    --gpus 1 \
    --shm-size=16GB \
    -e NGC_API_KEY=$NVIDIA_API_KEY \
    -v nim-cache:/opt/nim/.cache \
    -u $(id -u) \
    -p 8000:8000 \
    nvcr.io/nim/nvidia/nemotron-3-nano:latest
```

<!-- fold:break -->

As the NIM container is starting, the log allows you to observe that it is:

1. Finding the most optimized profile for your hardware
2. Downloading the model files
3. Loading the model, and finally
4. Starting the model

*Expect everything to take a few minutes to stabilize.*

You'll know the NIM is ready for inference when it says `Application startup complete`, runs a built-in smoke test, then starts logging metrics.

<div class="dx-aside">
<button class="dx-aside-btn" popovertarget="aside-migrate-1">📜 If you're curious, it looks like this.</button>
<div id="aside-migrate-1" popover class="dx-aside-panel">
<button class="dx-aside-x" popovertarget="aside-migrate-1" popovertargetaction="hide" aria-label="Close">×</button>

```
INFO 2025-09-10 16:31:52.7 on.py:48] Waiting for application startup.
INFO 2025-09-10 16:31:52.239 on.py:62] Application startup complete.
INFO 2025-09-10 16:31:52.240 server.py:214] Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO 2025-09-10 16:31:55.944 api_server.py:516] An example cURL request:
curl -X 'POST' \
  'http://0.0.0.0:8000/v1/chat/completions' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "nvidia/nemotron-3-nano",
    "messages": [
      {
        "role":"user",
        "content":"Hello! How are you?"
      },
      {
        "role":"assistant",
        "content":"Hi! I am quite well, how can I help you today?"
      },
      {
        "role":"user",
        "content":"Can you write me a song?"
      }
    ],
    "top_p": 1,
    "n": 1,
    "max_tokens": 15,
    "stream": true,
    "frequency_penalty": 1.0,
    "stop": ["hello"]
  }'

INFO 2025-09-10 16:31:55.944 api_server.py:524] Responses API examples:
curl -X 'POST' \
  'http://0.0.0.0:8000/v1/responses' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "nvidia/nemotron-3-nano",
    "input": "Hello, how are you?",
    "max_output_tokens": 128,
    "stream": false
  }'


curl -X 'GET' \
  'http://0.0.0.0:8000/v1/responses/resp_123456' \
  -H 'accept: application/json'


curl -X 'POST' \
  'http://0.0.0.0:8000/v1/responses/resp_123456/cancel' \
  -H 'accept: application/json'

INFO 2025-09-10 16:32:05.957 metrics.py:386] Avg prompt throughput: 0.2 tokens/s, Avg generation throughput: 1.1 tokens/s, Running: 0 reqs, Swapped: 0 reqs, Pending: 0 reqs, GPU KV cache usage: 0.0%, CPU KV cache usage: 0.0%.
```

</div>
</div>

<!-- fold:break -->

## Test the NIM

Before moving on, let's verify that the NIM is running correctly by sending it a test request.

Open a new <button onclick="openNewTerminal();"><i class="fas fa-terminal"></i> terminal</button> tab, and run the following test command:

```bash
curl -X 'POST' \
  'http://nemotron:8000/v1/chat/completions' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
      "model": "nvidia/nemotron-3-nano",
      "messages": [{"role":"user", "content":"Which number is larger, 9.11 or 9.8?"}],
      "max_tokens": 64
  }'
```

You should see the model start to answer the question, then get cut off after 64 tokens.

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

Go back to our <button onclick="launch('Simple Agents Client');"><i class="fa-solid fa-rocket"></i> Simple Agents Client</button> and try prompting the agent again. If everything was successful, you should notice no change!

Although... if you look at the log messages for the NIM, you should start seeing messages like this:

```
INFO 2025-09-10 19:08:21.184 httptools_impl.py:481] 172.19.0.3:35474 - "POST /v1/chat/completions HTTP/1.1" 200
```

<!-- fold:break -->

## Keep Going!

<img src="_static/robots/hiking.png" alt="You can reach the top." style="float:right;max-width:300px;margin:25px;" />

So far, we've only migrated one of our three models to run locally.

Recall that our agent also uses two additional models:

  - [Reranker: llama-nemotron-rerank-1b-v2](https://build.nvidia.com/nvidia/llama-nemotron-rerank-1b-v2)
  - [Embedding: llama-nemotron-embed-1b-v2](https://build.nvidia.com/nvidia/llama-nemotron-embed-1b-v2)

If you have access to a second GPU, consider running these models locally as well. You can follow the same process as before: consult the official docs for each model, launch their NIM endpoints, and update your agent code to point to the new local URLs (using the `base_url` parameter).

Running all three models locally will give you full control over your agent's stack and may improve performance. Give it a try!
