"""Keep the optional sandbox policy migration narrowly scoped."""

import copy
from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[3]
POLICY = runpy.run_path(str(ROOT / ".claude/skills/setup-workshop-nemoclaw-operator/scripts/build-workshop-policy.py"))


class SandboxPolicyTests(unittest.TestCase):
    def setUp(self):
        self.live = {
            "version": 1,
            "filesystem_policy": {"read_only": ["/usr"], "read_write": ["/sandbox"]},
            "network_policies": {
                "custom": {"endpoints": [{"host": "example.com", "port": 443}]},
                "mcp_tavily": {
                    "name": "existing-mcp",
                    "endpoints": [{"host": "mcp.tavily.com", "port": 443,
                                   "rules": [{"allow": {"method": "POST", "path": "/mcp/"}}]}],
                    "binaries": [{"path": "/usr/local/bin/node"}],
                },
            },
        }

    def test_existing_mcp_grant_gains_python_without_replacing_policy(self):
        before = copy.deepcopy(self.live)
        result = POLICY["compose"](self.live)
        original = self.live["network_policies"]["mcp_tavily"]
        migrated = result["network_policies"]["mcp_tavily"]
        self.assertEqual(self.live, before)
        self.assertEqual(migrated["endpoints"], original["endpoints"])
        self.assertEqual(migrated["name"], original["name"])
        self.assertEqual(migrated["binaries"], original["binaries"] + POLICY["PY_BINARIES"])
        self.assertEqual(result["network_policies"]["custom"], before["network_policies"]["custom"])
        self.assertEqual(POLICY["verify"](self.live, result), [])
        self.assertEqual(POLICY["compose"](result), result)

    def test_new_mcp_grant_uses_python(self):
        del self.live["network_policies"]["mcp_tavily"]
        result = POLICY["compose"](self.live)
        block = result["network_policies"]["mcp_tavily"]
        self.assertEqual(block["binaries"], POLICY["PY_BINARIES"])
        self.assertEqual([entry["host"] for entry in block["endpoints"]], ["mcp.tavily.com"])
        self.assertEqual(POLICY["verify"](self.live, result), [])

    def test_unrelated_permission_changes_fail_verification(self):
        result = POLICY["compose"](self.live)
        result["network_policies"]["mcp_tavily"]["endpoints"][0]["rules"].append(
            {"allow": {"method": "DELETE", "path": "/**"}}
        )
        self.assertTrue(POLICY["verify"](self.live, result))


if __name__ == "__main__":
    unittest.main()
