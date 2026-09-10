import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import runtime_versions


class RuntimeContractTests(unittest.TestCase):
    def test_runtime_versions_are_exact_pins(self):
        self.assertEqual(runtime_versions.MODAL_VERSION, "1.5.5")
        self.assertEqual(runtime_versions.HERMES_VERSION, "0.21.1")
        self.assertRegex(runtime_versions.HERMES_COMMIT, r"^[0-9a-f]{40}$")
        self.assertEqual(
            runtime_versions.HERMES_REPOSITORY,
            "https://github.com/NousResearch/hermes-agent.git",
        )
        self.assertEqual(runtime_versions.HERMES_SOURCE_DIR, "/opt/hermes-agent")
        self.assertEqual(runtime_versions.FREELLMAPI_VERSION, "0.9.8")
        self.assertRegex(
            runtime_versions.FREELLMAPI_IMAGE,
            r"^ghcr\.io/tashfeenahmed/freellmapi@sha256:[0-9a-f]{64}$",
        )
        self.assertRegex(
            runtime_versions.HERMES_DASHBOARD_NODE_IMAGE,
            r"^node:26-bookworm-slim@sha256:[0-9a-f]{64}$",
        )
        self.assertEqual(runtime_versions.HERMES_DASHBOARD_PORT, 9119)

    def test_bounded_worker_stays_small_protected_and_single_input(self):
        source = (ROOT / "modal_app.py").read_text(encoding="utf-8")
        self.assertIn("requires_proxy_auth=True", source)
        self.assertIn("@modal.concurrent(max_inputs=1)", source)
        self.assertIn("HERMES_COMMIT", source)
        self.assertIn("pip install --disable-pip-version-check -e", source)
        self.assertIn("FREELLMAPI_IMAGE", source)
        self.assertIn("agent-freellmapi-default.json", source)
        self.assertIn('"agent_carrier", "agent_budget_plugin", "runtime_versions"', source)
        self.assertNotIn("modal.Sandbox", source)
        self.assertNotIn("Pydantic", source)

        worker_start = source.index("def run_agent")
        worker_decorator = source.rfind("@app.function", 0, worker_start)
        dashboard_decorator = source.index("@app.function", worker_start)
        worker_section = source[worker_decorator:dashboard_decorator]
        self.assertIn("secrets=[freellmapi_client_secret]", worker_section)
        self.assertNotIn("hermes_dashboard_auth_secret", worker_section)
        self.assertNotIn("volumes=", worker_section)

    def test_interactive_dashboard_uses_native_hermes_and_one_persistent_volume(self):
        source = (ROOT / "modal_app.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("modal.Volume.from_name("), 1)
        self.assertIn("MODAL_HERMES_DASHBOARD_VOLUME", source)
        self.assertIn("HERMES_DASHBOARD_NODE_IMAGE", source)
        self.assertIn("npm run build", source)
        self.assertIn('"hermes",\n            "dashboard"', source)
        self.assertIn("hermes_dashboard_auth_secret", source)
        self.assertIn('required_keys=["HERMES_DASHBOARD_OAUTH_CLIENT_ID"]', source)
        self.assertIn("max_containers=1", source)
        self.assertIn("_start_volume_committer()", source)

    def test_managed_dashboard_policy_preserves_authority_boundaries(self):
        policy = (ROOT / "runtime/hermes-managed-dashboard.yaml").read_text(encoding="utf-8")
        self.assertIn('provider: "freellmapi"', policy)
        self.assertIn('base_url: "${FREELLMAPI_BASE_URL}"', policy)
        self.assertIn('key_env: "FREELLMAPI_API_KEY"', policy)
        self.assertIn("fallback_providers: []", policy)
        self.assertIn("toolsets:\n  - web", policy)
        self.assertIn("max_concurrent_sessions: 1", policy)
        self.assertNotIn("terminal", policy)
        self.assertNotIn("delegation", policy)
        self.assertNotIn("browser", policy)


if __name__ == "__main__":
    unittest.main()
