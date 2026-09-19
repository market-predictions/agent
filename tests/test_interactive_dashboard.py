from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import interactive_dashboard as dashboard


TEST_PROVIDER_SECRETS = frozenset({"OPENAI_API_KEY", "ANTHROPIC_API_KEY"})


class InteractiveDashboardContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = {
            "FREELLMAPI_API_KEY": "freellmapi-test-key",
            "MODAL_PROXY_KEY": "proxy-id",
            "MODAL_PROXY_SECRET": "proxy-secret",
            "HERMES_DASHBOARD_OAUTH_CLIENT_ID": "agent:test-instance",
        }

    def test_repository_managed_policy_is_exact_and_safe(self) -> None:
        policy = dashboard.validate_managed_policy(dashboard.load_managed_policy())
        self.assertEqual(policy["model"], {"default": "auto", "provider": "freellmapi"})
        self.assertEqual(set(policy["providers"]), {"freellmapi"})
        self.assertEqual(
            policy["platform_toolsets"]["cli"],
            ["web", "memory", "session_search"],
        )
        self.assertEqual(policy["approvals"]["mode"], "manual")
        self.assertNotIn("terminal", policy["platform_toolsets"]["cli"])
        self.assertNotIn("delegation", policy["platform_toolsets"]["cli"])

    def test_policy_drift_fails_closed(self) -> None:
        policy = dashboard.load_managed_policy()
        unsafe = copy.deepcopy(policy)
        unsafe["platform_toolsets"]["cli"].append("terminal")
        with self.assertRaises(dashboard.DashboardConfigError):
            dashboard.validate_managed_policy(unsafe)

        bypass = copy.deepcopy(policy)
        bypass["model"]["provider"] = "openai"
        with self.assertRaises(dashboard.DashboardConfigError):
            dashboard.validate_managed_policy(bypass)

    def test_environment_binds_only_to_protected_gateway_and_disables_bang_shell(self) -> None:
        env = dashboard.build_dashboard_environment(
            "https://gateway.example",
            self.env,
            direct_provider_secret_names=TEST_PROVIDER_SECRETS,
        )
        self.assertEqual(env["FREELLMAPI_BASE_URL"], "https://gateway.example/v1")
        self.assertEqual(env["HERMES_HOME"], "/root/.hermes")
        self.assertEqual(env["HERMES_MANAGED_DIR"], "/etc/hermes")
        self.assertEqual(env["HERMES_GATEWAY_SESSION"], "1")
        self.assertNotIn("OPENAI_API_KEY", env)

    def test_upstream_provider_secret_is_rejected(self) -> None:
        env = dict(self.env, OPENAI_API_KEY="must-not-enter-hermes")
        with self.assertRaises(dashboard.DashboardConfigError):
            dashboard.build_dashboard_environment(
                "https://gateway.example",
                env,
                direct_provider_secret_names=TEST_PROVIDER_SECRETS,
            )

    def test_missing_or_malformed_oauth_client_is_rejected(self) -> None:
        for value in ("", "dashboard-client", "agent:"):
            env = dict(self.env, HERMES_DASHBOARD_OAUTH_CLIENT_ID=value)
            with self.assertRaises(dashboard.DashboardConfigError):
                dashboard.build_dashboard_environment(
                    "https://gateway.example",
                    env,
                    direct_provider_secret_names=TEST_PROVIDER_SECRETS,
                )

    def test_missing_gateway_secret_is_rejected(self) -> None:
        for key in ("FREELLMAPI_API_KEY", "MODAL_PROXY_KEY", "MODAL_PROXY_SECRET"):
            env = dict(self.env)
            env.pop(key)
            with self.assertRaises(dashboard.DashboardConfigError):
                dashboard.build_dashboard_environment(
                    "https://gateway.example",
                    env,
                    direct_provider_secret_names=TEST_PROVIDER_SECRETS,
                )

    def test_managed_env_is_generated_from_provider_catalog_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            dashboard.materialize_managed_env_policy(TEST_PROVIDER_SECRETS, path)
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "ANTHROPIC_API_KEY=\nOPENAI_API_KEY=\n",
            )

    def test_host_route_policy_removes_only_authority_mutations_and_console(self) -> None:
        def route(path: str, methods=None):
            return SimpleNamespace(path=path, methods=methods)

        app = SimpleNamespace(
            router=SimpleNamespace(
                routes=[
                    route("/api/config", {"GET"}),
                    route("/api/config", {"PUT"}),
                    route("/api/env/reveal", {"POST"}),
                    route("/api/providers/oauth/{provider_id}/start", {"POST"}),
                    route("/api/mcp/servers", {"DELETE"}),
                    route("/api/cron/jobs", {"POST"}),
                    route("/api/console"),
                    route("/api/sessions", {"POST"}),
                ]
            )
        )
        removed = dashboard.install_host_route_policy(app)
        self.assertIn(("PUT", "/api/config"), removed)
        self.assertIn(("POST", "/api/env/reveal"), removed)
        self.assertIn(("POST", "/api/providers/oauth/{provider_id}/start"), removed)
        self.assertIn(("DELETE", "/api/mcp/servers"), removed)
        self.assertIn(("POST", "/api/cron/jobs"), removed)
        self.assertIn(("WS", "/api/console"), removed)
        kept = {(tuple(sorted(r.methods or ())), r.path) for r in app.router.routes}
        self.assertIn((("GET",), "/api/config"), kept)
        self.assertIn((("POST",), "/api/sessions"), kept)

    def test_native_dashboard_wrapper_uses_python_module_entrypoint(self) -> None:
        self.assertEqual(
            dashboard.dashboard_command(),
            [sys.executable, "-m", "interactive_dashboard"],
        )


if __name__ == "__main__":
    unittest.main()
