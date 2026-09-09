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
        self.assertIn(runtime_versions.HERMES_COMMIT, runtime_versions.HERMES_GIT_SPEC)
        self.assertEqual(runtime_versions.FREELLMAPI_VERSION, "0.9.8")
        self.assertRegex(
            runtime_versions.FREELLMAPI_IMAGE,
            r"^ghcr\.io/tashfeenahmed/freellmapi@sha256:[0-9a-f]{64}$",
        )

    def test_modal_topology_stays_small_and_protected(self):
        source = (ROOT / "modal_app.py").read_text(encoding="utf-8")
        self.assertIn("requires_proxy_auth=True", source)
        self.assertIn("max_containers=1", source)
        self.assertIn("min_containers=0", source)
        self.assertIn("HERMES_GIT_SPEC", source)
        self.assertIn("FREELLMAPI_IMAGE", source)
        self.assertNotIn("modal.Volume", source)
        self.assertNotIn("modal.Sandbox", source)
        self.assertNotIn("Pydantic", source)

    def test_worker_does_not_receive_provider_secret(self):
        source = (ROOT / "modal_app.py").read_text(encoding="utf-8")
        worker_start = source.index("def run_agent")
        worker_decorator = source.rfind("@app.function", 0, worker_start)
        worker_section = source[worker_decorator:]
        self.assertIn("secrets=[freellmapi_client_secret]", worker_section)
        self.assertNotIn("secrets=[freellmapi_service_secret", worker_section)


if __name__ == "__main__":
    unittest.main()
