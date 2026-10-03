"""Protect the deployment's prerequisite and credential boundaries."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nim_setup


class SetupTests(unittest.TestCase):
    def test_unsupported_driver_stops_before_any_download(self):
        with patch.object(nim_setup, "read_command", side_effect=[
            "28.0.0", "workbench", "565.57.01, NVIDIA A100 80GB PCIe, 81157, 81156",
        ]) as read:
            with self.assertRaisesRegex(RuntimeError, "below R580"):
                nim_setup.preflight()
        self.assertFalse(any("pull" in call.args[0] or "run" in call.args[0] for call in read.call_args_list))

    def test_existing_container_is_preserved(self):
        with patch.object(nim_setup, "read_command", side_effect=[
            "28.0.0", "workbench", "580.159.03, NVIDIA A100 80GB PCIe, 81157, 81156", "nemotron",
        ]):
            with self.assertRaisesRegex(RuntimeError, "already exists"):
                nim_setup.preflight()

    def test_key_is_passed_via_stdin_and_environment_not_command_arguments(self):
        key = "test-only-secret-not-a-real-credential"
        with patch.object(sys, "argv", ["nim_setup.py"]), \
             patch.object(nim_setup, "preflight"), \
             patch.object(nim_setup, "saved_key", return_value=key), \
             patch.object(nim_setup.subprocess, "run") as run:
            self.assertEqual(nim_setup.main(), 0)
        login, volume, launch = run.call_args_list
        self.assertEqual(login.kwargs["input"], key + "\n")
        self.assertEqual(launch.kwargs["env"]["NGC_API_KEY"], key)
        for call in run.call_args_list:
            self.assertNotIn(key, " ".join(call.args[0]))

    def test_check_mode_never_authenticates_or_starts_a_container(self):
        with patch.object(sys, "argv", ["nim_setup.py", "--check"]), \
             patch.object(nim_setup, "preflight"), \
             patch.object(nim_setup, "saved_key", return_value="test-only"), \
             patch.object(nim_setup.subprocess, "run") as run:
            self.assertEqual(nim_setup.main(), 0)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
