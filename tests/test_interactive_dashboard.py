from __future__ import annotations

import asyncio
import copy
import os
import tempfile
import unittest
from pathlib import Path

import interactive_dashboard as dashboard
from runtime.hermes_host_policy import (
    HostedDashboardPolicyMiddleware,
    enforce_llm_execution,
    llm_route_allowed,
    mutation_allowed,
)


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
        self.assertEqual(policy["fallback_providers"], [])
        self.assertEqual(policy["fallback_model"], [])
        self.assertEqual(
            policy["platform_toolsets"]["cli"],
            ["web", "memory", "session_search"],
        )
        self.assertEqual(policy["approvals"]["mode"], "manual")
        self.assertEqual(
            policy["plugins"],
            {"enabled": ["agent-host-policy"], "hook_callback_timeout": 5},
        )
        self.assertNotIn("terminal", policy["platform_toolsets"]["cli"])
        self.assertNotIn("delegation", policy["platform_toolsets"]["cli"])

    def test_policy_drift_fails_closed(self) -> None:
        policy = dashboard.load_managed_policy()

        unsafe_tools = copy.deepcopy(policy)
        unsafe_tools["platform_toolsets"]["cli"].append("terminal")
        with self.assertRaises(dashboard.DashboardConfigError):
            dashboard.validate_managed_policy(unsafe_tools)

        bypass = copy.deepcopy(policy)
        bypass["model"]["provider"] = "openai"
        with self.assertRaises(dashboard.DashboardConfigError):
            dashboard.validate_managed_policy(bypass)

        fallback = copy.deepcopy(policy)
        fallback["fallback_providers"] = [{"provider": "openai", "model": "gpt"}]
        with self.assertRaises(dashboard.DashboardConfigError):
            dashboard.validate_managed_policy(fallback)

        plugin_widening = copy.deepcopy(policy)
        plugin_widening["plugins"]["enabled"].append("other-plugin")
        with self.assertRaises(dashboard.DashboardConfigError):
            dashboard.validate_managed_policy(plugin_widening)

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

    def test_browser_mutations_are_default_deny_with_small_native_allowlist(self) -> None:
        for path in ("/api/config", "/api/env", "/api/providers/x", "/api/mcp/x", "/api/cron/x"):
            self.assertFalse(mutation_allowed(path))
        for path in ("/auth/logout", "/api/auth/ws-ticket", "/api/sessions/x", "/api/chat/image-upload"):
            self.assertTrue(mutation_allowed(path))

    def test_asgi_policy_blocks_mutation_console_and_legacy_pty(self) -> None:
        downstream = []
        sent = []

        async def app(scope, receive, send):
            downstream.append((scope["type"], scope.get("path")))

        async def receive():
            return {"type": "http.disconnect"}

        async def send(message):
            sent.append(message)

        middleware = HostedDashboardPolicyMiddleware(app)

        asyncio.run(middleware(
            {"type": "http", "method": "PUT", "path": "/api/config", "query_string": b""},
            receive,
            send,
        ))
        self.assertEqual(sent[0]["status"], 403)
        self.assertEqual(downstream, [])

        sent.clear()
        asyncio.run(middleware(
            {"type": "http", "method": "POST", "path": "/api/sessions/x", "query_string": b""},
            receive,
            send,
        ))
        self.assertEqual(downstream[-1], ("http", "/api/sessions/x"))

        sent.clear()
        asyncio.run(middleware(
            {"type": "websocket", "path": "/api/console", "query_string": b""},
            receive,
            send,
        ))
        self.assertEqual(sent[-1]["type"], "websocket.close")
        self.assertEqual(sent[-1]["code"], 4403)

        sent.clear()
        before = len(downstream)
        asyncio.run(middleware(
            {"type": "websocket", "path": "/api/pty", "query_string": b"ticket=x"},
            receive,
            send,
        ))
        self.assertEqual(sent[-1]["code"], 4403)
        self.assertEqual(len(downstream), before)

        sent.clear()
        asyncio.run(middleware(
            {"type": "websocket", "path": "/api/pty", "query_string": b"attach=tab-1"},
            receive,
            send,
        ))
        self.assertEqual(downstream[-1], ("websocket", "/api/pty"))

    def test_llm_execution_short_circuits_any_non_gateway_route(self) -> None:
        prior = os.environ.get("FREELLMAPI_BASE_URL")
        os.environ["FREELLMAPI_BASE_URL"] = "https://gateway.example/v1"
        calls = []

        def next_call(request):
            calls.append(request)
            return "ok"

        try:
            self.assertTrue(llm_route_allowed(
                provider="freellmapi", model="auto", base_url="https://gateway.example/v1/"
            ))
            self.assertEqual(
                enforce_llm_execution(
                    {"messages": []}, next_call,
                    provider="freellmapi", model="auto", base_url="https://gateway.example/v1",
                ),
                "ok",
            )
            self.assertEqual(len(calls), 1)

            self.assertIsNone(enforce_llm_execution(
                {"messages": []}, next_call,
                provider="openai", model="gpt", base_url="https://api.openai.com/v1",
            ))
            self.assertEqual(len(calls), 1)
        finally:
            if prior is None:
                os.environ.pop("FREELLMAPI_BASE_URL", None)
            else:
                os.environ["FREELLMAPI_BASE_URL"] = prior

    def test_native_dashboard_uses_upstream_cli_bootstrap(self) -> None:
        self.assertEqual(
            dashboard.dashboard_command(),
            ["hermes", "dashboard", "--host", "0.0.0.0", "--port", "9119", "--no-open"],
        )


if __name__ == "__main__":
    unittest.main()
