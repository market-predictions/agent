import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent_budget_plugin


class FakeContext:
    def __init__(self):
        self.hooks = {}
        self.middleware = {}

    def register_hook(self, name, callback):
        self.hooks[name] = callback

    def register_middleware(self, name, callback):
        self.middleware[name] = callback


class BudgetPluginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tmp.name) / "state.json"
        self.names = (
            agent_budget_plugin.STATE_PATH_ENV,
            agent_budget_plugin.MAX_MODEL_CALLS_ENV,
            agent_budget_plugin.MAX_TOOL_CALLS_ENV,
            agent_budget_plugin.MAX_RETRIES_ENV,
        )
        self.old = {name: os.environ.get(name) for name in self.names}
        os.environ[agent_budget_plugin.STATE_PATH_ENV] = str(self.state_path)
        os.environ[agent_budget_plugin.MAX_MODEL_CALLS_ENV] = "5"
        os.environ[agent_budget_plugin.MAX_TOOL_CALLS_ENV] = "2"
        os.environ[agent_budget_plugin.MAX_RETRIES_ENV] = "1"
        self.ctx = FakeContext()
        agent_budget_plugin.register(self.ctx)

    def tearDown(self):
        for name, value in self.old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self.tmp.cleanup()

    def state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def test_registers_native_execution_boundaries_and_ready_state(self):
        self.assertIn("llm_execution", self.ctx.middleware)
        self.assertIn("pre_tool_call", self.ctx.hooks)
        self.assertTrue(self.state()["plugin_ready"])

    def test_total_tool_limit_blocks_before_execution(self):
        pre = self.ctx.hooks["pre_tool_call"]
        self.assertIsNone(pre(tool_name="web_search"))
        self.assertIsNone(pre(tool_name="web_extract"))
        blocked = pre(tool_name="web_search")
        self.assertEqual(blocked["action"], "block")
        state = self.state()
        self.assertEqual(state["tool_calls"], 2)
        self.assertEqual(state["budget_exceeded"], "tool_calls")

    def test_tool_allowlist_fails_closed(self):
        blocked = self.ctx.hooks["pre_tool_call"](tool_name="terminal")
        self.assertEqual(blocked["action"], "block")
        self.assertEqual(self.state()["policy_violation"], "unauthorized_tool:terminal")

    def test_retry_limit_counts_actual_repeated_provider_execution(self):
        llm = self.ctx.middleware["llm_execution"]
        calls = []

        def next_call(request):
            calls.append(request)
            return SimpleNamespace(ok=True)

        kwargs = {
            "request": {"model": "auto"},
            "next_call": next_call,
            "api_request_id": "turn:api:1",
            "api_call_count": 1,
            "provider": "freellmapi",
        }
        self.assertTrue(llm(**kwargs).ok)
        self.assertTrue(llm(**kwargs).ok)
        blocked = llm(**kwargs)
        self.assertEqual(len(calls), 2)
        self.assertIn("agent_budget_exceeded", blocked.choices[0].message.content)
        state = self.state()
        self.assertEqual(state["model_calls"], 2)
        self.assertEqual(state["retries"], 1)
        self.assertEqual(state["budget_exceeded"], "retries")

    def test_real_provider_error_propagates_for_hermes_retry_handling(self):
        llm = self.ctx.middleware["llm_execution"]

        def next_call(request):
            raise RuntimeError("provider unavailable")

        with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
            llm(
                request={"model": "auto"},
                next_call=next_call,
                api_request_id="turn:api:error",
                api_call_count=1,
                provider="freellmapi",
            )
        self.assertEqual(self.state()["model_calls"], 1)
        self.assertIsNone(self.state()["policy_violation"])

    def test_model_call_limit_never_invokes_provider_beyond_cap(self):
        os.environ[agent_budget_plugin.MAX_MODEL_CALLS_ENV] = "2"
        os.environ[agent_budget_plugin.MAX_RETRIES_ENV] = "99"
        agent_budget_plugin.register(self.ctx)
        llm = self.ctx.middleware["llm_execution"]
        calls = []

        def next_call(request):
            calls.append(request)
            return SimpleNamespace(ok=True)

        for i in range(2):
            response = llm(
                request={"i": i},
                next_call=next_call,
                api_request_id=f"turn:api:{i}",
                api_call_count=i,
                provider="freellmapi",
            )
            self.assertTrue(response.ok)
        blocked = llm(
            request={"i": 3},
            next_call=next_call,
            api_request_id="turn:api:3",
            api_call_count=3,
            provider="freellmapi",
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(blocked.model, "agent-budget")
        self.assertEqual(self.state()["budget_exceeded"], "model_calls")

    def test_telemetry_never_persists_raw_tool_or_error_content(self):
        self.ctx.hooks["api_request_error"](
            reason="rate_limit",
            error={"message": "SECRET"},
            request={"authorization": "SECRET"},
        )
        self.ctx.hooks["post_tool_call"](
            status="success", args={"q": "SECRET"}, result="SECRET"
        )
        raw = self.state_path.read_text(encoding="utf-8")
        self.assertNotIn("SECRET", raw)
        state = json.loads(raw)
        self.assertEqual(state["provider_errors"], 1)
        self.assertEqual(state["provider_error_reasons"]["rate_limit"], 1)
        self.assertEqual(state["tool_calls_completed"], 1)


if __name__ == "__main__":
    unittest.main()
