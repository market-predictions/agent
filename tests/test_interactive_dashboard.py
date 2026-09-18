from __future__ import annotations

import copy
import unittest

import interactive_dashboard as dashboard


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

    def test_managed_env_blocks_all_direct_provider_credentials(self) -> None:
        names = dashboard.load_managed_env_names()
        self.assertEqual(names, set(dashboard.DIRECT_PROVIDER_SECRET_NAMES))
        dashboard.validate_managed_env_policy(names)

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

        incomplete_env = set(dashboard.DIRECT_PROVIDER_SECRET_NAMES) - {"OPENAI_API_KEY"}
        with self.assertRaises(dashboard.DashboardConfigError):
            dashboard.validate_managed_env_policy(incomplete_env)

    def test_environment_binds_only_to_protected_gateway(self) -> None:
        env = dashboard.build_dashboard_environment("https://gateway.example", self.env)
        self.assertEqual(env["FREELLMAPI_BASE_URL"], "https://gateway.example/v1")
        self.assertEqual(env["HERMES_HOME"], "/root/.hermes")
        self.assertEqual(env["HERMES_MANAGED_DIR"], "/etc/hermes")
        self.assertNotIn("OPENAI_API_KEY", env)

    def test_upstream_provider_secret_is_rejected(self) -> None:
        env = dict(self.env, OPENAI_API_KEY="must-not-enter-hermes")
        with self.assertRaises(dashboard.DashboardConfigError):
            dashboard.build_dashboard_environment("https://gateway.example", env)

    def test_missing_or_malformed_oauth_client_is_rejected(self) -> None:
        for value in ("", "dashboard-client", "agent:"):
            env = dict(self.env, HERMES_DASHBOARD_OAUTH_CLIENT_ID=value)
            with self.assertRaises(dashboard.DashboardConfigError):
                dashboard.build_dashboard_environment("https://gateway.example", env)

    def test_missing_gateway_secret_is_rejected(self) -> None:
        for key in ("FREELLMAPI_API_KEY", "MODAL_PROXY_KEY", "MODAL_PROXY_SECRET"):
            env = dict(self.env)
            env.pop(key)
            with self.assertRaises(dashboard.DashboardConfigError):
                dashboard.build_dashboard_environment("https://gateway.example", env)

    def test_native_dashboard_command_has_public_bind_and_no_custom_server(self) -> None:
        self.assertEqual(
            dashboard.dashboard_command(),
            ["hermes", "dashboard", "--host", "0.0.0.0", "--port", "9119", "--no-open"],
        )


if __name__ == "__main__":
    unittest.main()
