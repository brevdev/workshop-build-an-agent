"""Read-only workshop checks, served behind the JupyterLab proxy."""

import argparse
from concurrent.futures import ThreadPoolExecutor, wait
import contextlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import metadata
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

from dotenv import dotenv_values
from packaging.version import InvalidVersion, Version

from . import PROJECT_ROOT, get_model

STATIC = Path(__file__).with_name("static")
THEME = PROJECT_ROOT / ".devx/_static"
MODEL_SETTINGS = json.loads(Path(__file__).with_name("models.json").read_text())
MODULES = [
    ("Build an Agent", "1. Introduction to Agents", ["chat"], True),
    ("Agentic RAG", "2. Agentic RAG", ["chat", "embedding", "reranking"], True),
    ("Agent Evaluation", "3. Agent Evaluation", ["chat", "judge", "embedding", "reranking"], True),
    ("Agent Customization", "4. Agent Customization", ["fast_chat"], False),
    ("Deep Agents", "5. Deep Agents", ["chat", "fast_chat", "embedding", "reranking"], False),
    ("Agent Safety", "6. Agent Safety", ["chat", "fast_chat", "judge"], False),
    ("Agent Harnesses", "7. Agent Harnesses", ["chat"], False),
]


# Hosts the exercises, downloads and installers reach, and what each is for.
NETWORK_HOSTS = {
    "integrate.api.nvidia.com": "hosted models",
    "ai.api.nvidia.com": "hosted retrieval models",
    "api.tavily.com": "web search",
    "mcp.tavily.com": "remote MCP",
    "huggingface.co": "Module 4 model download",
    "nvcr.io": "Module 2 local NIM",
    "github.com": "Module 6 and 7 installers",
    "registry.npmjs.org": "OpenClaw and NemoClaw installers",
    "openclaw.ai": "OpenClaw installer",
    "www.nvidia.com": "NemoClaw installer",
}
# Module 4 GRPO training: model download plus merged export, and its GPU peak.
TRAINING_DISK_GB = 35
TRAINING_GPU_GB = 45  # the training notebook peaks around 43 GB on an A100


def row(label, status, detail, **extra):
    return {"label": label, "status": status, "detail": detail, **extra}


def credentials():
    values = dotenv_values(PROJECT_ROOT / "secrets.env")
    # A blank saved field clears an inherited key as well.
    return {key: (values.get(key) if key in values else os.getenv(key)) or ""
            for key in ("NVIDIA_API_KEY", "TAVILY_API_KEY", "LANGSMITH_API_KEY")}


def request_json(url, *, data=None, key=None, timeout=3):
    headers = {"Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, headers=headers,
                                     data=json.dumps(data).encode() if data is not None else None)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def local_service(label, port, path, expected, modules):
    try:
        value = request_json(f"http://127.0.0.1:{port}{path}")
        if expected(value):
            return row(label, "pass", f"Responding on port {port}.", modules=modules)
        return row(label, "fail", f"Port {port} is responding, but the expected service was not found.", modules=modules)
    except urllib.error.HTTPError:
        return row(label, "fail", f"Port {port} returned an error. Check its terminal.", modules=modules)
    except (ValueError, TypeError, AttributeError):
        return row(label, "fail", f"Port {port} returned an unexpected response. Check its terminal.", modules=modules)
    except OSError:
        return row(label, "idle", f"Start it when the lesson asks. Port {port}.", modules=modules)


