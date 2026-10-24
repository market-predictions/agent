"""Pinned runtime identities for the first operational Agent carrier.

This module is deliberately boring: one place owns every correctness-relevant
runtime pin used by Modal, tests, and operator documentation.
"""

MODAL_VERSION = "1.5.5"

HERMES_VERSION = "0.21.1"
HERMES_TAG = "v2026.9.7"
HERMES_COMMIT = "2237be355906fbe6065ce1815711eee52b2d646e"
HERMES_REPOSITORY = "https://github.com/NousResearch/hermes-agent.git"
HERMES_SOURCE_DIR = "/opt/hermes-agent"

FREELLMAPI_VERSION = "0.16.9"
FREELLMAPI_IMAGE = (
    "ghcr.io/tashfeenahmed/freellmapi@"
    "sha256:b4723c688f1d272a8a9e745b649221f6c44f3050c35e20ac31456855e74cf50b"
)
FREELLMAPI_PORT = 3001

# Modal object names are part of the operator contract. Keep them stable so a
# deployment updates the existing service instead of silently creating twins.
MODAL_APP_NAME = "agent-carrier"
MODAL_FREELLMAPI_SECRET = "agent-freellmapi"
MODAL_HERMES_SECRET = "agent-hermes"
