import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dotenv import dotenv_values
from workshop_support import get_model, load_secrets
from workshop_support.secrets import save_secrets
from workshop_support.health import check_endpoint, environment_checks, HealthState, local_service


class SharedSetupTests(unittest.TestCase):
    def test_saved_keys_override_stale_parent_environment(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / "secrets.env"
            for saved in ("updated-key", ""):
                path.write_text(f"NVIDIA_API_KEY='{saved}'\n")
                os.environ["NVIDIA_API_KEY"] = "stale-parent-key"
                load_secrets(folder)
                self.assertEqual(os.environ["NVIDIA_API_KEY"], saved)
            path.write_text("# No saved key\n")
            os.environ["NVIDIA_API_KEY"] = "exported-key"
            load_secrets(folder)
            self.assertEqual(os.environ["NVIDIA_API_KEY"], "exported-key")

    def test_edit_and_clear_keys_preserves_unmanaged_settings(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / "secrets.env"
            path.write_text("# Keep this comment\nCUSTOM_MODEL='unchanged'\nNVIDIA_API_KEY='old'\nTAVILY_API_KEY='search'\n")
            save_secrets({"NVIDIA_API_KEY": "new'quoted-key"}, path)
            values = dotenv_values(path)
            self.assertEqual(values["CUSTOM_MODEL"], "unchanged")
            self.assertEqual(values["TAVILY_API_KEY"], "search")
            self.assertEqual(values["NGC_API_KEY"], "new'quoted-key")
            self.assertIn("# Keep this comment", path.read_text())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            save_secrets({"NVIDIA_API_KEY": "", "TAVILY_API_KEY": ""}, path)
            self.assertEqual(dotenv_values(path)["NVIDIA_API_KEY"], "")
            self.assertNotIn("NVIDIA_API_KEY", os.environ)
            self.assertNotIn("NGC_API_KEY", os.environ)
            self.assertEqual(dotenv_values(path)["CUSTOM_MODEL"], "unchanged")

    def test_missing_key_does_not_call_provider(self):
        with patch("workshop_support.health.request_json") as request:
            result = check_endpoint("chat", "")
        request.assert_not_called()
        self.assertEqual(result["status"], "missing")

    def test_old_sdk_is_flagged_before_model_checks(self):
        with patch("workshop_support.health.metadata.version", return_value="1.2.1"), \
             patch("workshop_support.health.subprocess.run", side_effect=OSError):
            packages = environment_checks()[1]
        self.assertEqual(packages["status"], "fail")
        self.assertIn("langchain-nvidia-ai-endpoints 1.2.1", packages["detail"])
        self.assertIn("1.4.3", packages["detail"])

    def test_http_success_without_capability_is_not_pass(self):
        with patch("workshop_support.health.request_json", return_value={"choices": [{"message": {"content": "Hello"}}]}):
            self.assertEqual(check_endpoint("chat", "private-test-key")["status"], "fail")
        with patch("workshop_support.health.request_json", return_value={"data": [{"embedding": []}]}):
            self.assertEqual(check_endpoint("embedding", "private-test-key")["status"], "fail")
        with patch("workshop_support.health.request_json", return_value={"choices": [{"message": {"content": "Score: 5"}}]}):
            self.assertEqual(check_endpoint("judge", "private-test-key")["status"], "fail")
        with patch("workshop_support.health.request_json", return_value={"choices": [{"message": {"content": '{"score": 5, "explanation": " "}'}}]}):
            self.assertEqual(check_endpoint("judge", "private-test-key")["status"], "fail")

    def test_provider_error_does_not_expose_credentials_or_payload(self):
        error = urllib.error.HTTPError("https://provider.invalid", 410, "PRIVATE-PAYLOAD", {}, None)
        with patch("workshop_support.health.request_json", side_effect=error):
            result = check_endpoint("chat", "private-test-key")
        self.assertEqual(result["status"], "fail")
        self.assertIn("retired", result["detail"])
        self.assertNotIn("private-test-key", json.dumps(result))
        self.assertNotIn("PRIVATE-PAYLOAD", json.dumps(result))

    def test_service_not_started_is_not_failed(self):
        with patch("workshop_support.health.request_json", side_effect=OSError()), \
             patch("workshop_support.health.shutil.which", return_value=None), \
             patch("workshop_support.health.environment_checks", return_value=[]), \
             patch("workshop_support.health.credentials", return_value={"NVIDIA_API_KEY": "fake", "TAVILY_API_KEY": "fake", "LANGSMITH_API_KEY": ""}):
            snapshot = HealthState().snapshot()
        self.assertTrue(all(service["status"] == "idle" for service in snapshot["services"]))
        self.assertTrue(all(endpoint["status"] == "unknown" for endpoint in snapshot["endpoints"]))
        self.assertNotIn('"fake"', json.dumps(snapshot))

    def test_sdk_provider_failure_stays_a_private_endpoint_failure(self):
        with patch("langchain_nvidia_ai_endpoints.NVIDIARerank", side_effect=Exception("[503] PRIVATE-PAYLOAD key=private-test-key")):
            result = check_endpoint("reranking", "private-test-key")
        self.assertEqual(result["status"], "fail")
        self.assertNotIn("PRIVATE-PAYLOAD", json.dumps(result))
        self.assertNotIn("private-test-key", json.dumps(result))

    def test_wrong_service_response_is_not_reported_as_stopped(self):
        with patch("workshop_support.health.request_json", return_value=[]):
            result = local_service("RAG", 2024, "/ok", lambda value: value.get("ok") is True, [2])
        self.assertEqual(result["status"], "fail")

    def test_roles_sharing_a_model_do_not_send_concurrent_requests(self):
        active, overlap = set(), []
        lock = threading.Lock()

        def endpoint(role, key):
            model = get_model(role)
            with lock:
                if model in active:
                    overlap.append(model)
                active.add(model)
            time.sleep(0.03)
            with lock:
                active.discard(model)
            return {"role": role, "status": "pass"}

        with patch("workshop_support.health.credentials", return_value={"NVIDIA_API_KEY": "fake", "TAVILY_API_KEY": "", "LANGSMITH_API_KEY": ""}), \
             patch("workshop_support.health.check_endpoint", side_effect=endpoint), \
             patch("workshop_support.health.check_search", return_value={"status": "missing"}):
            state = HealthState()
            self.assertTrue(state.check())
        self.assertEqual(overlap, [])
        self.assertEqual({r["role"] for r in state.endpoints}, {"chat", "fast_chat", "judge", "embedding", "reranking"})


if __name__ == "__main__":
    unittest.main()
