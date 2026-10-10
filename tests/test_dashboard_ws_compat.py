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


def _fixture(root, patch_module):
    hermes_cli = root / "hermes_cli"
    hermes_cli.mkdir()
    server = hermes_cli / "web_server.py"
    server.write_text("before\n" + patch_module.TARGET + "after\n", encoding="utf-8")
    chat_dir = root / "web" / "src" / "pages"
    chat_dir.mkdir(parents=True)
    chat = chat_dir / "ChatPage.tsx"
    chat.write_text(
        "\n".join(target for _, target, _ in patch_module.FONT_PATCHES),
        encoding="utf-8",
    )
    return server, chat


class DashboardWebSocketCompatibilityTests(unittest.TestCase):
    def test_dashboard_image_applies_patch_only_to_interactive_runtime(self):
        source = (ROOT / "modal_app.py").read_text(encoding="utf-8")
        dashboard_image_start = source.index("hermes_dashboard_image =")
        dashboard_image_end = source.index(
            "def _bootstrap_freellmapi_unified_key", dashboard_image_start
        )
        dashboard_image = source[dashboard_image_start:dashboard_image_end]
        bounded_image = source[source.index("hermes_image ="):dashboard_image_start]

        self.assertIn('"runtime/patch_hermes_dashboard.py"', dashboard_image)
        self.assertIn("copy=True", dashboard_image)
        self.assertIn("python /tmp/patch_hermes_dashboard.py", dashboard_image)
        self.assertNotIn("patch_hermes_dashboard.py", bounded_image)
        self.assertIn("@modal.concurrent(max_inputs=20)", source)
        self.assertIn("@modal.concurrent(max_inputs=1)", source)

    def test_pinned_patch_adds_persistent_font_selection_and_resizing(self):
        p = _load_patch_module()
        with tempfile.TemporaryDirectory() as tmp:
            server, chat = _fixture(Path(tmp), p)
            p.patch(Path(tmp))
            server_result = server.read_text(encoding="utf-8")
            chat_result = chat.read_text(encoding="utf-8")

            self.assertIn("ws_per_message_deflate=False", server_result)
            self.assertNotIn(p.TARGET, server_result)
            self.assertIn("[14, 16, 18, 20, 22]", chat_result)
            self.assertIn("return 16;", chat_result)
            self.assertIn("window.localStorage.getItem(CONSOLE_FONT_STORAGE_KEY)", chat_result)
            self.assertIn("window.localStorage.setItem(CONSOLE_FONT_STORAGE_KEY", chat_result)
            self.assertIn("const nextSize = consoleFontSizeRef.current;", chat_result)
            self.assertIn("syncMetricsRef.current?.();", chat_result)
            self.assertIn('aria-label="Console font size"', chat_result)
            self.assertIn("fontSize: consoleFontSizeRef.current,", chat_result)
            self.assertNotIn("terminalFontSizeForWidth", chat_result)

            # Reapplying an immutable image patch changes no bytes.
            p.patch(Path(tmp))
            self.assertEqual(server_result, server.read_text(encoding="utf-8"))
            self.assertEqual(chat_result, chat.read_text(encoding="utf-8"))

    def test_patch_fails_closed_without_touching_server_on_invalid_chat(self):
        p = _load_patch_module()
        with tempfile.TemporaryDirectory() as tmp:
            server, chat = _fixture(Path(tmp), p)
            original_server = server.read_text(encoding="utf-8")
            chat.write_text("unexpected upstream UI", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                p.patch(Path(tmp))
            self.assertEqual(original_server, server.read_text(encoding="utf-8"))

    def test_patch_fails_closed_on_changed_server_anchor(self):
        p = _load_patch_module()
        with tempfile.TemporaryDirectory() as tmp:
            server, chat = _fixture(Path(tmp), p)
            original_chat = chat.read_text(encoding="utf-8")
            server.write_text("unexpected upstream server", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                p.patch(Path(tmp))
            self.assertEqual(original_chat, chat.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