def environment_checks():
    checks = [row("Python", "pass" if sys.version_info >= (3, 11) else "fail",
                  f"{sys.version.split()[0]} · Python 3.11 or newer required.")]
    packages = ("langchain", "langchain-nvidia-ai-endpoints", "langgraph", "faiss-cpu",
                "ragas", "deepagents", "ipywidgets", "python-dotenv")
    package_issues = []
    for name in packages:
        try:
            version = metadata.version(name)
            if name == "langchain-nvidia-ai-endpoints" and Version(version) < Version("1.4.3"):
                package_issues.append(f"{name} {version} (needs 1.4.3 or newer)")
        except metadata.PackageNotFoundError:
            package_issues.append(f"{name} is missing")
        except InvalidVersion:
            package_issues.append(f"{name} has an unrecognized version")
    checks.append(row("Workshop packages", "fail" if package_issues else "pass",
                      "; ".join(package_issues) + ". Rebuild the workshop environment."
                      if package_issues else "Core packages are installed. Endpoint checks test their services."))
    try:
        mem = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
        available = int(mem["MemAvailable"].split()[0]) / 1024 ** 2
        detail = f"{available:.0f} GiB available on the host."
        try:
            limit = Path("/sys/fs/cgroup/memory.max").read_text().strip()
            if limit != "max":
                detail += f" Container limit: {int(limit) / 1024 ** 3:.0f} GiB."
        except (OSError, ValueError):
            pass
        checks.append(row("Memory", "info", detail + " Training also needs free GPU memory."))
    except (OSError, KeyError, ValueError):
        checks.append(row("Memory", "unknown", "Memory information is unavailable."))
    try:
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.free,memory.total,driver_version",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=4, check=True)
        name, free, total, driver = [part.strip() for part in gpu.stdout.splitlines()[0].split(",")]
        try:
            free_gb, total_gb = int(free) / 1024, int(total) / 1024
            detail = f"{name} · {free_gb:.0f} of {total_gb:.0f} GB free · driver {driver}."
            if total_gb < TRAINING_GPU_GB:
                detail += f" Module 4 training needs about {TRAINING_GPU_GB} GB of GPU memory."
            elif free_gb < TRAINING_GPU_GB:
                detail += (f" Module 4 training needs about {TRAINING_GPU_GB} GB free; shut down other "
                           "notebook kernels or model containers first.")
        except ValueError:
            detail = f"{name} · free GPU memory is not reported separately · driver {driver}."
        checks.append(row("GPU", "info", detail))
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        checks.append(row("GPU", "idle", "No accessible GPU. Local training and the optional GPU lab need one."))
    try:
        free_disk = shutil.disk_usage("/").free / 1e9
        checks.append(row("Disk", "pass" if free_disk >= TRAINING_DISK_GB else "fail",
                          f"{free_disk:.0f} GB free. Module 4 training needs about {TRAINING_DISK_GB} GB; "
                          "the optional local NIM in Module 2 needs 56–101 GB, depending on its profile."))
    except OSError:
        checks.append(row("Disk", "unknown", "Free disk space is unavailable."))
    try:
        subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                       capture_output=True, timeout=4, check=True)
        checks.append(row("Docker", "pass", "Available for the Module 5 sandbox."))
    except (OSError, subprocess.SubprocessError):
        checks.append(row("Docker", "idle", "Needed for the Module 5 Docker sandbox. Check the workshop setup."))
    for command in ("openshell", "nemoclaw"):
        checks.append(row(command, "pass" if shutil.which(command) else "idle",
                          "Installed. Module 6 walks through setup." if shutil.which(command)
                          else "Install during Module 6 setup."))
    checks.append(network_check())
    checks.append(local_nim())
    return checks


def network_check():
    """Resolve every host the workshop needs; DNS failures look like exercise bugs otherwise."""
    executor = ThreadPoolExecutor(max_workers=len(NETWORK_HOSTS))
    futures = {executor.submit(socket.getaddrinfo, host, 443): host for host in NETWORK_HOSTS}
    done, _ = wait(futures, timeout=4)
    executor.shutdown(wait=False, cancel_futures=True)
    failed = [host for future, host in futures.items() if future not in done or future.exception()]
    if not failed:
        return row("Network", "pass", f"All {len(NETWORK_HOSTS)} workshop hosts resolve.")
    names = "; ".join(f"{host} ({NETWORK_HOSTS[host]})" for host in failed)
    return row("Network", "fail", f"Could not resolve {names}. DNS lookups can fail intermittently; "
                                  "refresh to check again before installs or downloads.")


