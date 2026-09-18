"""Fail-closed contract for the AGENT-R1-GAP-05 interactive Hermes dashboard.

The dashboard is the pinned native Hermes UI.  This module only binds that UI
to the already-protected FreeLLMAPI service and validates the immutable managed
policy shipped by this repository; it is intentionally not a second agent
runtime, auth service, task queue, or project authority plane.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

from runtime_versions import (
    HERMES_DASHBOARD_HOME,
    HERMES_DASHBOARD_PORT,
    HERMES_MANAGED_DIR,
)

SAFE_INTERACTIVE_TOOLSETS = ("web", "memory", "session_search")
MANAGED_POLICY_PATH = Path(__file__).parent / "runtime" / "hermes-managed-config.json"

# A dashboard worker receives only the FreeLLMAPI client credential, Modal proxy
# credential and dashboard OAuth client id.  Refuse a deployment environment in
# which common upstream-provider secrets have accidentally leaked into Hermes.
DIRECT_PROVIDER_SECRET_NAMES = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "DEEPSEEK_API_KEY",
        "MISTRAL_API_KEY",
        "XAI_API_KEY",
        "GROQ_API_KEY",
        "TOGETHER_API_KEY",
        "FIREWORKS_API_KEY",
        "CEREBRAS_API_KEY",
        "COHERE_API_KEY",
        "HF_TOKEN",
        "NVIDIA_API_KEY",
        "KIMI_API_KEY",
        "MINIMAX_API_KEY",
        "MINIMAX_CN_API_KEY",
        "GLM_API_KEY",
    }
)


class DashboardConfigError(ValueError):
    pass


def _absolute_http_url(value: str, *, label: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise DashboardConfigError(f"{label} must be an absolute http(s) URL")
    if any(ch in value for ch in ("\n", "\r", "\t")):
        raise DashboardConfigError(f"{label} contains control characters")
    return value


def load_managed_policy(path: Path = MANAGED_POLICY_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DashboardConfigError("managed dashboard policy is unreadable") from exc
    if not isinstance(value, dict):
        raise DashboardConfigError("managed dashboard policy must be a JSON object")
    return value


def validate_managed_policy(policy: dict) -> dict:
    """Validate the repository-owned effective interactive policy exactly."""
    if set(policy) != {"database", "model", "providers", "platform_toolsets", "approvals"}:
        raise DashboardConfigError("managed dashboard policy contains unexpected root keys")

    if policy.get("database") != {"journal_mode": "delete"}:
        raise DashboardConfigError("dashboard state must use the single-container-safe delete journal")

    if policy.get("model") != {"default": "auto", "provider": "freellmapi"}:
        raise DashboardConfigError("interactive model route must be pinned to FreeLLMAPI auto")

    providers = policy.get("providers")
    if not isinstance(providers, dict) or set(providers) != {"freellmapi"}:
        raise DashboardConfigError("FreeLLMAPI must be the only configured interactive provider")
    gateway = providers["freellmapi"]
    expected_gateway = {
        "base_url": "${FREELLMAPI_BASE_URL}",
        "key_env": "FREELLMAPI_API_KEY",
        "api_mode": "chat_completions",
        "default_model": "auto",
        "discover_models": False,
        "models": ["auto"],
        "extra_headers": {
            "Modal-Key": "${MODAL_PROXY_KEY}",
            "Modal-Secret": "${MODAL_PROXY_SECRET}",
        },
    }
    if gateway != expected_gateway:
        raise DashboardConfigError("FreeLLMAPI managed provider contract drifted")

    if policy.get("platform_toolsets") != {"cli": list(SAFE_INTERACTIVE_TOOLSETS)}:
        raise DashboardConfigError("interactive Hermes tool capability is not the bounded safe set")
    if policy.get("approvals") != {"mode": "manual"}:
        raise DashboardConfigError("interactive approval UX must remain manual")

    serialized = json.dumps(policy, sort_keys=True)
    for secret_name in DIRECT_PROVIDER_SECRET_NAMES:
        if secret_name in serialized:
            raise DashboardConfigError("managed policy may not reference upstream provider secrets")
    return policy


def build_dashboard_environment(gateway_root: str, source_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return the native-dashboard environment after strict authority checks."""
    source = dict(os.environ if source_env is None else source_env)
    leaked = sorted(name for name in DIRECT_PROVIDER_SECRET_NAMES if source.get(name))
    if leaked:
        raise DashboardConfigError(
            "upstream provider credential(s) must not enter interactive Hermes: " + ", ".join(leaked)
        )

    for required in ("FREELLMAPI_API_KEY", "MODAL_PROXY_KEY", "MODAL_PROXY_SECRET"):
        if not source.get(required):
            raise DashboardConfigError(f"missing protected gateway credential: {required}")
    if not source["FREELLMAPI_API_KEY"].startswith("freellmapi-"):
        raise DashboardConfigError("FREELLMAPI_API_KEY must use the freellmapi- prefix")

    oauth_client = source.get("HERMES_DASHBOARD_OAUTH_CLIENT_ID", "").strip()
    if not oauth_client.startswith("agent:") or len(oauth_client) <= len("agent:"):
        raise DashboardConfigError(
            "HERMES_DASHBOARD_OAUTH_CLIENT_ID must be a provisioned agent:{instance_id} value"
        )

    validate_managed_policy(load_managed_policy())
    root = _absolute_http_url(gateway_root, label="FreeLLMAPI gateway root")
    source["FREELLMAPI_BASE_URL"] = f"{root}/v1"
    source["HERMES_HOME"] = HERMES_DASHBOARD_HOME
    source["HERMES_MANAGED_DIR"] = HERMES_MANAGED_DIR
    return source


def dashboard_command() -> list[str]:
    """Use the pinned upstream dashboard unchanged; no local UI fork exists."""
    return [
        "hermes",
        "dashboard",
        "--host",
        "0.0.0.0",
        "--port",
        str(HERMES_DASHBOARD_PORT),
        "--no-open",
    ]
