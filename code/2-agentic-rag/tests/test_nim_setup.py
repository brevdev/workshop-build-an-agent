"""Protect the deployment's prerequisite and credential boundaries."""

from collections import namedtuple
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nim_setup

Usage = namedtuple("Usage", "total used free")
A100 = "565.57.01, NVIDIA A100 80GB PCIe, 81920, 81000, 8.0"


class Completed:
    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


def run_preflight(gpu_row, *, free_disk_gb=200, image=False, cache=None, existing="", profile="auto"):
    """Run preflight with Docker, nvidia-smi and disk answers supplied by the test.

    `cache` is the profile label of an existing nim-cache volume ("" for an unlabeled one).
    """
    reads = ["28.0.0", "workbench", existing, gpu_row]

    def run(command, **kwargs):
        if command[:3] == ["docker", "volume", "inspect"]:
            return Completed(1) if cache is None else Completed(0, cache + "\n")
        if command[:3] == ["docker", "image", "inspect"]:
            return Completed(0 if image else 1)
        raise AssertionError(f"unexpected command: {command}")

    with patch.object(nim_setup, "read_command", side_effect=reads) as read, \
         patch.object(nim_setup.subprocess, "run", side_effect=run), \
         patch.object(nim_setup.shutil, "disk_usage", return_value=Usage(0, 0, free_disk_gb * 1e9)):
        plan = nim_setup.preflight(profile)
    return plan, read


