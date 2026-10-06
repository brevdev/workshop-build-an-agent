"""Launch the workshop's pinned Nano NIM without exposing a key in shell arguments."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

# NIM 2.0.13 / vLLM 0.28.0. Pin the multi-architecture manifest, not `latest`.
# Its built-in parsers were checked against the Nano model's chat template.
NIM_IMAGE = (
    "nvcr.io/nim/nvidia/nemotron-3-nano@"
    "sha256:31e60afd3f0e03a18dd8443ab0fe2d124c8ba053cbf42aa112237c7c345d1408"
)
CONTAINER = "nemotron"
CACHE = "nim-cache"
PROFILE_LABEL = "workshop.nim.profile"
GPU_MEMORY_UTILIZATION = 0.8

# The image targets CUDA 13 (R580+) and ships CUDA forward-compatibility
# libraries. Data-center GPUs can use them with an older driver; this was
# validated on an A100 with R565. Other GPUs need an R580+ driver.
COMPAT_LIBS = "/usr/local/cuda-13.0/compat"
MIN_COMPAT_DRIVER = 535
DATA_CENTER_GPU = re.compile(r"^(A100|A800|A30|A40|A10G?|A16|A2|H100|H200|H800|H20|GH200|L4|L40S?|L20"
                             r"|B100|B200|B300|GB200|GB300|T4|V100)$")

# vllm-nvfp4-tp1: native on Blackwell; older GPUs need Marlin emulation, which
# NIM labels "not validated". It worked for the workshop's tool-calling test.
NVFP4_PROFILE = "1fba9ecfcfb4cde28d4ce3fd55c40bca89a5a613e25e98f057befe6a7e99eada"
IMAGE_GB = 32  # unpacked image size
HEADROOM_GB = 5


def profile_requirements(profile: str, compute_cap: float) -> tuple[str, int, int]:
    """Return (profile description, model download GB, minimum GPU GB) for the run NIM will select."""
    if profile == "nvfp4":
        return "NVFP4 (vllm-nvfp4-tp1)", 19, 21
    if compute_cap >= 8.9:  # FP8-capable GPUs (Ada, Hopper, Blackwell)
        return "FP8 (vllm-fp8-tp1)", 34, 34
    return "BF16 (vllm-bf16-tp1)", 64, 63


def launch_command(compat_library_path: str | None = None, profile: str = "auto",
                   emulate_nvfp4: bool = False) -> list[str]:
    options = []
    if compat_library_path:
        options += ["-e", f"LD_LIBRARY_PATH={compat_library_path}"]
    if profile == "nvfp4":
        options += ["-e", f"NIM_MODEL_PROFILE={NVFP4_PROFILE}"]
        if emulate_nvfp4:
            options += ["-e", "NIM_ALLOW_NVFP4_EMULATION=1"]
    return [
        "docker", "run", "-d", "--name", CONTAINER,
        "--network", "workbench", "--gpus", "1", "--shm-size=16GB",
        "-e", "NGC_API_KEY", *options, "-v", f"{CACHE}:/opt/nim/.cache",
        "-u", str(os.getuid()), "-p", "8000:8000", NIM_IMAGE,
        "--max-model-len", "16384", "--gpu-memory-utilization", str(GPU_MEMORY_UTILIZATION),
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


def image_present() -> bool:
    result = subprocess.run(["docker", "image", "inspect", NIM_IMAGE], capture_output=True, timeout=30)
    return result.returncode == 0


def compat_library_path() -> str:
    """Prepend the compatibility libraries to the image's own library path."""
    try:
        env = json.loads(read_command(["docker", "image", "inspect", NIM_IMAGE, "--format", "{{json .Config.Env}}"]))
    except (RuntimeError, ValueError):
        env = []
    default = next((item.split("=", 1)[1] for item in env if item.startswith("LD_LIBRARY_PATH=")), "")
    return f"{COMPAT_LIBS}:{default}" if default else COMPAT_LIBS


