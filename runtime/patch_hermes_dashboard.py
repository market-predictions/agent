"""Apply the one compatibility patch required by the Modal-hosted Hermes dashboard.

Hermes/Uvicorn enables permessage-deflate by default. The browser-facing Modal
WebSocket hop has produced immediate RFC 6455 protocol-error closes (1002) on
Hermes' /api/ws path. Disabling server-side WebSocket compression removes that
negotiation while preserving native Hermes framing and every security boundary.

The patch is intentionally exact and fail-closed because Hermes is commit-pinned.
If upstream changes the target block, the image build must fail rather than apply
an approximate source rewrite.
"""

from __future__ import annotations

import sys
from pathlib import Path

TARGET = """        ws_ping_timeout=ping_timeout,\n        ws_max_size=_DESKTOP_ATTACHMENT_WS_MAX_BYTES,\n"""
REPLACEMENT = """        ws_ping_timeout=ping_timeout,\n        # Modal ingress compatibility: avoid permessage-deflate negotiation.\n        ws_per_message_deflate=False,\n        ws_max_size=_DESKTOP_ATTACHMENT_WS_MAX_BYTES,\n"""


def patch(source_root: Path) -> None:
    target = source_root / "hermes_cli" / "web_server.py"
    text = target.read_text(encoding="utf-8")
    if REPLACEMENT in text:
        return
    matches = text.count(TARGET)
    if matches != 1:
        raise RuntimeError(
            f"Expected exactly one Hermes uvicorn WebSocket config target, found {matches}"
        )
    target.write_text(text.replace(TARGET, REPLACEMENT, 1), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_hermes_dashboard.py HERMES_SOURCE_DIR")
    patch(Path(sys.argv[1]))
    print("Hermes dashboard WebSocket compression disabled")
