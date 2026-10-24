"""Pinned runtime identities for the operational Agent carrier.

This module is deliberately boring: one place owns every correctness-relevant
runtime pin used by Modal, tests, and operator documentation.
"""

MODAL_VERSION = "1.5.5"

HERMES_VERSION = "0.21.1"
HERMES_TAG = "v2026.9.7"
HERMES_COMMIT = "2237be355906fbe6065ce1815711eee52b2d646e"
HERMES_REPOSITORY = "https://github.com/NousResearch/hermes-agent.git"
HERMES_SOURCE_DIR = "/opt/hermes-agent"

FREELLMAPI_VERSION = "0.9.8"
FREELLMAPI_IMAGE = (
    "ghcr.io/tashfeenahmed/freellmapi@"
    "sha256:f753afb35f58587a62863c767abf158fa46b90f0de9eab0f9162c48f953ea246"
)
FREELLMAPI_PORT = 3001

# Hermes 0.21.1 requires Node ^22.22.0 (or a newer supported major) to build
# its native dashboard. Pin the first supported v22 release and verify the
# official Linux x64 archive before it enters the Modal image.
NODE_VERSION = "22.22.0"
NODE_LINUX_X64_SHA256 = "9aa8e9d2298ab68c600bd6fb86a6c13bce11a4eca1ba9b39d79fa021755d7c37"
NODE_LINUX_X64_URL = (
    f"https://nodejs.org/download/release/v{NODE_VERSION}/"
    f"node-v{NODE_VERSION}-linux-x64.tar.xz"
)

# Modal object names are part of the operator contract. Keep them stable so a
# deployment updates the existing service instead of silently creating twins.
MODAL_APP_NAME = "agent-carrier"
MODAL_FREELLMAPI_SECRET = "agent-freellmapi"
MODAL_HERMES_SECRET = "agent-hermes"
MODAL_HERMES_DASHBOARD_SECRET = "agent-hermes-dashboard"
MODAL_HERMES_DASHBOARD_VOLUME = "agent-hermes-dashboard-state"

HERMES_DASHBOARD_PORT = 9119
HERMES_DASHBOARD_HOME = "/root/.hermes"
HERMES_MANAGED_DIR = "/etc/hermes"