def local_nim():
    """Report whether Module 2's optional local NIM can run here, without starting anything."""
    label = "Local NIM (optional)"
    try:
        spec = importlib.util.spec_from_file_location(
            "workshop_nim_setup", PROJECT_ROOT / "code/2-agentic-rag/nim_setup.py")
        nim_setup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nim_setup)
        state = subprocess.run(["docker", "ps", "-a", "--filter", f"name=^/{nim_setup.CONTAINER}$",
                                "--format", "{{.Status}}"], capture_output=True, text=True, timeout=5)
        if state.stdout.strip():
            running = state.stdout.startswith("Up")
            return row(label, "pass" if running else "info",
                       f"Container {nim_setup.CONTAINER!r}: {state.stdout.strip()}.", modules=[2])
        reason = ""
        for profile in ("auto", "nvfp4"):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    nim_setup.preflight(profile)
            except RuntimeError as exc:
                reason = str(exc)
                continue
            how = "" if profile == "auto" else " with `--profile nvfp4` (smaller download)"
            return row(label, "pass", f"This host can run the Module 2 local NIM{how}.", modules=[2])
        return row(label, "idle", f"Not available here: {reason} The hosted model works for every exercise.",
                   modules=[2])
    except Exception:
        return row(label, "unknown", "Could not check. Run `python code/2-agentic-rag/nim_setup.py --check`.",
                   modules=[2])


def sandbox_service():
    if not shutil.which("nemoclaw"):
        return row("NemoClaw sandbox", "idle", "Set it up during Module 6.", modules=[6])
    try:
        result = subprocess.run(["nemoclaw", os.getenv("NEMOCLAW_SANDBOX_NAME", "my-assistant"), "status"],
                                capture_output=True, text=True, timeout=5)
        output = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", result.stdout)
        if result.returncode == 0 and re.search(r"^\s*Phase:\s*Ready\b", output, re.MULTILINE):
            return row("NemoClaw sandbox", "pass", "Reports Ready. Use the lesson probes to check its behavior.", modules=[6])
    except (OSError, subprocess.SubprocessError):
        pass
    return row("NemoClaw sandbox", "fail", "Not ready. Run the control-plane health check in Module 6.", modules=[6])


def check_endpoint(role, key):
    model = get_model(role)
    label = MODEL_SETTINGS[role]["label"]
    common = {"role": role, "model": model, "modules": MODEL_SETTINGS[role]["modules"]}
    if not key:
        return row(label, "missing", "Add your NVIDIA key in Secrets Manager.", **common)
    base = "https://integrate.api.nvidia.com/v1"
    try:
        if role in ("chat", "fast_chat"):
            data = request_json(base + "/chat/completions", key=key, timeout=45, data={
                "model": model, "messages": [{"role": "user", "content": "Call workshop_check with status ready."}],
                "tools": [{"type": "function", "function": {"name": "workshop_check",
                    "description": "Confirm this small workshop check.",
                    "parameters": {"type": "object", "properties": {"status": {"type": "string"}},
                                   "required": ["status"], "additionalProperties": False}}}],
                "tool_choice": {"type": "function", "function": {"name": "workshop_check"}},
                "chat_template_kwargs": {"enable_thinking": False},
                "max_tokens": 1024, "temperature": 0,
            })
            calls = data["choices"][0]["message"].get("tool_calls", [])
            valid = any(call["function"]["name"] == "workshop_check"
                        and json.loads(call["function"]["arguments"]).get("status") == "ready" for call in calls)
            detail = "Returned a valid tool call."
        elif role == "judge":
            data = request_json(base + "/chat/completions", key=key, timeout=45, data={
                "model": model, "messages": [{"role": "user", "content": 'Return JSON with "score": 5 and "explanation": "ready".'}],
                "response_format": {"type": "json_object"},
                "chat_template_kwargs": {"enable_thinking": False},
                "max_tokens": 1024, "temperature": 0,
            })
            result = json.loads(data["choices"][0]["message"]["content"])
            explanation = result.get("explanation")
            valid = result.get("score") == 5 and isinstance(explanation, str) and bool(explanation.strip())
            detail = "Returned a structured rubric score."
        elif role == "embedding":
            data = request_json(base + "/embeddings", key=key, timeout=30, data={
                "model": model, "input": ["Workshop health check"], "input_type": "query", "truncate": "END"})
            vector = data["data"][0]["embedding"]
            valid = bool(vector) and all(isinstance(v, (int, float)) and math.isfinite(v) for v in vector)
            detail = "Returned an embedding."
        else:
            from langchain_nvidia_ai_endpoints import NVIDIARerank
            # Use the SDK's model-specific route, as the RAG exercises do.
            url = NVIDIARerank(model=model, api_key=key)._client.infer_url
            data = request_json(url, key=key, timeout=30, data={
                "model": model, "query": {"text": "Where is the workshop?"},
                "passages": [{"text": "The workshop runs in JupyterLab."}, {"text": "Bananas are yellow."}]})
            rankings = data["rankings"]
            valid = len(rankings) == 2 and {r["index"] for r in rankings} == {0, 1}
            valid = valid and all(isinstance(r["logit"], (int, float)) and math.isfinite(r["logit"]) for r in rankings)
            detail = "Ranked two short passages."
        return row(label, "pass" if valid else "fail", detail if valid else "The response did not pass the capability check. Try again.", **common)
    except urllib.error.HTTPError as exc:
        messages = {401: "The key was rejected. Update it in Secrets Manager.",
                    403: "This key does not have access to the endpoint.",
                    404: "This model endpoint was not found. Check the shared model setting.",
                    410: "This endpoint has retired. Update the shared model setting.",
                    429: "The service is busy or rate limited. Try again shortly."}
        return row(label, "fail", messages.get(exc.code, f"The service returned HTTP {exc.code}. Try again shortly."), **common)
    except (OSError, TimeoutError):
        return row(label, "fail", "The request timed out or could not connect. Check the network and retry.", **common)
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return row(label, "fail", "The service returned an unexpected response. Try again.", **common)
    except Exception:
        # The SDK can wrap provider failures in a plain Exception with its payload.
        return row(label, "fail", "The model check could not finish. Check the environment and retry.", **common)


