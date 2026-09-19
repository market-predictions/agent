"""Hosted policy for the native Hermes dashboard used by AGENT-R1-GAP-05.

Hermes remains the dashboard/runtime implementation. This module only supplies
the host-owned policy boundary required by the Mission: protected FreeLLMAPI
inference, managed safe tools, no direct provider credentials, no local shell
shortcut, and no browser mutation surface that can widen those capabilities.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from runtime_versions import (
    HERMES_DASHBOARD_HOME,
    HERMES_DASHBOARD_PORT,
    HERMES_MANAGED_DIR,
)

SAFE_INTERACTIVE_TOOLSETS = ("web", "memory", "session_search")
_RUNTIME_DIR = Path(__file__).parent / "runtime"
MANAGED_POLICY_PATH = _RUNTIME_DIR / "hermes-managed-config.json"

# These are host-management surfaces, not chat/session state. GET/HEAD/OPTIONS
# remain available where Hermes exposes them; mutating routes are removed from
# the hosted app before it starts. This keeps the native UI while preventing a
# browser session from widening provider/tool/scheduler authority.
BLOCKED_MUTATION_PREFIXES = (
    "/api/config",
    "/api/env",
    "/api/providers",
    "/api/mcp",
    "/api/dashboard/plugins",
    "/api/cron",
)
BLOCKED_WEBSOCKET_PATHS = frozenset({"/api/console"})
_READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


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
        raise DashboardConfigError("FreeLLMAPI must be the only managed interactive provider")
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
    return policy


def provider_secret_names() -> frozenset[str]:
    """Credential env names from the exact installed Hermes provider catalog.

    The Hermes commit is pinned by ``runtime_versions.py``. Deriving this set
    from upstream's own catalog avoids a second, inevitably stale provider-key
    inventory in this repository.
    """
    try:
        from hermes_cli.provider_catalog import provider_catalog
    except Exception as exc:
        raise DashboardConfigError("pinned Hermes provider catalog is unavailable") from exc

    names = frozenset(
        str(name).strip()
        for descriptor in provider_catalog()
        for name in descriptor.api_key_env_vars
        if str(name).strip()
    )
    if not names:
        raise DashboardConfigError("pinned Hermes provider catalog exposed no credential names")
    return names


def materialize_managed_env_policy(
    names: frozenset[str] | set[str] | None = None,
    path: Path | None = None,
) -> Path:
    """Pin every upstream-provider credential name to an empty managed value."""
    resolved = frozenset(names if names is not None else provider_secret_names())
    if not resolved:
        raise DashboardConfigError("managed provider credential set is empty")
    managed_path = path or (Path(HERMES_MANAGED_DIR) / ".env")
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_path.write_text("".join(f"{name}=\n" for name in sorted(resolved)), encoding="utf-8")
    try:
        managed_path.chmod(0o444)
    except OSError:
        pass
    return managed_path


def build_dashboard_environment(
    gateway_root: str,
    source_env: dict[str, str] | None = None,
    *,
    direct_provider_secret_names: frozenset[str] | set[str] | None = None,
) -> dict[str, str]:
    """Return the native-dashboard environment after strict authority checks."""
    source = dict(os.environ if source_env is None else source_env)
    direct_secrets = frozenset(
        direct_provider_secret_names
        if direct_provider_secret_names is not None
        else provider_secret_names()
    )
    leaked = sorted(name for name in direct_secrets if source.get(name))
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
    # The pinned Hermes bang-shell implementation is disabled for gateway or
    # platform sessions. The dashboard PTY inherits this process environment,
    # closing the direct `!command` local-shell shortcut without a Hermes fork.
    source["HERMES_GATEWAY_SESSION"] = "1"
    return source


def _path_has_prefix(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def is_blocked_mutation(path: str, methods: set[str] | frozenset[str]) -> bool:
    normalized_methods = {str(method).upper() for method in methods}
    if not normalized_methods or normalized_methods <= _READ_METHODS:
        return False
    return any(_path_has_prefix(path, prefix) for prefix in BLOCKED_MUTATION_PREFIXES)


def install_host_route_policy(app) -> set[tuple[str, str]]:
    """Remove hosted-only authority bypass routes from the native FastAPI app.

    Returns removed ``(method, path)`` signatures for exact-upstream CI proof.
    Chat/session/memory routes remain native and untouched.
    """
    kept = []
    removed: set[tuple[str, str]] = set()
    for route in app.router.routes:
        path = str(getattr(route, "path", "") or "")
        methods = {str(method).upper() for method in (getattr(route, "methods", None) or set())}
        if path in BLOCKED_WEBSOCKET_PATHS:
            removed.add(("WS", path))
            continue
        if is_blocked_mutation(path, methods):
            removed.update((method, path) for method in methods if method not in _READ_METHODS)
            continue
        kept.append(route)
    app.router.routes[:] = kept
    return removed


def dashboard_command() -> list[str]:
    """Launch the host wrapper; it serves the exact pinned native Hermes app."""
    return [sys.executable, "-m", "interactive_dashboard"]


def serve_native_dashboard() -> None:
    """Apply the bounded host policy, then call Hermes' own dashboard server."""
    from hermes_cli import web_server

    removed = install_host_route_policy(web_server.app)
    if ("WS", "/api/console") not in removed:
        raise DashboardConfigError("pinned Hermes console route was not fenced")
    web_server.start_server(
        host="0.0.0.0",
        port=HERMES_DASHBOARD_PORT,
        open_browser=False,
    )


if __name__ == "__main__":
    serve_native_dashboard()
