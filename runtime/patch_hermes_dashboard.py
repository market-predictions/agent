"""Patch the pinned Hermes dashboard for Modal and a usable console font size.

Both changes are dashboard-only: preserve the upstream headless Hermes worker.
Exact source anchors fail closed if the pinned upstream checkout changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Modal ingress WebSocket compatibility: no permessage-deflate negotiation.
TARGET = """        ws_ping_timeout=ping_timeout,
        ws_max_size=_DESKTOP_ATTACHMENT_WS_MAX_BYTES,
"""
REPLACEMENT = """        ws_ping_timeout=ping_timeout,
        # Modal ingress compatibility: avoid permessage-deflate negotiation.
        ws_per_message_deflate=False,
        ws_max_size=_DESKTOP_ATTACHMENT_WS_MAX_BYTES,
"""

# The xterm renderer has its own pixel sizes, independent of dashboard themes.
# Use localStorage for one browser-specific setting; existing FitAddon and PTY
# resize logic own reflow, with no new server setting or background process.
FONT_PATCHES = (
    (
        "remove unused width initialization",
        """    const tierW0 = terminalTierWidthPx(host);
    const term = new Terminal({""",
        """    const term = new Terminal({""",
    ),
    (
        "terminal font sizes",
        """function terminalFontSizeForWidth(layoutWidthPx: number): number {
  if (layoutWidthPx < 300) return 7;
  if (layoutWidthPx < 360) return 8;
  if (layoutWidthPx < 420) return 9;
  if (layoutWidthPx < 520) return 10;
  if (layoutWidthPx < 720) return 11;
  if (layoutWidthPx < 1024) return 12;
  return 14;
}""",
        """const CONSOLE_FONT_SIZES = [14, 16, 18, 20, 22] as const;
const CONSOLE_FONT_STORAGE_KEY = "hermes.console.fontSize";

function readConsoleFontSize(): number {
  if (typeof window === "undefined") return 16;
  try {
    const stored = window.localStorage.getItem(CONSOLE_FONT_STORAGE_KEY);
    const size = stored === null ? NaN : Number(stored);
    return CONSOLE_FONT_SIZES.includes(size as (typeof CONSOLE_FONT_SIZES)[number])
      ? size : 16;
  } catch {
    return 16;
  }
}""",
    ),
    (
        "console size state",
        """  const syncMetricsRef = useRef<(() => void) | null>(null);""",
        """  const syncMetricsRef = useRef<(() => void) | null>(null);
  const [consoleFontSize, setConsoleFontSize] = useState(readConsoleFontSize);
  const consoleFontSizeRef = useRef(consoleFontSize);
  const changeConsoleFontSize = (size: number) => {
    if (!CONSOLE_FONT_SIZES.includes(size as (typeof CONSOLE_FONT_SIZES)[number])) return;
    consoleFontSizeRef.current = size;
    setConsoleFontSize(size);
    try {
      window.localStorage.setItem(CONSOLE_FONT_STORAGE_KEY, String(size));
    } catch {
      // Private mode and blocked storage: the current session still works.
    }
    syncMetricsRef.current?.();
  };""",
    ),
    (
        "initial xterm font size",
        """fontSize: terminalFontSizeForWidth(tierW0),""",
        """fontSize: consoleFontSizeRef.current,""",
    ),
    (
        "xterm refit size",
        """const nextSize = terminalFontSizeForWidth(w);""",
        """const nextSize = consoleFontSizeRef.current;""",
    ),
    (
        "font control",
        """      {mobileModelToolsPortal}
""",
        """      {mobileModelToolsPortal}
      <div className="flex shrink-0 items-center justify-end gap-2 px-1">
        <label htmlFor="hermes-console-font-size" className="text-xs text-text-secondary">
          Console font
        </label>
        <select
          id="hermes-console-font-size"
          aria-label="Console font size"
          value={consoleFontSize}
          onChange={(event) => changeConsoleFontSize(Number(event.target.value))}
          className="rounded border border-current/30 bg-background-base px-2 py-1 text-xs text-midground"
        >
          {CONSOLE_FONT_SIZES.map((size) => (
            <option key={size} value={size}>{size} px</option>
          ))}
        </select>
      </div>
""",
    ),
)


def _replace_exact(content: str, target: str, replacement: str, label: str) -> str:
    if replacement in content:
        return content
    matches = content.count(target)
    if matches != 1:
        raise RuntimeError(f"Expected exactly one Hermes {label} target, found {matches}")
    return content.replace(target, replacement, 1)


def patch(source_root: Path) -> None:
    server = source_root / "hermes_cli" / "web_server.py"
    chat = source_root / "web" / "src" / "pages" / "ChatPage.tsx"
    server_source = server.read_text(encoding="utf-8")
    chat_source = chat.read_text(encoding="utf-8")

    # Validate ALL anchors before writing either file.
    patched_server = _replace_exact(server_source, TARGET, REPLACEMENT, "WebSocket config")
    patched_chat = chat_source
    for label, target, replacement in FONT_PATCHES:
        patched_chat = _replace_exact(patched_chat, target, replacement, label)

    if server_source != patched_server:
        server.write_text(patched_server, encoding="utf-8")
    if chat_source != patched_chat:
        chat.write_text(patched_chat, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_hermes_dashboard.py HERMES_SOURCE_DIR")
    patch(Path(sys.argv[1]))
    print("Hermes dashboard compatibility and console font controls applied")