def preflight(profile: str = "auto") -> dict:
    """Check Docker, GPU, driver, memory and disk before any download. Returns the launch plan."""
    read_command(["docker", "info", "--format", "{{.ServerVersion}}"])
    read_command(["docker", "network", "inspect", "workbench", "--format", "{{.Name}}"])
    existing = read_command([
        "docker", "ps", "-a", "--filter", f"name=^/{CONTAINER}$", "--format", "{{.Names}}",
    ])
    if existing:
        raise RuntimeError(
            f"Container {CONTAINER!r} already exists. Inspect it with docker logs {CONTAINER}; "
            "remove it with `python code/2-agentic-rag/nim_setup.py --stop` if it belongs to your previous workshop run."
        )
    gpu_rows = read_command([
        "nvidia-smi", "--query-gpu=driver_version,name,memory.total,memory.free,compute_cap",
        "--format=csv,noheader,nounits",
    ]).splitlines()
    if not gpu_rows:
        raise RuntimeError("No NVIDIA GPU is visible. This optional exercise requires a supported local GPU.")
    # The container uses one GPU: the first one Docker assigns.
    driver, name, total_mib, free_mib, compute_cap = [part.strip() for part in gpu_rows[0].split(",")]
    print(f"GPU (driver, name, total MiB, free MiB, compute capability): {gpu_rows[0]}")
    driver_major = int(driver.split(".", 1)[0])
    data_center = any(DATA_CENTER_GPU.match(token) for token in re.split(r"[\s-]+", name))
    compat = False
    if driver_major < 580:
        if data_center and driver_major >= MIN_COMPAT_DRIVER:
            compat = True
            print(f"Driver {driver} is older than R580; using the image's CUDA forward-compatibility libraries.")
        else:
            raise RuntimeError(
                f"Driver {driver} is below R580 for this pinned CUDA 13 image, and forward compatibility "
                "applies only to data-center GPUs. Use a host with an R580+ driver. This helper does not "
                "change drivers. The hosted agent remains available."
            )
    try:
        cap = float(compute_cap)
    except ValueError:
        cap = 0.0
    emulate = profile == "nvfp4" and cap < 10.0
    label, model_gb, gpu_gb = profile_requirements(profile, cap)
    try:
        total_gb, free_gb = int(total_mib) / 1024, int(free_mib) / 1024
    except ValueError:  # unified-memory systems can report [N/A]
        total_gb = free_gb = None
        print("This GPU does not report its memory. Check that it can give the NIM "
              f"at least {gpu_gb} GB before launching.")
    if total_gb is not None:
        # vLLM loads the model into the share of GPU memory it is allowed to reserve.
        usable_gb = total_gb * GPU_MEMORY_UTILIZATION
        if usable_gb < gpu_gb:
            nvfp4_fits = profile != "nvfp4" and usable_gb >= profile_requirements("nvfp4", cap)[2]
            hint = " Try --profile nvfp4." if nvfp4_fits else " The hosted model works for every exercise."
            raise RuntimeError(
                f"The {label} profile needs at least {gpu_gb} GB of GPU memory; the NIM can use "
                f"{GPU_MEMORY_UTILIZATION:.0%} of this GPU's {total_gb:.0f} GB ({usable_gb:.0f} GB).{hint}"
            )
        if free_gb < usable_gb:
            raise RuntimeError(
                f"Only {free_gb:.0f} GB of GPU memory is free; the NIM reserves {GPU_MEMORY_UTILIZATION:.0%} "
                f"({usable_gb:.0f} GB). Stop other GPU work first, such as training "
                "notebook kernels (Kernel > Shut Down Kernel) or other model containers."
            )
    # The cache volume records which profile it holds; another profile downloads again.
    volume = subprocess.run(["docker", "volume", "inspect", CACHE, "--format", f'{{{{ index .Labels "{PROFILE_LABEL}" }}}}'],
                            capture_output=True, text=True, timeout=30)
    cache_exists = volume.returncode == 0
    cached = cache_exists and volume.stdout.strip() == profile
    have_image = image_present()
    needed_gb = (0 if have_image else IMAGE_GB) + (0 if cached else model_gb) + HEADROOM_GB
    # Images and volumes live on the Docker host. In Workbench this container's
    # root filesystem shares that disk, so its free space is a close estimate.
    free_disk_gb = shutil.disk_usage("/").free / 1e9
    note = (" (this profile's download is already in the model cache)" if cached else
            " (the model cache holds a different download; this profile adds its own)" if cache_exists else "")
    print(f"Profile: {label}. Disk: about {needed_gb} GB needed, {free_disk_gb:.0f} GB free{note}.")
    if free_disk_gb < needed_gb:
        hint = " The --profile nvfp4 option needs less." if profile != "nvfp4" and model_gb > 19 else ""
        raise RuntimeError(
            f"Not enough disk space: about {needed_gb} GB is needed and {free_disk_gb:.0f} GB is free. "
            f"Free space first (for example, remove the Module 4 merged model in "
            f"code/4-agent-customization/outputs/, or run --teardown to clear an old model cache).{hint}"
        )
    if emulate:
        print("NVFP4 runs in emulation on this GPU. NIM has not validated this combination; "
              "the workshop's smoke test checks that tool calling works.")
    return {"compat": compat, "profile": profile, "emulate_nvfp4": emulate, "image_present": have_image,
            "cache_exists": cache_exists}


