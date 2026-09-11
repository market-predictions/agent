import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH_PATH = ROOT / "runtime" / "patch_hermes_dashboard.py"


def _load_patch_module():
    spec = importlib.util.spec_from_file_location("patch_hermes_dashboard", PATCH_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load dashboard patch module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DashboardWebSocketCompatibilityTests(unittest.TestCase):
    def test_dashboard_image_applies_patch_only_to_interactive_runtime(self):
        source = (ROOT / "modal_app.py").read_text(encoding="utf-8")
        dashboard_image_start = source.index("hermes_dashboard_image =")
        dashboard_image_end = source.index("def _bootstrap_freellmapi_unified_key", dashboard_image_start)
        dashboard_image = source[dashboard_image_start:dashboard_image_end]
        bounded_image = source[source.index("hermes_image ="):dashboard_image_start]

        self.assertIn('"runtime/patch_hermes_dashboard.py"', dashboard_image)
        self.assertIn('copy=True', dashboard_image)
        self.assertIn('python /tmp/patch_hermes_dashboard.py', dashboard_image)
        self.assertNotIn('patch_hermes_dashboard.py', bounded_image)
        self.assertIn('@modal.concurrent(max_inputs=20)', source)
        self.assertIn('@modal.concurrent(max_inputs=1)', source)

    def test_patch_disables_deflate_and_fails_closed_on_wrong_target(self):
        patch_module = _load_patch_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hermes_cli = root / "hermes_cli"
            hermes_cli.mkdir()
            server = hermes_cli / "web_server.py"
            server.write_text(
                "before\n" + patch_module.TARGET + "after\n",
                encoding="utf-8",
            )

            patch_module.patch(root)
            patched = server.read_text(encoding="utf-8")
            self.assertIn("ws_per_message_deflate=False", patched)
            self.assertNotIn(patch_module.TARGET, patched)

            # Idempotent on the exact already-patched source.
            patch_module.patch(root)

            server.write_text("no matching uvicorn config here\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                patch_module.patch(root)


if __name__ == "__main__":
    unittest.main()
