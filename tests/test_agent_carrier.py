import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent_carrier


class AgentCarrierTests(unittest.TestCase):
    def test_default_budget_is_single_task_and_bounded(self):
        budget = agent_carrier.Budget()
        budget.validate()
        self.assertEqual(budget.max_concurrent_tasks, 1)
        self.assertEqual(budget.max_turns, 12)
        self.assertEqual(budget.max_wall_seconds, 600)
        self.assertLessEqual(budget.max_turns, budget.max_model_calls)

    def test_invalid_freellmapi_url_is_rejected(self):
        with self.assertRaises(agent_carrier.CarrierConfigError):
            agent_carrier.validate_freellmapi_base_url("not-a-url")

    def test_hermes_config_routes_only_through_freellmapi_and_modal_proxy(self):
        config = agent_carrier.render_hermes_config("https://freellm.example/v1")
        self.assertIn('provider: "custom"', config)
        self.assertIn('model: "auto"', config)
        self.assertIn('api_mode: "chat_completions"', config)
        self.assertIn("https://freellm.example/v1", config)
        self.assertIn("FREELLMAPI_API_KEY", config)
        self.assertIn("${MODAL_PROXY_KEY}", config)
        self.assertIn("${MODAL_PROXY_SECRET}", config)
        self.assertIn("keyless_fallback: true", config)
        self.assertNotIn("OPENAI_API_KEY", config)
        self.assertNotIn("ANTHROPIC_API_KEY", config)
        self.assertNotIn("GEMINI_API_KEY", config)
        self.assertNotIn("sk-", config)

    def test_command_respects_hermes_parser_boundaries_and_is_web_only(self):
        command = agent_carrier.build_hermes_command(
            prompt_file=Path("prompt.txt"),
            usage_file=Path("usage.json"),
            budget=agent_carrier.Budget(),
        )
        chat_index = command.index("chat")
        usage_index = command.index("--usage-file")
        query_index = command.index("--query-file")
        max_turns_index = command.index("--max-turns")
        self.assertEqual(command[0:2], ["hermes", "--ignore-rules"])
        self.assertLess(usage_index, chat_index)
        self.assertGreater(query_index, chat_index)
        self.assertGreater(max_turns_index, chat_index)
        self.assertEqual(command[command.index("--toolsets") + 1], "web")
        self.assertNotIn("terminal", command)
        self.assertNotIn("file", command)
        self.assertNotIn("browser", command)
        self.assertNotIn("delegation", command)

    def test_prompt_requires_public_web_and_structured_result(self):
        prompt = agent_carrier.render_task_prompt(
            "Research a public technical standard.",
            agent_carrier.Budget(),
        )
        self.assertIn("PUBLIC_NON_PERSONAL", prompt)
        self.assertIn("Use the web toolset", prompt)
        self.assertIn("Return ONLY valid JSON", prompt)
        self.assertIn('"source_url"', prompt)

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

    def test_plan_uses_normalized_freellmapi_url(self):
        plan = agent_carrier.build_plan(
            task_id="t-1",
            objective="Research a public technical standard.",
            base_url="  https://freellm.example/v1/  ",
            budget=agent_carrier.Budget(),
        )
        self.assertEqual(plan["freellmapi_base_url"], "https://freellm.example/v1")

    def test_runtime_requires_only_gateway_and_proxy_credentials(self):
        names = (
            agent_carrier.KEY_ENV,
            agent_carrier.PROXY_KEY_ENV,
            agent_carrier.PROXY_SECRET_ENV,
        )
        old = {name: os.environ.pop(name, None) for name in names}
        try:
            with self.assertRaises(agent_carrier.CarrierConfigError):
                agent_carrier._require_runtime_secrets()
            os.environ[agent_carrier.KEY_ENV] = "freellmapi-test"
            os.environ[agent_carrier.PROXY_KEY_ENV] = "wk-test"
            os.environ[agent_carrier.PROXY_SECRET_ENV] = "ws-test"
            agent_carrier._require_runtime_secrets()
        finally:
            for name in names:
                os.environ.pop(name, None)
                if old[name] is not None:
                    os.environ[name] = old[name]

    def test_structured_candidate_is_strict(self):
        value = agent_carrier._parse_candidate_output(
            json.dumps(
                {
                    "summary": "HTTP is an application-layer protocol.",
                    "claims": [
                        {
                            "claim": "HTTP is an application-layer protocol.",
                            "source_url": "https://www.rfc-editor.org/rfc/rfc9110",
                        }
                    ],
                }
            )
        )
        self.assertEqual(len(value["claims"]), 1)
        with self.assertRaises(agent_carrier.CarrierConfigError):
            agent_carrier._parse_candidate_output('{"summary":"x","claims":[],"extra":1}')

    def test_usage_enforces_model_call_budget(self):
        with self.assertRaises(agent_carrier.CarrierConfigError):
            agent_carrier._validate_usage(
                {"api_calls": 13, "completed": True, "failed": False},
                agent_carrier.Budget(max_model_calls=12),
            )
        accepted = agent_carrier._validate_usage(
            {
                "api_calls": 2,
                "completed": True,
                "failed": False,
                "provider": "custom",
                "model": "auto",
            },
            agent_carrier.Budget(),
        )
        self.assertEqual(accepted["api_calls"], 2)


if __name__ == "__main__":
    unittest.main()
