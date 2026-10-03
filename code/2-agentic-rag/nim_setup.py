"""Launch the workshop's pinned Nano NIM without exposing a key in shell arguments."""

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys

# NIM 2.0.13 / vLLM 0.28.0. Pin the multi-architecture manifest, not `latest`.
# Its built-in parsers were checked against the Nano model's chat template.
NIM_IMAGE = (
    "nvcr.io/nim/nvidia/nemotron-3-nano@"
    "sha256:31e60afd3f0e03a18dd8443ab0fe2d124c8ba053cbf42aa112237c7c345d1408"
)
CONTAINER = "nemotron"
CACHE = "nim-cache"


def launch_command() -> list[str]:
    return [
        "docker", "run", "-d", "--name", CONTAINER,
        "--network", "workbench", "--gpus", "1", "--shm-size=16GB",
        "-e", "NGC_API_KEY", "-v", f"{CACHE}:/opt/nim/.cache",
        "-u", str(os.getuid()), "-p", "8000:8000", NIM_IMAGE,
        "--max-model-len", "16384", "--gpu-memory-utilization", "0.8",
        "--max-num-seqs", "4", "--enable-auto-tool-choice",
        "--tool-call-parser", "qwen3_coder", "--reasoning-parser", "nemotron_v3",
    ]


def saved_key() -> str:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from workshop_support import load_secrets

    load_secrets()
    key = (os.environ.get("NGC_API_KEY") or os.environ.get("NVIDIA_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("Save your NVIDIA key in Workshop Secrets Manager, then rerun this command.")
    return key


def read_command(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {shlex.join(command)}")
    return result.stdout.strip()


def preflight() -> None:
    read_command(["docker", "info", "--format", "{{.ServerVersion}}"])
    read_command(["docker", "network", "inspect", "workbench", "--format", "{{.Name}}"])
    gpu_rows = read_command([
        "nvidia-smi", "--query-gpu=driver_version,name,memory.total,memory.free",
        "--format=csv,noheader,nounits",
    ]).splitlines()
    if not gpu_rows:
        raise RuntimeError("No NVIDIA GPU is visible. This optional exercise requires a supported local GPU.")
    for row in gpu_rows:
        driver = row.split(",", 1)[0].strip()
        if int(driver.split(".", 1)[0]) < 580:
            raise RuntimeError(
                f"Driver {driver} is below R580 for this pinned CUDA 13 image. "
                "Use a host with a supported driver/profile, or ask the host administrator "
                "to assess NVIDIA's compatibility guidance. This helper does not change drivers. "
                "The hosted agent remains available."
            )
        print(f"GPU (driver, name, total MiB, free MiB): {row}")
    existing = read_command([
        "docker", "ps", "-a", "--filter", f"name=^/{CONTAINER}$", "--format", "{{.Names}}",
    ])
    if existing:
        raise RuntimeError(
            f"Container {CONTAINER!r} already exists. Inspect it with docker logs {CONTAINER}; "
            "stop/remove it only if it belongs to your previous workshop run."
        )
    print("Check the model's Deploy page for your GPU/profile and Docker-host disk capacity before launch.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check Docker, driver and saved-key presence only")
    mode.add_argument("--print-command", action="store_true", help="show the pinned command without loading keys or starting Docker")
    args = parser.parse_args()
    if args.print_command:
        print(shlex.join(launch_command()))
        return 0
    try:
        preflight()
        key = saved_key()
        if args.check:
            print("Preflight passed; saved key is present. No image was pulled or container started.")
            return 0
        # stdin and an inherited environment avoid putting the key in argv or shell history.
        env = {**os.environ, "NGC_API_KEY": key}
        subprocess.run(
            ["docker", "login", "nvcr.io", "--username", "$oauthtoken", "--password-stdin"],
            input=key + "\n", text=True, check=True, env=env,
        )
        subprocess.run(["docker", "volume", "create", CACHE], check=True)
        subprocess.run(launch_command(), check=True, env=env)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"NIM setup stopped: {exc}", file=sys.stderr)
        return 1
    print(f"Container started. Follow loading with: docker logs -f {CONTAINER}")
    print("Then run: python code/2-agentic-rag/nim_smoke_test.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