def check_search(key):
    if not key:
        return row("Web search", "missing", "Add your Tavily key for the web search exercises.")
    try:
        data = request_json("https://api.tavily.com/search", timeout=20, data={
            "api_key": key, "query": "NVIDIA AI agents", "max_results": 1, "search_depth": "basic"})
        if not isinstance(data.get("results"), list) or not data["results"]:
            raise ValueError("No results")
        return row("Web search", "pass", "Returned a search result.")
    except (OSError, ValueError, TypeError, AttributeError):
        return row("Web search", "fail", "Search did not complete. Check the Tavily key and retry.")


class HealthState:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_checked = None
        self.endpoints = []
        self.search = row("Web search", "unknown", "Run endpoint checks to test search.")
        self.key_fingerprint = None

    def snapshot(self):
        keys = credentials()
        fingerprint = tuple(keys.values()) + tuple(get_model(role) for role in MODEL_SETTINGS)
        # Clear results if keys or configured models changed. Never send keys to the browser.
        if self.key_fingerprint != fingerprint:
            endpoints = []
            checked = None
            search = row("Web search", "unknown", "Run endpoint checks to test search.")
        else:
            endpoints, checked, search = self.endpoints, self.last_checked, self.search
        if not endpoints:
            endpoints = [row(cfg["label"], "unknown" if keys["NVIDIA_API_KEY"] else "missing",
                             "Run endpoint checks." if keys["NVIDIA_API_KEY"] else "Add your NVIDIA key in Secrets Manager.",
                             model=get_model(role), role=role, modules=cfg["modules"]) for role, cfg in MODEL_SETTINGS.items()]
        environment = environment_checks()
        key_rows = [row(label, "pass" if keys[key] else "missing" if required else "idle",
                        "Saved. Endpoint checks confirm it works." if keys[key] else detail)
                    for key, label, required, detail in [
                        ("NVIDIA_API_KEY", "NVIDIA", True, "Required for hosted models."),
                        ("TAVILY_API_KEY", "Tavily", True, "Needed for web search exercises."),
                        ("LANGSMITH_API_KEY", "LangSmith", False, "Optional tracing. The workshop works without it.")]]
        services = [
            local_service("RAG agent", 2024, "/ok", lambda r: r.get("ok") is True, [2, 3]),
            local_service("Training reward server", 8001, "/health", lambda r: r.get("status") in ("healthy", "ok"), [4]),
            local_service("Deep Agents backend", 8000, "/api/health", lambda r: r.get("status") == "ok", [5]),
            sandbox_service(),
        ]
        module_rows = []
        for number, (label, tile, roles, needs_search) in enumerate(MODULES, 1):
            relevant = [check for check in endpoints if check["role"] in roles]
            if any(c["status"] == "fail" for c in environment[:2]) or any(c["status"] in ("fail", "missing") for c in relevant):
                status, detail = "fail", "Resolve the setup or endpoint checks below."
            elif needs_search and (not keys["TAVILY_API_KEY"] or search["status"] == "fail"):
                status, detail = "fail", "Check web search before its exercises."
            elif any(c["status"] == "unknown" for c in relevant) or (needs_search and search["status"] == "unknown"):
                status, detail = "unknown", "Run endpoint checks before you start."
            else:
                status, detail = "pass", "Shared checks passed. Follow the lesson’s local setup steps."
            if number == 4:
                detail += f" Training also needs about {TRAINING_GPU_GB} GB of free GPU memory and {TRAINING_DISK_GB} GB of disk."
            module_rows.append(row(label, status, detail, number=number, tile=tile))
        return {"environment": environment, "keys": key_rows, "endpoints": endpoints,
                "search": search, "services": services, "modules": module_rows, "checked_at": checked}

    def check(self):
        if not self.lock.acquire(blocking=False):
            return False
        try:
            keys = credentials()
            groups = {}
            for role in MODEL_SETTINGS:
                groups.setdefault(get_model(role), []).append(role)

            def check_model(roles):
                results = []
                for role in roles:
                    # Chat and judge may share an endpoint. Avoid a burst at it.
                    if results:
                        time.sleep(2)
                    results.append(check_endpoint(role, keys["NVIDIA_API_KEY"]))
                return results

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(check_model, roles) for roles in groups.values()]
                search = executor.submit(check_search, keys["TAVILY_API_KEY"])
                results = {item["role"]: item for future in futures for item in future.result()}
                self.endpoints = [results[role] for role in MODEL_SETTINGS]
                self.search = search.result()
            self.last_checked = datetime.now(timezone.utc).isoformat()
            self.key_fingerprint = tuple(keys.values()) + tuple(get_model(role) for role in MODEL_SETTINGS)
            return True
        finally:
            self.lock.release()


