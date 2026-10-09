"""Hosted authority boundary for AGENT-R1-GAP-05.

This is a Hermes extension plugin, not a dashboard/runtime fork. It keeps the
native authenticated dashboard and native chat/session storage while enforcing
three host-owned invariants at the narrowest native seams:

* provider execution can reach only the protected FreeLLMAPI route;
* tool execution can use only the repository-approved safe toolsets; and
* the hosted dashboard cannot mutate capability/configuration state or spawn
  unregistered legacy PTYs.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from urllib.parse import parse_qs

SAFE_TOOLSETS = ("web", "memory", "session_search")
EXPECTED_PROVIDER = "freellmapi"
EXPECTED_MODEL = "auto"
MAX_INTERACTIVE_PTY_SESSIONS = 1
_READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_ALLOWED_MUTATION_PREFIXES = (
    "/auth",
    "/api/auth",
    "/api/sessions",
)
_ALLOWED_MUTATION_PATHS = frozenset({"/api/chat/image-upload"})


def _normalise_url(value: object) -> str:
    return str(value or "").strip().rstrip("/")


def _path_has_prefix(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def mutation_allowed(path: str) -> bool:
    return path in _ALLOWED_MUTATION_PATHS or any(
        _path_has_prefix(path, prefix) for prefix in _ALLOWED_MUTATION_PREFIXES
    )


@lru_cache(maxsize=1)
def allowed_tool_names() -> frozenset[str]:
    """Resolve the safe capability from the exact pinned Hermes toolset catalog."""
    from toolsets import resolve_toolset

    names: set[str] = set()
    for toolset in SAFE_TOOLSETS:
        names.update(resolve_toolset(toolset, include_registry=False))
    if not names:
        raise RuntimeError("hosted Hermes safe toolset resolved empty")
    return frozenset(names)


def enforce_tool_policy(tool_name: str, **_kwargs):
    """Native pre_tool_call directive; Hermes fails closed on timeout as well."""
    if str(tool_name or "") not in allowed_tool_names():
        return {
            "action": "block",
            "message": f"Hosted dashboard policy blocks tool: {tool_name or '<empty>'}",
        }
    return None


def llm_route_allowed(*, provider: object, model: object, base_url: object) -> bool:
    expected_base = _normalise_url(os.environ.get("FREELLMAPI_BASE_URL"))
    return bool(expected_base) and (
        str(provider or "").strip().lower() == EXPECTED_PROVIDER
        and str(model or "").strip() == EXPECTED_MODEL
        and _normalise_url(base_url) == expected_base
    )


def enforce_llm_execution(
    request: dict,
    next_call,
    *,
    provider: object = "",
    model: object = "",
    base_url: object = "",
    **_kwargs,
):
    """Short-circuit before provider I/O when a session tries to leave FreeLLMAPI.

    Hermes execution middleware explicitly supports intentional short-circuiting.
    Returning ``None`` makes the turn fail/retry through the normal agent path,
    but never invokes the disallowed downstream provider. Managed policy also
    pins both fallback lists empty, so retries cannot escape through fallback.
    """
    if not llm_route_allowed(provider=provider, model=model, base_url=base_url):
        return None
    return next_call(request)


class HostedDashboardPolicyMiddleware:
    """Pure ASGI admission fence around the exact native Hermes dashboard app."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        scope_type = scope.get("type")
        path = str(scope.get("path") or "")

        if scope_type == "websocket":
            if path == "/api/console":
                await send({
                    "type": "websocket.close",
                    "code": 4403,
                    "reason": "hosted dashboard console disabled",
                })
                return
            if path == "/api/pty":
                query = parse_qs(
                    bytes(scope.get("query_string") or b"").decode("ascii", "ignore"),
                    keep_blank_values=True,
                )
                if not any(str(value).strip() for value in query.get("attach", ())):
                    # Exact pinned Hermes otherwise falls back to an unregistered
                    # 1:1 PTY that bypasses PTY_REGISTRY.max_sessions.
                    await send({
                        "type": "websocket.close",
                        "code": 4403,
                        "reason": "hosted dashboard requires managed PTY attach",
                    })
                    return
            await self.app(scope, receive, send)
            return

        if scope_type == "http":
            method = str(scope.get("method") or "GET").upper()
            if method not in _READ_METHODS and not mutation_allowed(path):
                body = b'{"detail":"hosted dashboard mutation blocked by policy"}'
                await send({
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                })
                await send({"type": "http.response.body", "body": body})
                return

        await self.app(scope, receive, send)


def _is_native_dashboard_process() -> bool:
    return any(str(arg).strip().lower() == "dashboard" for arg in sys.argv[1:])


def install_dashboard_host_policy() -> None:
    """Install the dashboard-only ASGI fence and one-PTY native registry cap."""
    from hermes_cli import web_server, web_server_chat

    if not getattr(web_server.app.state, "agent_host_policy_installed", False):
        web_server.app.add_middleware(HostedDashboardPolicyMiddleware)
        web_server.app.state.agent_host_policy_installed = True

    registry = web_server_chat.PTY_REGISTRY
    if not hasattr(registry, "_max"):
        raise RuntimeError("pinned Hermes PTY registry contract changed")
    registry._max = MAX_INTERACTIVE_PTY_SESSIONS


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", enforce_tool_policy)
    ctx.register_middleware("llm_execution", enforce_llm_execution)
    if _is_native_dashboard_process():
        install_dashboard_host_policy()