def remove(teardown: bool) -> int:
    """Stop the container; with teardown, also delete the image and model cache."""
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)
    print(f"Container {CONTAINER!r} stopped and removed (if it existed). GPU memory is released.")
    if teardown:
        image = subprocess.run(["docker", "rmi", NIM_IMAGE], capture_output=True, text=True)
        print("Image removed." if image.returncode == 0 else "Image was not present.")
        volume = subprocess.run(["docker", "volume", "rm", CACHE], capture_output=True, text=True)
        print(f"Model cache volume {CACHE!r} removed." if volume.returncode == 0 else f"No {CACHE!r} volume to remove.")
    else:
        print(f"The image and the {CACHE!r} volume are kept for a faster restart. "
              "Use --teardown to delete them and free their disk space.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check Docker, GPU, driver, disk and saved-key presence only")
    mode.add_argument("--print-command", action="store_true", help="show the pinned command without loading keys or starting Docker")
    mode.add_argument("--stop", action="store_true", help="stop and remove the container; keep the image and model cache")
    mode.add_argument("--teardown", action="store_true", help="remove the container, image and model cache")
    parser.add_argument("--profile", choices=("auto", "nvfp4"), default="auto",
                        help="auto: let NIM pick (BF16 on A100: ~64 GB download); nvfp4: smaller ~19 GB download")
    args = parser.parse_args()
    if args.stop or args.teardown:
        return remove(args.teardown)
    if args.print_command:
        print(shlex.join(launch_command(profile=args.profile)))
        print("Preflight adds forward-compatibility settings when this host's driver needs them.")
        return 0
    try:
        plan = preflight(args.profile)
        key = saved_key()
        if args.check:
            print("Preflight passed; saved key is present. No image was pulled or container started.")
            return 0
        # stdin and an inherited environment avoid putting the key in argv or shell history.
        env = {**os.environ, "NGC_API_KEY": key}
        if not plan["image_present"]:
            # A temporary Docker config keeps the registry login out of ~/.docker.
            with tempfile.TemporaryDirectory(prefix="nim-docker-") as config_dir:
                login_env = {**env, "DOCKER_CONFIG": config_dir}
                subprocess.run(
                    ["docker", "login", "nvcr.io", "--username", "$oauthtoken", "--password-stdin"],
                    input=key + "\n", text=True, check=True, env=login_env, stdout=subprocess.DEVNULL,
                )
                print("Pulling the pinned NIM image (about 32 GB unpacked; this can take several minutes)...")
                subprocess.run(["docker", "pull", NIM_IMAGE], check=True, env=login_env)
        if not plan["cache_exists"]:
            subprocess.run(["docker", "volume", "create", "--label", f"{PROFILE_LABEL}={plan['profile']}", CACHE],
                           check=True, stdout=subprocess.DEVNULL)
        command = launch_command(compat_library_path() if plan["compat"] else None,
                                 plan["profile"], plan["emulate_nvfp4"])
        subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"NIM setup stopped: {exc}", file=sys.stderr)
        return 1
    print(f"Container started. Follow loading with: docker logs -f {CONTAINER}")
    print("Then run: python code/2-agentic-rag/nim_smoke_test.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
