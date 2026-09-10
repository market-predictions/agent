"""Native Hermes policy plugin for hard Phase-1 execution budgets.

The plugin is installed into each disposable ``HERMES_HOME`` by ``agent_carrier``.
It uses Hermes' documented ``llm_execution`` middleware and ``pre_tool_call``
hook so limits are enforced at the actual provider/tool execution boundaries,
including retries. Only counters and non-sensitive routing metadata are written
to the state file; prompts, tool arguments, results, errors, and credentials are
never persisted here.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

STATE_PATH_ENV = "AGENT_BUDGET_STATE_PATH"
MAX_MODEL_CALLS_ENV = "AGENT_MAX_MODEL_CALLS"
MAX_TOOL_CALLS_ENV = "AGENT_MAX_TOOL_CALLS"
MAX_RETRIES_ENV = "AGENT_MAX_RETRIES"

_ALLOWED_TOOLS = frozenset({"web_search", "web_extract"})
_LOCK = threading.Lock()
_SEEN_REQUEST_IDS: set[str] = set()
_STATE: dict[str, Any] = {}


def _positive_limit(name: str) -> int:
    raw = os.environ.get(name, "")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 1
    return value if value > 0 else 1


def _fresh_state() -> dict[str, Any]:
    return {
        "plugin_ready": True,
        "model_calls": 0,
        "tool_calls": 0,
        "tool_calls_completed": 0,
        "tool_successes": 0,
        "tool_failures": 0,
        "tool_blocks": 0,
        "retries": 0,
        "provider_errors": 0,
        "provider_error_reasons": {},
        "provider": None,
        "response_model": None,
        "budget_exceeded": None,
        "policy_violation": None,
    }


def _public_state() -> dict[str, Any]:
    # Keep the persisted file intentionally metadata-only. In particular, no
    # request ids, prompts, arguments, tool results, or raw provider errors.
    return dict(_STATE)


def _write_state() -> None:
    path_text = os.environ.get(STATE_PATH_ENV, "").strip()
    if not path_text:
        return
    try:
        path = Path(path_text)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(
            json.dumps(_public_state(), sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(tmp, path)
    except Exception:
        # Enforcement is in-memory and must not become fail-open because optional
        # telemetry persistence is unavailable. The parent process independently
        # fails a successful run if no valid state file is produced.
        pass


def _budget_response(code: str) -> SimpleNamespace:
    """Return the smallest Chat-Completions-shaped stop response Hermes accepts."""
    message = SimpleNamespace(
        role="assistant",
        content=json.dumps({"agent_budget_exceeded": code}, separators=(",", ":")),
        tool_calls=None,
        reasoning=None,
        reasoning_content=None,
        reasoning_details=None,
        refusal=None,
    )
    choice = SimpleNamespace(message=message, finish_reason="stop")
    return SimpleNamespace(choices=[choice], usage=None, model="agent-budget")


def _llm_execution(**kwargs):
    """Hard-cap actual provider executions and total retry attempts."""
    try:
        next_call = kwargs.get("next_call")
        if not callable(next_call):
            raise TypeError("llm_execution next_call is unavailable")
        request = kwargs["request"]
        request_id = str(
            kwargs.get("api_request_id")
            or f"api:{kwargs.get('api_call_count', 'unknown')}"
        )
        with _LOCK:
            is_retry = request_id in _SEEN_REQUEST_IDS
            if _STATE["model_calls"] >= _positive_limit(MAX_MODEL_CALLS_ENV):
                _STATE["budget_exceeded"] = "model_calls"
                _write_state()
                return _budget_response("model_calls")
            if is_retry and _STATE["retries"] >= _positive_limit(MAX_RETRIES_ENV):
                _STATE["budget_exceeded"] = "retries"
                _write_state()
                return _budget_response("retries")

            _STATE["model_calls"] += 1
            if is_retry:
                _STATE["retries"] += 1
            else:
                _SEEN_REQUEST_IDS.add(request_id)
            provider = kwargs.get("provider")
            if isinstance(provider, str) and provider:
                _STATE["provider"] = provider
            _write_state()
    except Exception as exc:
        # Middleware failures are fail-open in Hermes. Therefore failures in this
        # policy callback must themselves short-circuit rather than escape.
        with _LOCK:
            _STATE["policy_violation"] = f"budget_guard_failure:{type(exc).__name__}"
            _write_state()
        return _budget_response("budget_guard_failure")

    # Deliberately outside the guard's catch: real provider exceptions must reach
    # Hermes' recovery loop and api_request_error observers, where any retry will
    # re-enter this middleware and consume the hard run-global retry budget.
    return next_call(request)


def _pre_tool_call(tool_name: str = "", **kwargs):
    """Hard-cap total tool executions and keep the Phase-1 allow-list fixed."""
    del kwargs
    try:
        with _LOCK:
            if tool_name not in _ALLOWED_TOOLS:
                _STATE["policy_violation"] = f"unauthorized_tool:{tool_name or 'unknown'}"
                _STATE["tool_blocks"] += 1
                _write_state()
                return {
                    "action": "block",
                    "message": "AGENT_POLICY_BLOCKED: tool is outside the Phase-1 allow-list",
                }
            if _STATE["tool_calls"] >= _positive_limit(MAX_TOOL_CALLS_ENV):
                _STATE["budget_exceeded"] = "tool_calls"
                _STATE["tool_blocks"] += 1
                _write_state()
                return {
                    "action": "block",
                    "message": "AGENT_BUDGET_EXCEEDED: tool call limit reached",
                }
            _STATE["tool_calls"] += 1
            _write_state()
        return None
    except Exception as exc:
        with _LOCK:
            _STATE["policy_violation"] = f"tool_guard_failure:{type(exc).__name__}"
            _STATE["tool_blocks"] += 1
            _write_state()
        return {
            "action": "block",
            "message": "AGENT_POLICY_BLOCKED: tool budget guard failed closed",
        }


def _post_tool_call(status: str | None = None, **kwargs) -> None:
    del kwargs
    try:
        with _LOCK:
            normalized = str(status or "").strip().lower()
            if normalized == "blocked":
                # A blocked call was never included in tool_calls. The blocking
                # directive itself was already counted in pre_tool_call.
                pass
            else:
                _STATE["tool_calls_completed"] += 1
                if normalized in {"error", "failed", "failure"}:
                    _STATE["tool_failures"] += 1
                else:
                    _STATE["tool_successes"] += 1
            _write_state()
    except Exception:
        # Observer telemetry cannot weaken the hard pre-execution gates.
        pass


def _api_request_error(reason: str | None = None, **kwargs) -> None:
    del kwargs
    try:
        with _LOCK:
            _STATE["provider_errors"] += 1
            key = str(reason or "unknown")[:80]
            reasons = _STATE["provider_error_reasons"]
            reasons[key] = int(reasons.get(key, 0)) + 1
            _write_state()
    except Exception:
        pass


def _post_api_request(response_model: str | None = None, provider: str | None = None, **kwargs) -> None:
    del kwargs
    try:
        with _LOCK:
            if isinstance(response_model, str) and response_model:
                _STATE["response_model"] = response_model
            if isinstance(provider, str) and provider:
                _STATE["provider"] = provider
            _write_state()
    except Exception:
        pass


def register(ctx) -> None:
    """Register only the native Hermes surfaces needed by the bounded carrier."""
    with _LOCK:
        _SEEN_REQUEST_IDS.clear()
        _STATE.clear()
        _STATE.update(_fresh_state())
        _write_state()
    ctx.register_middleware("llm_execution", _llm_execution)
    ctx.register_hook("pre_tool_call", _pre_tool_call)
    ctx.register_hook("post_tool_call", _post_tool_call)
    ctx.register_hook("api_request_error", _api_request_error)
    ctx.register_hook("post_api_request", _post_api_request)
