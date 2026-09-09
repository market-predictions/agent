import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent_carrier


class AgentCarrierBootstrapTests(unittest.TestCase):
    def test_default_budget_is_single_task_and_bounded(self):
        budget = agent_carrier.Budget()
        budget.validate()
        self.assertEqual(budget.max_concurrent_tasks, 1)
        self.assertEqual(budget.max_turns, 12)
        self.assertEqual(budget.max_wall_seconds, 600)

    def test_invalid_freellmapi_url_is_rejected(self):
        with self.assertRaises(agent_carrier.CarrierConfigError):
            agent_carrier.validate_freellmapi_base_url("not-a-url")

    def test_hermes_config_uses_only_freellmapi_alias_and_key_env(self):
        config = agent_carrier.render_hermes_config("https://freellm.example/v1")
        self.assertIn("provider: \"custom\"", config)
        self.assertIn("model: \"auto\"", config)
        self.assertIn("https://freellm.example/v1", config)
        self.assertIn("FREELLMAPI_API_KEY", config)
        self.assertNotIn("sk-", config)

    def test_command_is_oneshot_web_only(self):
        command = agent_carrier.build_hermes_command(
            prompt_file=Path("prompt.txt"),
            usage_file=Path("usage.json"),
            budget=agent_carrier.Budget(),
        )
        self.assertEqual(command[0:3], ["hermes", "chat", "--oneshot"])
        self.assertIn("--toolsets", command)
        toolset_index = command.index("--toolsets")
        self.assertEqual(command[toolset_index + 1], "web")
        self.assertNotIn("terminal", command)
        self.assertNotIn("file", command)
        self.assertNotIn("browser", command)
        self.assertNotIn("delegation", command)

    def test_plan_declares_public_non_personal_and_freellmapi(self):
        plan = agent_carrier.build_plan(
            task_id="t-1",
            objective="Research a public technical standard.",
            base_url="https://freellm.example/v1",
            budget=agent_carrier.Budget(),
        )
        self.assertEqual(plan["data_class"], "PUBLIC_NON_PERSONAL")
        self.assertEqual(plan["agent_runtime"], "hermes")
        self.assertEqual(plan["inference_gateway"], "freellmapi")
        self.assertEqual(plan["model"], "auto")
        self.assertEqual(plan["toolsets"], ["web"])

    def test_execute_requires_unified_gateway_key(self):
        old = os.environ.pop(agent_carrier.KEY_ENV, None)
        try:
            with self.assertRaises(agent_carrier.CarrierConfigError):
                agent_carrier.execute_once(
                    task_id="t-1",
                    objective="Research a public technical standard.",
                    base_url="https://freellm.example/v1",
                    budget=agent_carrier.Budget(),
                )
        finally:
            if old is not None:
                os.environ[agent_carrier.KEY_ENV] = old


if __name__ == "__main__":
    unittest.main()