class SetupTests(unittest.TestCase):
    def test_unsupported_driver_stops_before_any_download(self):
        with self.assertRaisesRegex(RuntimeError, "below R580"):
            run_preflight("565.57.01, NVIDIA GeForce RTX 4090, 24564, 24000, 8.9")

    def test_old_driver_on_data_center_gpu_uses_forward_compatibility(self):
        plan, _ = run_preflight(A100)
        self.assertTrue(plan["compat"])
        command = nim_setup.launch_command("/usr/local/cuda-13.0/compat:/usr/lib", plan["profile"])
        self.assertIn("LD_LIBRARY_PATH=/usr/local/cuda-13.0/compat:/usr/lib", command)

    def test_current_driver_needs_no_compatibility_libraries(self):
        plan, _ = run_preflight("580.159.03, NVIDIA A100 80GB PCIe, 81920, 81000, 8.0")
        self.assertFalse(plan["compat"])
        self.assertFalse(any(arg.startswith("LD_LIBRARY_PATH") for arg in nim_setup.launch_command()))

    def test_existing_container_is_preserved(self):
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            run_preflight(A100, existing="nemotron")

    def test_low_disk_stops_before_download_and_suggests_smaller_profile(self):
        # Image (32) + BF16 model (64) + headroom (5) does not fit in 78 GB.
        with self.assertRaisesRegex(RuntimeError, "Not enough disk space.*--profile nvfp4"):
            run_preflight(A100, free_disk_gb=78)
        plan, _ = run_preflight(A100, free_disk_gb=78, profile="nvfp4")
        self.assertTrue(plan["emulate_nvfp4"])

    def test_cached_image_and_model_need_only_headroom(self):
        plan, _ = run_preflight(A100, free_disk_gb=10, image=True, cache="auto")
        self.assertTrue(plan["image_present"] and plan["cache_exists"])

    def test_a_cache_of_another_profile_still_needs_the_download(self):
        with self.assertRaisesRegex(RuntimeError, "Not enough disk space"):
            run_preflight(A100, free_disk_gb=40, image=True, cache="nvfp4")
        with self.assertRaisesRegex(RuntimeError, "Not enough disk space"):
            run_preflight(A100, free_disk_gb=40, image=True, cache="")  # unlabeled, from an older helper

    def test_existing_container_is_reported_before_gpu_checks(self):
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            run_preflight("565.57.01, NVIDIA A100 80GB PCIe, 81920, 1000, 8.0", existing="nemotron")

    def test_gpu_without_memory_reporting_does_not_crash(self):
        plan, _ = run_preflight("580.95, NVIDIA GB10, [N/A], [N/A], 12.1", profile="nvfp4")
        self.assertFalse(plan["emulate_nvfp4"])

    def test_busy_gpu_stops_with_guidance(self):
        with self.assertRaisesRegex(RuntimeError, "Stop other GPU work"):
            run_preflight("565.57.01, NVIDIA A100 80GB PCIe, 81920, 20000, 8.0")

    def test_gpu_memory_check_uses_the_share_vllm_reserves(self):
        # 32 GB x 80% = 25.6 GB: too small for BF16, enough for NVFP4.
        with self.assertRaisesRegex(RuntimeError, "at least 63 GB.*--profile nvfp4"):
            run_preflight("580.1, NVIDIA V100-SXM2-32GB, 32768, 32000, 7.0")
        # 24 GB x 80% = 19 GB: too small even for NVFP4, so do not suggest it.
        with self.assertRaisesRegex(RuntimeError, "hosted model works") as error:
            run_preflight("580.1, NVIDIA A10G, 23028, 23000, 8.6")
        self.assertNotIn("nvfp4", str(error.exception))
        with self.assertRaisesRegex(RuntimeError, "at least 21 GB"):
            run_preflight("580.1, NVIDIA A10G, 23028, 23000, 8.6", profile="nvfp4")

    def test_nvfp4_profile_is_pinned_and_emulated_only_before_blackwell(self):
        command = nim_setup.launch_command(profile="nvfp4", emulate_nvfp4=True)
        self.assertIn(f"NIM_MODEL_PROFILE={nim_setup.NVFP4_PROFILE}", command)
        self.assertIn("NIM_ALLOW_NVFP4_EMULATION=1", command)
        plan, _ = run_preflight("580.1, NVIDIA B200, 183359, 183000, 10.0", profile="nvfp4")
        self.assertFalse(plan["emulate_nvfp4"])

    def test_key_is_passed_via_stdin_and_a_temporary_docker_config(self):
        key = "test-only-secret-not-a-real-credential"
        plan = {"compat": False, "profile": "auto", "emulate_nvfp4": False, "image_present": False,
                "cache_exists": False}
        with patch.object(sys, "argv", ["nim_setup.py"]), \
             patch.object(nim_setup, "preflight", return_value=plan), \
             patch.object(nim_setup, "saved_key", return_value=key), \
             patch.object(nim_setup.subprocess, "run") as run:
            self.assertEqual(nim_setup.main(), 0)
        login, pull, volume, launch = run.call_args_list
        self.assertEqual(login.kwargs["input"], key + "\n")
        config = login.kwargs["env"]["DOCKER_CONFIG"]
        self.assertNotEqual(config, str(Path.home() / ".docker"))
        self.assertEqual(pull.kwargs["env"]["DOCKER_CONFIG"], config)
        self.assertFalse(Path(config).exists(), "the temporary login config must be deleted")
        self.assertEqual(launch.kwargs["env"]["NGC_API_KEY"], key)
        self.assertIn("workshop.nim.profile=auto", volume.args[0])
        for call in run.call_args_list:
            self.assertNotIn(key, " ".join(call.args[0]))

    def test_present_image_skips_login_and_pull(self):
        plan = {"compat": False, "profile": "auto", "emulate_nvfp4": False, "image_present": True,
                "cache_exists": True}
        with patch.object(sys, "argv", ["nim_setup.py"]), \
             patch.object(nim_setup, "preflight", return_value=plan), \
             patch.object(nim_setup, "saved_key", return_value="test-only"), \
             patch.object(nim_setup.subprocess, "run") as run:
            self.assertEqual(nim_setup.main(), 0)
        self.assertEqual([call.args[0][:3] for call in run.call_args_list], [["docker", "run", "-d"]])

    def test_check_mode_never_authenticates_or_starts_a_container(self):
        with patch.object(sys, "argv", ["nim_setup.py", "--check"]), \
             patch.object(nim_setup, "preflight", return_value={}), \
             patch.object(nim_setup, "saved_key", return_value="test-only"), \
             patch.object(nim_setup.subprocess, "run") as run:
            self.assertEqual(nim_setup.main(), 0)
        run.assert_not_called()

    def test_stop_keeps_downloads_and_teardown_removes_them(self):
        for flag, expected in (("--stop", [["docker", "rm", "-f"]]),
                               ("--teardown", [["docker", "rm", "-f"], ["docker", "rmi", nim_setup.NIM_IMAGE],
                                               ["docker", "volume", "rm"]])):
            with patch.object(sys, "argv", ["nim_setup.py", flag]), \
                 patch.object(nim_setup.subprocess, "run", return_value=Completed()) as run:
                self.assertEqual(nim_setup.main(), 0)
            self.assertEqual([call.args[0][:len(prefix)] for call, prefix in zip(run.call_args_list, expected)],
                             expected)
            self.assertEqual(len(run.call_args_list), len(expected))


if __name__ == "__main__":
    unittest.main()
