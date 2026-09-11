import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DashboardConcurrencyContractTests(unittest.TestCase):
    def test_dashboard_allows_native_http_and_websocket_concurrency(self):
        source = (ROOT / "modal_app.py").read_text(encoding="utf-8")
        dashboard_def = source.index("def dashboard()")
        dashboard_decorator = source.rfind("@app.function", 0, dashboard_def)
        dashboard_section = source[dashboard_decorator:dashboard_def]

        # Native Hermes dashboard opens several long-lived sockets (/api/ws,
        # /api/events, /api/pty) while continuing to poll HTTP APIs. With one
        # Modal container these inputs must share that container instead of
        # queueing behind the first WebSocket.
        self.assertIn("@modal.concurrent(max_inputs=20)", dashboard_section)
        self.assertIn("max_containers=1", dashboard_section)

    def test_bounded_worker_remains_single_input(self):
        source = (ROOT / "modal_app.py").read_text(encoding="utf-8")
        worker_def = source.index("def run_agent")
        worker_decorator = source.rfind("@app.function", 0, worker_def)
        worker_section = source[worker_decorator:worker_def]
        self.assertIn("@modal.concurrent(max_inputs=1)", worker_section)


if __name__ == "__main__":
    unittest.main()
