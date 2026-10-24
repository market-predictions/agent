"""Deterministic safeguards for the pinned FreeLLMAPI upgrade candidate.

Provider availability and the real 404/fallback behavior are verified by
the separate upstream-runtime CI job, not assumed from a local JSON test.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FreeModelRoutingPolicyTests(unittest.TestCase):
    def test_only_existing_keyless_free_providers_are_configured(self):
        config = json.loads((ROOT / "runtime/freellmapi.default.json").read_text())
        self.assertEqual(config["keys"], [
            {"platform": "kilo", "label": "keyless"},
            {"platform": "ovh", "label": "keyless"},
        ])
        self.assertEqual(config["routing"], {"strategy": "balanced"})
        self.assertNotIn("fallback", config)
        self.assertNotIn("licenseKey", config)

    def test_known_broken_kilo_route_is_disabled_without_fallback(self):
        config = json.loads((ROOT / "runtime/freellmapi.default.json").read_text())
        self.assertEqual(config["models"], [{
            "platform": "kilo",
            "modelId": "nvidia/nemotron-3-super-120b-a12b:free",
            "enabled": False,
            "fallbackEnabled": False,
        }])

    def test_existing_bootstrap_and_gateway_boundaries_are_not_bypassed(self):
        shim = (ROOT / "runtime/freellmapi-bootstrap.mjs").read_text()
        modal = (ROOT / "modal_app.py").read_text()
        self.assertIn("initDb, setSetting", shim)
        self.assertIn("FREELLMAPI_API_KEY", shim)
        self.assertIn("setSetting('unified_api_key', key)", shim)
        self.assertIn('FREEAPI_CONFIG_PATH', modal)
        self.assertIn('requires_proxy_auth=True', modal)
        self.assertIn('secrets=[freellmapi_client_secret]', modal)
        self.assertNotIn('secrets=[freellmapi_service_secret', modal[modal.index("def run_agent"):])

if __name__ == "__main__":
    unittest.main()