class Handler(BaseHTTPRequestHandler):
    state = HealthState()

    def log_message(self, *_):
        pass

    def send(self, status, body, content_type="application/json"):
        body = body.encode() if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            self.send(200, json.dumps(self.state.snapshot()))
            return
        files = {"/": (STATIC / "index.html", "text/html; charset=utf-8"),
                 "/health.css": (STATIC / "health.css", "text/css"),
                 "/health.js": (STATIC / "health.js", "text/javascript"),
                 "/theme.css": (THEME / "css/devx-theme.css", "text/css"),
                 "/jupyter-link.js": (THEME / "js/jupyter-link.js", "text/javascript"),
                 "/fonts/NVIDIASans_Rg.ttf": (THEME / "css/fonts/NVIDIASans_Rg.ttf", "font/ttf"),
                 "/fonts/JetBrainsMono-Regular.woff2": (THEME / "css/fonts/JetBrainsMono-Regular.woff2", "font/woff2"),
                 "/fonts/JetBrainsMono-Bold.woff2": (THEME / "css/fonts/JetBrainsMono-Bold.woff2", "font/woff2")}
        if path not in files:
            self.send(404, '{"error":"Not found"}')
            return
        file, mime = files[path]
        self.send(200, file.read_bytes(), mime)

    def do_POST(self):
        # Same-origin custom header prevents cross-site forms from spending API calls.
        if self.path != "/api/check" or self.headers.get("X-Workshop-Check") != "1":
            self.send(403, '{"error":"Open Workshop Health to run checks."}')
            return
        if not self.state.check():
            self.send(409, '{"error":"Checks are already running."}')
            return
        self.send(200, json.dumps(self.state.snapshot()))


def main():
    parser = argparse.ArgumentParser(description="Workshop Health dashboard")
    parser.add_argument("--port", type=int, default=8099)
    args = parser.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
