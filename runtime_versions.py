"""Pinned runtime identities for the Agent carrier and interactive Hermes UI."""

MODAL_VERSION = "1.5.5"

HERMES_VERSION = "0.21.1"
HERMES_TAG = "v2026.9.7"
HERMES_COMMIT = "2237be355906fbe6065ce1815711eee52b2d646e"
HERMES_REPOSITORY = "https://github.com/NousResearch/hermes-agent.git"
HERMES_SOURCE_DIR = "/opt/hermes-agent"

# Hermes upstream pins Node 26 for its browser dashboard/TUI build. Reuse that
# exact upstream base instead of inventing a second Node installation path.
HERMES_DASHBOARD_NODE_IMAGE = (
    "node:26-bookworm-slim@"
    "sha256:9e6f9357d371591e32ab6f2d8a26d63bdd0d17c29eee3f4f3e7e454d9634bf73"
)
HERMES_DASHBOARD_PORT = 9119
HERMES_DASHBOARD_HOME = "/data/hermes"
HERMES_DASHBOARD_PUBLIC_URL = (
    "https://market-predictions--agent-carrier-dashboard.modal.run"
)
# OAuth client IDs are public identifiers, not credentials. Keeping this value
# in GitHub avoids an unnecessary third Modal Secret while real credentials
# remain confined to the existing protected runtime Secrets.
HERMES_DASHBOARD_OAUTH_CLIENT_ID = "agent:cmtvyr0070021gm0azzjkg522"

FREELLMAPI_VERSION = "0.9.8"
FREELLMAPI_IMAGE = (
    "ghcr.io/tashfeenahmed/freellmapi@"
    "sha256:f753afb35f58587a62863c767abf158fa46b90f0de9eab0f9162c48f953ea246"
)
FREELLMAPI_PORT = 3001

# Modal object names are part of the operator contract. Keep them stable so a
# deployment updates the existing service instead of silently creating twins.
MODAL_APP_NAME = "agent-carrier"
MODAL_FREELLMAPI_SECRET = "agent-freellmapi"
MODAL_HERMES_SECRET = "agent-hermes"
MODAL_HERMES_DASHBOARD_VOLUME = "agent-hermes-home"
